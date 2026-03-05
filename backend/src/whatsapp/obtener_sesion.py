import logging
import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.config.log_config import configurar_log

# Inicializamos el logging
configurar_log()

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = BASE_DIR / "chrome_profile"
DOWNLOAD_DIR = BASE_DIR / "downloads"


def _normalizar_texto(valor: str) -> str:
    return " ".join((valor or "").strip().lower().split())

class WhatsAppService:
    def __init__(self):
        # Por ahora solo definimos el estado del modo headless
        self.headless = False

    @staticmethod
    def quote_xpath(s: str) -> str:
        if '"' not in s:
            return f'"{s}"'
        if "'" not in s:
            return f"'{s}'"
        parts = s.split('"')
        return "concat(" + ", '\"', ".join(f'"{p}"' for p in parts) + ")"

    def obtener_imagenes(self):
        """
        Método principal que orquesta la apertura del navegador y la espera del QR.
        """
        logging.info("Iniciando proceso de obtención de imágenes (Solo QR)...")
        chrome = self.get_chrome(self.headless)
        
        try:
            # 1. Navegar a WhatsApp
            url = "https://web.whatsapp.com/"
            logging.info(f"Navegando a {url}")
            chrome.get(url)

            # 2. Esperar a que el usuario escanee el QR
            # El elemento "//div[@contenteditable='true']" solo aparece tras un login exitoso
            logging.info("Esperando escaneo de QR (Máximo 120 segundos)...")
            wait = WebDriverWait(chrome, timeout=120)
            wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
            )
            
            logging.info("¡Sesión iniciada correctamente!")

            self.abrir_grupo(chrome, "prueba rpa")

            time.sleep(5)

            self.procesar_imagenes_del_dia(chrome, "AYER")
            
            time.sleep(5)
            
        except Exception:
            logging.exception("Error durante la espera de la sesión de WhatsApp.")
            # Opcionalmente podrías llamar a mostrar_log_chrome aquí
            raise
        finally:
            logging.info("Cerrando navegador...")
            chrome.quit()

    def abrir_grupo(self, chrome: webdriver.Chrome, nombre_grupo: str):
        buscar = WebDriverWait(chrome, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
        )
        buscar.click()
        buscar.send_keys(Keys.CONTROL, "a")
        buscar.send_keys(Keys.DELETE)
        buscar.send_keys(nombre_grupo)
        WebDriverWait(chrome, 5)
        chat = WebDriverWait(chrome, 30).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[@title={self.quote_xpath(nombre_grupo)}]"))
        )
        chat.click()

    def hacer_scroll_hasta_fecha(self, chrome, fecha_objetivo: str):
        """
        Sube en el chat hasta que la etiqueta de fecha objetivo sea visible.
        """
        objetivo_normalizado = _normalizar_texto(fecha_objetivo)
        logging.info(f"Buscando la etiqueta de fecha: {fecha_objetivo}...")

        contenedor_chat = self._obtener_contenedor_scroll_chat(chrome)
        if not contenedor_chat:
            logging.error("No se pudo localizar el contenedor de scroll del chat.")
            return False

        scroll_sin_cambios = 0
        ultimo_scroll_top = None
        max_intentos = 45

        for intento in range(max_intentos):
            if self._fecha_visible_en_chat(chrome, objetivo_normalizado):
                logging.info(f"¡Etiqueta '{fecha_objetivo}' localizada!")
                return True

            scroll_top = chrome.execute_script("return arguments[0].scrollTop", contenedor_chat)
            chrome.execute_script("arguments[0].scrollTop = Math.max(0, arguments[0].scrollTop - arguments[1])", contenedor_chat, 1400)
            time.sleep(1.2)

            nuevo_scroll_top = chrome.execute_script("return arguments[0].scrollTop", contenedor_chat)
            logging.info(f"Intento scroll {intento + 1}/{max_intentos} | scrollTop: {scroll_top} -> {nuevo_scroll_top}")

            if ultimo_scroll_top is not None and nuevo_scroll_top == ultimo_scroll_top:
                scroll_sin_cambios += 1
            else:
                scroll_sin_cambios = 0

            ultimo_scroll_top = nuevo_scroll_top
            if scroll_sin_cambios >= 3 or nuevo_scroll_top == scroll_top:
                logging.info("Scroll estancado, se detiene búsqueda hacia arriba.")
                break

        return self._fecha_visible_en_chat(chrome, objetivo_normalizado)

    def procesar_imagenes_del_dia(self, chrome, fecha_objetivo: str):
        """
        Orquesta el scroll y la descarga.
        """
        encontrado = self.hacer_scroll_hasta_fecha(chrome, fecha_objetivo)

        if not encontrado:
            logging.warning(f"No se pudo encontrar la sección de {fecha_objetivo} tras varios intentos.")
            return

        logging.info("Analizando mensajes de la sección...")

        mensajes = self._obtener_mensajes_de_fecha(chrome, fecha_objetivo)
        logging.info(f"Mensajes encontrados para {fecha_objetivo}: {len(mensajes)}")
        if not mensajes:
            logging.warning("No hay mensajes multimedia asociados a la fecha objetivo en las filas cargadas.")

        for msg in mensajes:
            try:
                remitente = self._obtener_remitente(msg)
                prefijo_archivo = self._crear_prefijo_nombre(fecha_objetivo, remitente)

                botones_foto = msg.find_elements(By.XPATH, ".//*[@role='button' and @aria-label='Abrir foto']")
                if not botones_foto:
                    continue

                logging.info(f"MEDIA detectada de {remitente}.")
                self.descargar_foto_unica(chrome, botones_foto[0], prefijo_archivo)

            except Exception:
                logging.exception("Error procesando mensaje multimedia")
                continue

    def descargar_foto_unica(self, chrome, elemento_click, prefijo_archivo: str):
        """Abre multimedia y descarga (single o carrusel) según el estado del visor."""
        elemento_click.click()
        self._descargar_desde_visor(chrome, prefijo_archivo)
        self.cerrar_visor(chrome)

    def descargar_album(self, chrome, contenedor_album, prefijo_archivo: str):
        """Compatibilidad: abre el primer item del contenedor y usa la misma lógica de visor."""
        primera_foto = contenedor_album.find_element(By.XPATH, ".//*[@role='button' and @aria-label='Abrir foto']")
        primera_foto.click()
        self._descargar_desde_visor(chrome, prefijo_archivo)
        self.cerrar_visor(chrome)

    def _descargar_desde_visor(self, chrome, prefijo_archivo: str):
        """Descarga media en visor: individual o agrupada según botón Siguiente."""
        self._esperar_visor_abierto(chrome)

        # Si no hay siguiente, tratamos la media como individual.
        if not self._tiene_boton_siguiente(chrome):
            self.ejecutar_descarga_en_visor(chrome, prefijo_archivo)
            return

        # Si hay siguiente, es carrusel/agrupado: avanzar hasta X == Y.
        while True:
            estado = self._obtener_estado_carrusel(chrome)
            if estado:
                actual, total = estado
                sufijo = f"_{actual:02d}" if total > 1 else ""
                self.ejecutar_descarga_en_visor(chrome, f"{prefijo_archivo}{sufijo}")
                logging.info(f"Carrusel: imagen {actual} de {total}")

                if actual >= total:
                    logging.info("Fin de carrusel alcanzado por contador X de Y.")
                    break
            else:
                # Fallback defensivo si no aparece el contador.
                self.ejecutar_descarga_en_visor(chrome, prefijo_archivo)

            if not self._click_siguiente_en_visor(chrome, timeout=4):
                logging.info("No hay más elementos en carrusel (botón Siguiente no disponible).")
                break
            time.sleep(0.8)

    def ejecutar_descarga_en_visor(self, chrome, prefijo_archivo: str):
        """Presiona el botón de descarga dentro del visor de imágenes."""
        try:
            self._esperar_visor_abierto(chrome)
            antes = set(DOWNLOAD_DIR.glob("*"))
            self._click_descargar_en_visor(chrome)
            archivo = self._esperar_archivo_descargado(antes)
            if archivo:
                self._renombrar_descarga(archivo, prefijo_archivo)
            else:
                logging.warning("No se detectó archivo descargado tras pulsar descargar.")
        except Exception:
            logging.exception("No se pudo descargar la imagen")

    def _esperar_visor_abierto(self, chrome):
        """Espera a que el visor de multimedia esté completamente visible."""
        selectores_visor = [
            "//*[@aria-label='Descargar' or @aria-label='Download' or @title='Descargar' or @title='Download']",
            "//*[@aria-label='Siguiente' or @aria-label='Next' or @title='Siguiente' or @title='Next']",
            "//*[@aria-label='Cerrar' or @aria-label='Close' or @title='Cerrar' or @title='Close']",
            "//*[@data-icon='ic-download' or @data-icon='download']",
        ]
        for xpath in selectores_visor:
            try:
                WebDriverWait(chrome, 5).until(EC.presence_of_element_located((By.XPATH, xpath)))
                return
            except TimeoutException:
                continue
        raise TimeoutException("No se detectó apertura del visor de imagen.")

    def _click_descargar_en_visor(self, chrome):
        """Click robusto del botón Descargar con múltiples variantes de selector."""
        candidatos = [
            "//button[@aria-label='Descargar' or @title='Descargar']",
            "//button[@aria-label='Download' or @title='Download']",
            "//*[@role='button' and (@title='Descargar' or @aria-label='Descargar' or @title='Download' or @aria-label='Download')]",
            "//*[self::button or self::div][.//*[@data-icon='ic-download' or @data-icon='download']]",
            "//*[@data-icon='ic-download' or @data-icon='download']/ancestor::*[self::button or @role='button'][1]",
        ]

        ultimo_error = None
        for xpath in candidatos:
            try:
                btn = WebDriverWait(chrome, 4).until(EC.presence_of_element_located((By.XPATH, xpath)))
                chrome.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                try:
                    WebDriverWait(chrome, 2).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    btn.click()
                except Exception:
                    chrome.execute_script("arguments[0].click();", btn)
                return
            except Exception as exc:
                ultimo_error = exc
                continue

        raise TimeoutException(f"No se encontró botón de descarga en el visor: {ultimo_error}")

    def _tiene_boton_siguiente(self, chrome) -> bool:
        """Indica si el visor tiene navegación al siguiente elemento."""
        xpath = (
            "//button[@aria-label='Siguiente' or @title='Siguiente' or @aria-label='Next' or @title='Next']"
            " | //*[@role='button' and (@aria-label='Siguiente' or @title='Siguiente' or @aria-label='Next' or @title='Next')]"
        )
        return bool(chrome.find_elements(By.XPATH, xpath))

    def _click_siguiente_en_visor(self, chrome, timeout: int = 4) -> bool:
        """Avanza a la siguiente imagen del álbum."""
        candidatos = [
            "//button[@aria-label='Siguiente' or @title='Siguiente']",
            "//button[@aria-label='Next' or @title='Next']",
            "//*[@role='button' and (@aria-label='Siguiente' or @title='Siguiente' or @aria-label='Next' or @title='Next')]",
            "//*[self::button or self::div][.//*[@data-icon='ic-chevron-right']]",
            "//*[@data-icon='ic-chevron-right']/ancestor::*[self::button or @role='button'][1]",
        ]

        for xpath in candidatos:
            try:
                btn = WebDriverWait(chrome, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
                try:
                    btn.click()
                except Exception:
                    chrome.execute_script("arguments[0].click();", btn)
                return True
            except Exception:
                continue
        return False

    def _obtener_estado_carrusel(self, chrome):
        """Retorna (actual, total) leyendo textos tipo '1 de 4' en el visor."""
        candidatos = chrome.find_elements(By.XPATH, "//span[contains(normalize-space(.), ' de ')]")
        for c in candidatos:
            texto = _normalizar_texto(c.text)
            match = re.search(r"^(\d+)\s+de\s+(\d+)$", texto)
            if match:
                return int(match.group(1)), int(match.group(2))
        return None

    def cerrar_visor(self, chrome):
        """Cierra el visor de imágenes (botón X o tecla Esc)."""
        try:
            btn_cerrar = chrome.find_element(
                By.XPATH,
                "//button[@aria-label='Cerrar' or @title='Cerrar' or @aria-label='Close' or @title='Close'] | //*[@role='button' and (@title='Cerrar' or @aria-label='Cerrar' or @title='Close' or @aria-label='Close')]"
            )
            try:
                btn_cerrar.click()
            except Exception:
                chrome.execute_script("arguments[0].click();", btn_cerrar)
        except:
            # Si falla el clic, mandamos la tecla Escape
            from selenium.webdriver.common.keys import Keys
            chrome.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)


    def _obtener_contenedor_scroll_chat(self, chrome):
        """Localiza de forma robusta el contenedor que realmente hace scroll en el chat."""
        candidatos_xpath = [
            "//div[@id='main']//div[contains(@class, 'copyable-area')]",
            "//div[@id='main']//div[@role='application']",
            "//div[@id='main']//div[contains(@class, '_aiy2')]",
            "//div[@id='main']//div[contains(@class, '_amk4')]",
        ]

        for xpath in candidatos_xpath:
            elementos = chrome.find_elements(By.XPATH, xpath)
            for el in elementos:
                try:
                    if chrome.execute_script("return arguments[0].scrollHeight > arguments[0].clientHeight", el):
                        return el
                except Exception:
                    continue

        try:
            return WebDriverWait(chrome, 20).until(
                lambda drv: drv.execute_script(
                    """
                    const main = document.querySelector('#main');
                    if (!main) return null;
                    const all = [main, ...main.querySelectorAll('div')];
                    return all.find(el => el.scrollHeight > el.clientHeight + 40) || null;
                    """
                )
            )
        except TimeoutException:
            return None

    def _fecha_visible_en_chat(self, chrome, fecha_objetivo: str) -> bool:
        """Valida fecha solo contra separadores de fecha del chat (no contra textos de mensajes)."""
        spans_fecha = chrome.find_elements(
            By.XPATH,
            "//div[@id='main']//div[contains(@class,'x141l45o')]//span[@dir='auto']"
        )
        for span in spans_fecha:
            if _normalizar_texto(span.text) == fecha_objetivo and span.is_displayed():
                return True
        return False

    def _obtener_mensajes_de_fecha(self, chrome, fecha_objetivo: str):
        """Obtiene mensajes del día objetivo respetando el orden real del timeline."""
        objetivo_normalizado = _normalizar_texto(fecha_objetivo)

        mensajes = chrome.execute_script(
            r"""
            const normalizar = (v) => (v || '').toLowerCase().trim().replace(/\s+/g, ' ');
            const objetivo = arguments[0];
            const main = document.querySelector('#main');
            if (!main) return [];

            const nodos = main.querySelectorAll('div.x141l45o, div.message-in, div.message-out');
            let fechaActual = '';
            const salida = [];

            for (const nodo of nodos) {
                if (nodo.classList.contains('x141l45o')) {
                    const spanFecha = nodo.querySelector("span[dir='auto']");
                    if (spanFecha) fechaActual = normalizar(spanFecha.textContent);
                    continue;
                }

                if (!nodo.classList.contains('message-in') && !nodo.classList.contains('message-out')) {
                    continue;
                }

                if (fechaActual === objetivo) {
                    salida.push(nodo);
                }
            }

            return salida;
            """,
            objetivo_normalizado,
        )

        return mensajes or []

    def _obtener_remitente(self, mensaje) -> str:
        candidatos = mensaje.find_elements(By.XPATH, ".//span[contains(@class, '_ahxv')] | .//span[contains(@class,'_ahxu')]")
        for candidato in candidatos:
            texto = (candidato.text or "").strip()
            if texto:
                return texto
        return "desconocido"

    def _crear_prefijo_nombre(self, fecha: str, remitente: str) -> str:
        limpio = f"{_normalizar_texto(fecha)}_{_normalizar_texto(remitente)}"
        return re.sub(r"[^a-zA-Z0-9_-]+", "_", limpio).strip("_") or "imagen"

    def _esperar_archivo_descargado(self, archivos_antes: set[Path], timeout: int = 20):
        fin = time.time() + timeout
        while time.time() < fin:
            actuales = set(DOWNLOAD_DIR.glob("*"))
            nuevos = [f for f in actuales - archivos_antes if f.is_file() and not f.name.endswith(".crdownload")]
            if nuevos and not list(DOWNLOAD_DIR.glob("*.crdownload")):
                return max(nuevos, key=lambda f: f.stat().st_mtime)
            time.sleep(0.4)
        return None

    def _renombrar_descarga(self, archivo: Path, prefijo: str):
        sufijo = archivo.suffix or ".jpg"
        destino = DOWNLOAD_DIR / f"{prefijo}{sufijo}"
        contador = 1
        while destino.exists():
            destino = DOWNLOAD_DIR / f"{prefijo}_{contador:02d}{sufijo}"
            contador += 1
        archivo.rename(destino)
        logging.info(f"Imagen guardada en {destino.name}")

    @staticmethod
    def get_chrome(headless: bool) -> WebDriver:
        """
        Configura e instancia el ChromeDriver siguiendo las buenas prácticas.
        """
        logging.info("Iniciando navegador Chrome con Selenium...")
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)

        options = Options()
        
        options.add_argument(f"--user-data-dir={PROFILE_DIR.as_posix()}")
        prefs = {
            "download.default_directory": str(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        options.add_experimental_option("prefs", prefs)
        
        if headless:
            options.add_argument("--headless=new")

        # Configuraciones generales para evitar detección y mejorar compatibilidad
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=es-CL")

        # Omitir la detección de automatización
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Opciones de estabilidad
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # Habilitar logs de performance y consola (Siguiendo tu primer ejemplo)
        options.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
        options.add_experimental_option("perfLoggingPrefs", {"enableNetwork": True, "enablePage": False})

        logging.info("Configurando ChromeDriver para ambiente local...")
        # Es importante pasar 'options=options' de forma explícita
        return webdriver.Chrome(options=options)
    

if __name__ == "__main__":
    service = WhatsAppService()
    try:
        service.obtener_imagenes()
    except KeyboardInterrupt:
        logging.info("Proceso interrumpido por el usuario.")

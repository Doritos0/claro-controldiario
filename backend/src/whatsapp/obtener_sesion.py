import logging
import json
import time
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
            Sube en el chat poco a poco hasta que la etiqueta de fecha (ej. 'Ayer') sea visible.
            """
            logging.info(f"Buscando la etiqueta de fecha: {fecha_objetivo}...")
            
            # Identificamos el contenedor de los mensajes que tiene el scroll
            # En la estructura actual es el div con id='main' y una clase interna que suele ser '_am78'
            try:
                contenedor_chat = chrome.find_element(By.XPATH, "//div[@id='main']//div[contains(@class, '_am78')]")
            except:
                # Si cambia la clase, intentamos por el rol general
                contenedor_chat = chrome.find_element(By.XPATH, "//div[@role='application' and @data-tab='8']")

            intentos = 0
            max_intentos = 15 # Para no subir infinitamente si la fecha no existe
            
            while intentos < max_intentos:
                try:
                    # Buscamos el span que contiene el texto exacto (ej: 'Ayer', 'Hoy' o '04/03/2026')
                    xpath_fecha = f"//span[text()='{fecha_objetivo}']"
                    elemento_fecha = chrome.find_element(By.XPATH, xpath_fecha)
                    
                    if elemento_fecha.is_displayed():
                        logging.info(f"¡Etiqueta '{fecha_objetivo}' localizada!")
                        return True
                except:
                    # Si no lo encuentra, hace scroll hacia arriba
                    logging.info("Fecha no visible, subiendo...")
                    chrome.execute_script("arguments[0].scrollTop -= 1200", contenedor_chat)
                    time.sleep(2) # Esperar a que carguen los mensajes antiguos
                    intentos += 1
            
            return False

    def procesar_imagenes_del_dia(self, chrome, fecha_objetivo: str):
        """
        Orquesta el scroll y la descarga.
        """
        encontrado = self.hacer_scroll_hasta_fecha(chrome, fecha_objetivo)
        
        if not encontrado:
            logging.warning(f"No se pudo encontrar la sección de {fecha_objetivo} tras varios intentos.")
            return

        # Una vez encontrada la fecha, recolectamos los mensajes que están debajo
        # Usamos los selectores basados en el HTML que pasaste
        logging.info("Analizando mensajes de la sección...")
        
        # Seleccionamos todos los bloques de mensajes
        mensajes = chrome.find_elements(By.XPATH, "//div[contains(@class, 'message-in') or contains(@class, 'message-out')]")
        
        for msg in mensajes:
            try:
                data_id = msg.get_attribute("data-id") or ""
                
                # Caso A: Es un ÁLBUM (Mosaico)
                # Según tu HTML: data-id="album-false_..."
                if "album" in data_id:
                    logging.info("Elemento identificado como ÁLBUM.")
                    self.descargar_album(chrome, msg)
                
                # Caso B: Es una IMAGEN SOLITARIA
                # Según tu HTML: div role="button" aria-label="Abrir foto"
                else:
                    botones_foto = msg.find_elements(By.XPATH, ".//div[@role='button' and @aria-label='Abrir foto']")
                    if botones_foto:
                        logging.info("Elemento identificado como FOTO SOLITARIA.")
                        self.descargar_foto_unica(chrome, botones_foto[0])
                        
            except Exception as e:
                continue

    def descargar_foto_unica(self, chrome, elemento_click):
        """Abre una foto, la descarga y cierra el visor."""
        elemento_click.click()
        self.ejecutar_descarga_en_visor(chrome)
        self.cerrar_visor(chrome)

    def descargar_album(self, chrome, contenedor_album):
        """Entra en un álbum y recorre las fotos descargando una a una."""
        # Hacemos clic en la primera imagen del álbum
        primera_foto = contenedor_album.find_element(By.XPATH, ".//div[@role='button']")
        primera_foto.click()
        
        while True:
            # Descargamos la foto actual
            self.ejecutar_descarga_en_visor(chrome)
            
            # Intentamos ir a la siguiente
            try:
                # El botón 'Siguiente' suele tener aria-label="Siguiente"
                btn_sig = WebDriverWait(chrome, 2).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Siguiente']"))
                )
                btn_sig.click()
                time.sleep(1) # Esperar a que cargue la siguiente imagen del álbum
            except TimeoutException:
                # Si no hay botón 'Siguiente', hemos llegado al final del álbum
                logging.info("Fin del álbum alcanzado.")
                break
        
        self.cerrar_visor(chrome)

    def ejecutar_descarga_en_visor(self, chrome):
        """Presiona el botón de descarga dentro del visor de imágenes."""
        try:
            # El botón de descarga tiene un título "Descargar"
            btn_descarga = WebDriverWait(chrome, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@title='Descargar']"))
            )
            btn_descarga.click()
            time.sleep(1) # Tiempo para que el navegador procese la descarga
        except Exception as e:
            logging.error(f"No se pudo descargar la imagen: {e}")

    def cerrar_visor(self, chrome):
        """Cierra el visor de imágenes (botón X o tecla Esc)."""
        try:
            btn_cerrar = chrome.find_element(By.XPATH, "//div[@title='Cerrar']")
            btn_cerrar.click()
        except:
            # Si falla el clic, mandamos la tecla Escape
            from selenium.webdriver.common.keys import Keys
            chrome.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)

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
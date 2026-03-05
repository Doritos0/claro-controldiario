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
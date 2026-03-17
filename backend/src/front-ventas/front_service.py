import json
import logging
import time
import os
from pathlib import Path

from src.config.log_config import configurar_log
from src.bd.bd_credenciales import CredencialesService

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

configurar_log()

class FrontService:
    def __init__(self):
        self.credenciales_service = CredencialesService()

    def obtener_excel(self, empresa_id):
        chrome = self.get_chrome(headless=True)
        wait = WebDriverWait(chrome, timeout=20, poll_frequency=0.5)

        if empresa_id == 1:

            credenciales = self.credenciales_service.get_credenciales_sql(empresa_id=empresa_id)

            for n in credenciales:
                logging.info(f"Ingresando las credenciales para usuario {n.usuario_id}")
                logging.info(f"Login Usuario: {n.login_user}")
                logging.info(f"Login Password: {n.login_pass}")
                try:
                    # 1. Proceso de Login
                    url = "https://fvc-prod.clarovtrcloud.com/#/login"
                    chrome.get(url)
                    logging.info(f"Navegando a pagina de login...")
                    wait.until(EC.title_contains("Front Ventas Convergente"))
                    
                    logging.info(f"Llenando campo de usuario...")
                    input_user = wait.until(EC.presence_of_element_located((By.ID, "loginUser")))
                    input_user.send_keys(n.login_user)
                    logging.info(f"Usuario ingresado {n.login_user}...")
                    
                    input_pass = wait.until(EC.presence_of_element_located((By.ID, "loginPass")))
                    input_pass.send_keys(n.login_pass)
                    logging.info(f"Contraseña ingresada {n.login_pass}...")
                    
                    boton_login = wait.until(EC.element_to_be_clickable((By.ID, "loginBtn")))
                    boton_login.click()
                    logging.info(f"Ingresando...")
                    
                    wait.until(EC.presence_of_element_located((By.ID, "user")))
                
                    url_dashboard = "https://fvc-prod.clarovtrcloud.com/#/home/dashboard"
                    max_intentos = 3
                    intento_actual = 0
                    cargado_exitosamente = False

                    while intento_actual < max_intentos and not cargado_exitosamente:
                        try:
                            logging.info(f"Intento {intento_actual + 1}: Navegando al dashboard...")
                            chrome.get(url_dashboard)
                            
                            # Esperamos que el header del dashboard exista (aunque haya un spinner encima)
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "dashboard-header")))
                            
                            # Intentamos esperar que la capa de carga desaparezca, pero no morimos si no lo hace
                            try:
                                wait_spinner = WebDriverWait(chrome, timeout=10)
                                wait_spinner.until(EC.invisibility_of_element_located((By.CLASS_NAME, "block-ui-wrapper")))
                                logging.info("La capa de carga desapareció normalmente.")
                            except TimeoutException:
                                logging.warning("La capa de carga sigue presente visualmente. Se procederá a eliminarla por JS.")
                            
                            cargado_exitosamente = True
                        except TimeoutException:
                            intento_actual += 1
                            logging.warning(f"No se detectó el dashboard en el intento {intento_actual}. Reintentando...")

                    if not cargado_exitosamente:
                        raise Exception("No se pudo acceder al contenido del dashboard.")

                    # 3. Limpieza de interfaz y Descarga
                    logging.info("Limpiando capas de bloqueo...")
                    # Eliminamos cualquier spinner que esté tapando los botones
                    chrome.execute_script("""
                        var elements = document.getElementsByClassName('block-ui-wrapper');
                        while(elements.length > 0){
                            elements[0].parentNode.removeChild(elements[0]);
                        }
                    """)

                    logging.info(f"Buscando boton de transacciones...")
                    # XPath basado en tu estructura divDataDashboard
                    xpath_transacciones = '//*[@id="divDataDashboard"]/div/button'
                    boton_transacciones = wait.until(EC.presence_of_element_located((By.XPATH, xpath_transacciones)))
                    chrome.execute_script("arguments[0].click();", boton_transacciones)
                    logging.info(f"Boton transacciones clickeado...")

                    logging.info(f"Buscando boton de descarga...")
                    # XPath flexible que busca el botón por el texto "Descargar"
                    xpath_descarga = "//button[contains(., 'Descargar')]"
                    boton_descarga = wait.until(EC.presence_of_element_located((By.XPATH, xpath_descarga)))
                    chrome.execute_script("arguments[0].click();", boton_descarga)
                    logging.info(f"Boton descarga clickeado...")
                    
                    # Tiempo de espera para que la descarga finalice
                    logging.info("Esperando 10 segundos para completar la descarga...")
                    time.sleep(10)

                except Exception as e:
                    logging.error(f"Error en el proceso: {str(e)}")
                    raise
            chrome.quit()

        else:
            return 0

    @staticmethod
    def get_chrome(headless: bool) -> WebDriver:
        logging.info(f"Iniciando navegador chrome...")
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_argument("--window-size=1366,768")
        options.add_argument("--lang=es-CL")

        # Evitar detección de automatización
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        logging.info("Configurando ChromeDriver para ambiente local...")

        
        carpeta = Path(__file__).resolve().parent.parent
        ruta_excels = carpeta / "front-web"
        ruta_excels.mkdir(exist_ok=True)

        logging.info(f"Path obtenido {carpeta}")

        prefs = {
            "download.default_directory": str(ruta_excels), 
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        return webdriver.Chrome(options=options)

if __name__ == "__main__":
    logging.info(f"Inicializando servicio...")
    front_service = FrontService()
    logging.info(f"Obteniendo excel...")
    try:
        front_service.obtener_excel(1)
    except Exception as e:
        logging.error(f"Fallo critico: {e}")
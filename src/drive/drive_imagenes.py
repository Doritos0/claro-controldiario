import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

from src.bd.bd_ejecutivo import EjecutivoService

load_dotenv()

credenciales = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")

class DriveImagenesService:
    def __init__(self, credentials_path: str, root_folder_id: str):
        self.credentials_path = credentials_path
        self.root_folder_id = root_folder_id
        self.ejecutivo_service = EjecutivoService()
        self.drive = self._autenticar()

    def _autenticar(self):
        logging.info(f"Funcion de autenticación comienza ejecución")
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile(credenciales)

        if gauth.access_token_expired:
            gauth.Refresh()
            gauth.SaveCredentialsFile(credenciales)
        else:
            gauth.Authorize()

        logging.info(f"Funcion de autenticación finalizada")
        return GoogleDrive(gauth)
    
    def encontrar_archivo(self, query: str):
        logging.info(f"Se esta buscando en Drive con la siguiente query {query}")
        return self.drive.ListFile({'q': query}).GetList()
    
    def obtener_imagenes(self, fecha: str = None, full_scan: bool = False) -> list[dict]:
        logging.info(f"Se estan obteniendo imagenes para la siguiente fecha {fecha}, full-scan {full_scan}")
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        if not fecha and not full_scan:
            fecha = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%y")

        hoy = datetime.now()
        nombre_mes_anio = f"{meses[hoy.month-1]} {hoy.year}" if full_scan else None

        if not full_scan:
            dia, mes_num, anio = fecha.split("/")
            nombre_mes_anio = f"{meses[int(mes_num)-1]} 20{anio}"

        query_mes = f"title = '{nombre_mes_anio}' and '{self.root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        carpetas_mes = self.encontrar_archivo(query_mes)

        if not carpetas_mes:
            logging.error(f"No se encontró la carpeta del mes: {nombre_mes_anio}")
            return []
        
        id_mes = carpetas_mes[0]['id']
        resultados = []

        ejecutivos = self.ejecutivo_service.get_ejecutivos_sql()

        for ejecutivo in ejecutivos:
            logging.info(f"Se esta buscando por ejecutivo")
            query_ejec = f"title = '{ejecutivo.nombre}' and '{id_mes}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            carpetas_ejec = self.encontrar_archivo(query_ejec)

            if not carpetas_ejec: continue

            ejecutivo_id = carpetas_ejec[0]['id']

            query_dias = f"'{ejecutivo_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

            if not full_scan:
                query_dias += f" and title = '{fecha}'"

            carpetas_dias = self.encontrar_archivo(query_dias)

            for dia in carpetas_dias:
                logging.info(f"Se esta buscando entre las carpetas de dias - {dia['title']}")
                query_img = f"'{dia['id']}' in parents and mimeType contains 'image/' and trashed = false"
                imagenes = self.encontrar_archivo(query_img)

                query_excel = f"'{dia['id']}' in parents and (mimeType = 'application/vnd.google-apps.spreadsheet' or mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or mimeType = 'application/vnd.ms-excel') and trashed = false"

                excels = self.encontrar_archivo(query_excel)

                logging.info(f"Se encontraron {len(imagenes)} imagenes")
                logging.info(f"Se encontraron {len(excels)} excels")

                for img in imagenes:
                    logging.info(f"Descargando: {img['title']} - ID {img['id']} ({ejecutivo.nombre} - {dia['title']})")
                    images_bytes = self.descargar(img['id'])
                    resultados.append({
                        "ejecutivo": ejecutivo,
                        "data": images_bytes,
                        "filename": img['title'],
                        "fecha": dia['title']
                    })

                for exc in excels:
                    print(f"Acá ira codigo de procesamiento de excel")

        logging.info(f"Servicio de descarga de imagenes completado se envian {len(resultados)} imagenes")
        return resultados
    
    def descargar(self, file_id: str):
        request = self.drive.auth.service.files().get_media(fileId = file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logging.info(f"Progreso descarga {file_id}: {int(status.progress() * 100)}%")
        return fh.getvalue()
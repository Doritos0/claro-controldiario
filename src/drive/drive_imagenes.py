import os
import logging
from datetime import datetime, timedelta
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from src.bd.bd_ejecutivo import EjecutivoService

class DriveImagenesService:
    def __init__(self, credentials_path: str, root_folder_id: str):
        self.scopes = ['https://www.googleapis.com/auth/drive.readonly']
        self.credentials_path = credentials_path
        self.root_folder_id = root_folder_id
        
        # Autenticación y creación del cliente
        self.drive_service = self._autenticar()
        self.ejecutivo_service = EjecutivoService()

    def _autenticar(self):
        """Maneja el flujo de OAuth2 para Desktop App."""
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.scopes)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        return build('drive', 'v3', credentials=creds)

    def obtener_imagenes(self, fecha: str = None, full_scan: bool = False) -> list[dict]:
        """
        Si full_scan es True, ignora la fecha y trae TODO lo del mes actual.
        Si full_scan es False, trae solo lo de la fecha (o ayer).
        """
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        # Manejo de fecha por defecto (Ayer)
        if not fecha and not full_scan:
            ayer = datetime.now() - timedelta(days=1)
            fecha = ayer.strftime("%d/%m/%y")

        # Determinar el Mes a buscar
        if full_scan:
            hoy = datetime.now()
            nombre_mes_anio = f"{meses[hoy.month - 1]} {hoy.year}"
            logging.info(f"MODO FULL SCAN: Buscando todo en {nombre_mes_anio}")
        else:
            dia, mes_num, anio = fecha.split("/")
            nombre_mes_anio = f"{meses[int(mes_num)-1]} 20{anio}"
            logging.info(f"MODO FECHA: Buscando para el día {fecha} en {nombre_mes_anio}")

        id_mes = self._buscar_por_nombre(nombre_mes_anio, self.root_folder_id)
        if not id_mes:
            logging.error(f"No se encontró la carpeta del mes: {nombre_mes_anio}")
            return []

        resultados = []
        ejecutivos = self.ejecutivo_service.get_ejecutivos_sql()

        for ejecutivo in ejecutivos:
            id_ejecutivo = self._buscar_por_nombre(ejecutivo.nombre, id_mes)
            if not id_ejecutivo:
                continue
                
            if full_scan:
                # Buscamos todas las subcarpetas (que son los días) dentro del ejecutivo
                carpetas_dias = self._listar_subcarpetas(id_ejecutivo)
                for id_dia, nombre_dia in carpetas_dias:
                    archivos = self._listar_archivos_en_carpeta(id_dia)
                    for f_id, f_name in archivos:
                        resultados.append(self._preparar_item(ejecutivo, f_id, f_name, nombre_dia))
            else:
                # Búsqueda normal por una sola fecha
                id_dia = self._buscar_por_nombre(fecha, id_ejecutivo)
                if id_dia:
                    archivos = self._listar_archivos_en_carpeta(id_dia)
                    for f_id, f_name in archivos:
                        resultados.append(self._preparar_item(ejecutivo, f_id, f_name, fecha))

        return resultados

    def _listar_subcarpetas(self, parent_id: str):
        """Auxiliar para listar carpetas (días) de un ejecutivo"""
        query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        response = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        return [(f['id'], f['name']) for f in response.get('files', [])]

    def _preparar_item(self, ejecutivo, f_id, f_name, fecha_str):
        """Auxiliar para no repetir código de descarga"""
        logging.info(f"Descargando {f_name} del día {fecha_str} para {ejecutivo.nombre}")
        return {
            "ejecutivo": ejecutivo,
            "data": self._download_file(f_id),
            "filename": f_name,
            "fecha": fecha_str
        }

    def _buscar_por_nombre(self, nombre: str, parent_id: str):
        query = (f"name = '{nombre}' and '{parent_id}' in parents and "
                 f"mimeType = 'application/vnd.google-apps.folder' and trashed = false")
        response = self.drive_service.files().list(q=query, fields="files(id)").execute()
        files = response.get('files', [])
        return files[0]['id'] if files else None

    def _listar_archivos_en_carpeta(self, folder_id: str):
        query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
        response = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        return [(f['id'], f['name']) for f in response.get('files', [])]

    def _download_file(self, file_id: str):
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh.getvalue()
import os
import logging
from datetime import datetime, timedelta
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class DriveImagenesService:
    def __init__(self, credentials_path: str, root_folder_id: str):
        self.scopes = ['https://www.googleapis.com/auth/drive.readonly']
        self.credentials_path = credentials_path
        self.root_folder_id = root_folder_id
        
        # Autenticación y creación del cliente
        self.service = self._autenticar()
        
        self.ejecutivos = [
            "Ada Rengifo", "Bárbara Cruz", "Daniela Baeza", 
            "Paulina Cataldo", "Rafael Cayun", "Tania Alviar"
        ]

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

    def obtener_imagenes_del_dia(self, fecha: str = None) -> list[dict]:
        """
        Navega por la estructura: Root -> Mes -> Ejecutivo -> Día
        fecha format: "DD/MM/YY" (ej: "18/02/26")
        """
        if not fecha:
            ayer = datetime.now() - timedelta(days=1)
            fecha = ayer.strftime("%d/%m/%y")
        
        dia, mes_num, anio = fecha.split("/")
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        nombre_mes_anio = f"{meses[int(mes_num)-1]} 20{anio}"

        logging.info(f"Iniciando búsqueda para el día {fecha}...")
        
        # 1. Buscar carpeta del Mes
        id_mes = self._buscar_por_nombre(nombre_mes_anio, self.root_folder_id)
        if not id_mes:
            logging.error(f"No se encontró la carpeta del mes: {nombre_mes_anio}")
            return []

        resultados = []

        # 2. Iterar ejecutivos
        for ejecutivo in self.ejecutivos:
            logging.debug(f"Buscando carpeta de {ejecutivo}...")
            id_ejecutivo = self._buscar_por_nombre(ejecutivo, id_mes)
            
            if id_ejecutivo:
                # 3. Buscar carpeta del Día
                id_dia = self._buscar_por_nombre(fecha, id_ejecutivo)
                
                if id_dia:
                    # 4. Listar y descargar imágenes
                    archivos = self._listar_archivos_en_carpeta(id_dia)
                    for f_id, f_name in archivos:
                        logging.info(f"Descargando imagen: {f_name} de {ejecutivo}")
                        img_data = self._download_file(f_id)
                        
                        resultados.append({
                            "ejecutivo": ejecutivo,
                            "data": img_data,
                            "filename": f_name,
                            "fecha": fecha
                        })
                else:
                    logging.warning(f"No hay carpeta del día {fecha} para {ejecutivo}")
            else:
                logging.warning(f"No se encontró carpeta para el ejecutivo: {ejecutivo}")

        return resultados

    def _buscar_por_nombre(self, nombre: str, parent_id: str):
        """Busca una carpeta por nombre dentro de un padre específico."""
        query = (f"name = '{nombre}' and '{parent_id}' in parents and "
                 f"mimeType = 'application/vnd.google-apps.folder' and trashed = false")
        response = self.service.files().list(q=query, fields="files(id)").execute()
        files = response.get('files', [])
        return files[0]['id'] if files else None

    def _listar_archivos_en_carpeta(self, folder_id: str):
        """Retorna lista de (id, name) de imágenes en una carpeta."""
        query = f"'{folder_id}' in parents and mimeType contains 'image/' and trashed = false"
        response = self.service.files().list(q=query, fields="files(id, name)").execute()
        return [(f['id'], f['name']) for f in response.get('files', [])]

    def _download_file(self, file_id: str):
        """Descarga el contenido del archivo en bytes."""
        request = self.service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh.getvalue()
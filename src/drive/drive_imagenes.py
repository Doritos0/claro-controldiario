import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
from io import BytesIO

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
        logging.info("Iniciando autenticación Drive")
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile(self.credentials_path or credenciales)

        if gauth.access_token_expired:
            gauth.Refresh()
            gauth.SaveCredentialsFile(self.credentials_path or credenciales)
        else:
            gauth.Authorize()

        logging.info("Autenticación Drive OK")
        return GoogleDrive(gauth)

    def encontrar_archivo(self, query: str):
        logging.info("Query Drive: %s", query)
        return self.drive.ListFile({"q": query}).GetList()

    def obtener_imagenes(self, fecha: str = None, full_scan: bool = False) -> list[dict]:
        logging.info("Obteniendo imágenes fecha=%s full_scan=%s", fecha, full_scan)
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
        ]

        if not fecha and not full_scan:
            fecha = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%y")

        hoy = datetime.now()
        nombre_mes_anio = f"{meses[hoy.month-1]} {hoy.year}" if full_scan else None

        if not full_scan:
            _, mes_num, anio = fecha.split("/")
            nombre_mes_anio = f"{meses[int(mes_num)-1]} 20{anio}"

        query_mes = (
            f"title = '{nombre_mes_anio}' and '{self.root_folder_id}' in parents "
            "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )
        carpetas_mes = self.encontrar_archivo(query_mes)

        if not carpetas_mes:
            logging.warning("No se encontró carpeta mes %s", nombre_mes_anio)
            return []

        id_mes = carpetas_mes[0]["id"]
        resultados = []

        ejecutivos = self.ejecutivo_service.get_ejecutivos_sql()

        for ejecutivo in ejecutivos:
            query_ejec = (
                f"title = '{ejecutivo.nombre}' and '{id_mes}' in parents "
                "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            )
            carpetas_ejec = self.encontrar_archivo(query_ejec)
            if not carpetas_ejec:
                continue

            ejecutivo_id = carpetas_ejec[0]["id"]
            query_dias = f"'{ejecutivo_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            if not full_scan:
                query_dias += f" and title = '{fecha}'"

            carpetas_dias = self.encontrar_archivo(query_dias)

            for dia in carpetas_dias:
                query_img = f"'{dia['id']}' in parents and mimeType contains 'image/' and trashed = false"
                imagenes = self.encontrar_archivo(query_img)

                for img in imagenes:
                    image_bytes = self.descargar(img["id"])
                    resultados.append(
                        {
                            "ejecutivo": ejecutivo,
                            "data": image_bytes,
                            "filename": img["title"],
                            "fecha": dia["title"],
                            "drive_file_id": img["id"],
                        }
                    )

        logging.info("Descarga de imágenes completada: %s", len(resultados))
        return resultados

    def descargar(self, file_id: str):
        request = self.drive.auth.service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return fh.getvalue()

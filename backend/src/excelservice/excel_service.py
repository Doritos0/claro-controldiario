import logging
from pathlib import Path
import pandas as pd


class ExcelService:
    @staticmethod
    def procesar_excel():
        base_dir = Path(__file__).resolve().parent.parent
        ruta_excel = base_dir / "front-web"
        archivos = list(ruta_excel.glob("*.xlsx"))
        dfs = []

        for excel in archivos:
            logging.info(f"Leyendo {excel}")
            df = pd.read_excel(excel)
            dfs.append(df)
        return dfs

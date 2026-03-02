from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

import pandas as pd


@dataclass
class ExcelRulesResult:
    leads: int | None
    ventas: int | None
    total_rows: int
    warnings: list[str] = field(default_factory=list)


class ExcelRulesService:
    REQUIRED_COLUMNS = {"rutCliente", "descEstado"}

    def process_excel_bytes(self, excel_bytes: bytes) -> ExcelRulesResult:
        df = pd.read_excel(BytesIO(excel_bytes))
        total_rows = len(df)

        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            return ExcelRulesResult(
                leads=None,
                ventas=None,
                total_rows=total_rows,
                warnings=[f"Columnas faltantes: {', '.join(sorted(missing))}"],
            )

        rut_series = (
            df["rutCliente"]
            .dropna()
            .astype(str)
            .str.strip()
        )
        rut_series = rut_series[rut_series != ""]
        leads = int(rut_series.nunique())

        estado_series = (
            df["descEstado"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )
        ventas = int((estado_series == "pedidosya").sum())
        return ExcelRulesResult(leads=leads, ventas=ventas, total_rows=total_rows)

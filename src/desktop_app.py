from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageTk

from src.proceso_01_ocr import ejecutar_proceso_ocr_con_resultado
from src.reportes.dashboard_diario_service import resolver_fecha_objetivo


class ControlDiarioApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Claro | Control Diario")
        self.root.geometry("1120x760")
        self.root.minsize(1000, 700)

        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.fecha_modo = tk.StringVar(value="ayer")
        self.fecha_manual = tk.StringVar(value=(datetime.now() - timedelta(days=1)).strftime("%d/%m/%y"))
        self.status_text = tk.StringVar(value="Inicia sesión para generar tu reporte.")

        self._dashboard_path: Path | None = None
        self._img_ref: ImageTk.PhotoImage | None = None

        self.login_frame: ttk.Frame | None = None
        self.main_frame: ttk.Frame | None = None
        self.image_label: ttk.Label | None = None
        self.btn_generar: ttk.Button | None = None
        self.btn_guardar: ttk.Button | None = None

        self._build_login()

    def _build_login(self) -> None:
        self.login_frame = ttk.Frame(self.root, padding=32)
        self.login_frame.pack(expand=True)

        ttk.Label(self.login_frame, text="CLARO | CONTROL DIARIO", font=("Segoe UI", 20, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 24)
        )
        ttk.Label(self.login_frame, text="Usuario:").grid(row=1, column=0, sticky="e", padx=(0, 10), pady=8)
        ttk.Entry(self.login_frame, textvariable=self.username, width=28).grid(row=1, column=1, sticky="w")

        ttk.Label(self.login_frame, text="Contraseña:").grid(row=2, column=0, sticky="e", padx=(0, 10), pady=8)
        ttk.Entry(self.login_frame, textvariable=self.password, show="*", width=28).grid(row=2, column=1, sticky="w")

        ttk.Button(self.login_frame, text="Iniciar sesión", command=self._login).grid(
            row=3, column=0, columnspan=2, pady=(20, 0)
        )

    def _build_main(self) -> None:
        self.main_frame = ttk.Frame(self.root, padding=16)
        self.main_frame.pack(fill="both", expand=True)

        header = ttk.Label(self.main_frame, text="Generar reporte de control diario", font=("Segoe UI", 16, "bold"))
        header.pack(anchor="w", pady=(0, 8))

        options_frame = ttk.LabelFrame(self.main_frame, text="Opciones")
        options_frame.pack(fill="x", pady=(0, 10))

        ttk.Radiobutton(
            options_frame, text="Usar fecha de ayer (por defecto)", value="ayer", variable=self.fecha_modo
        ).grid(row=0, column=0, sticky="w", padx=10, pady=8)

        ttk.Radiobutton(
            options_frame, text="Elegir fecha (dd/mm/yy)", value="manual", variable=self.fecha_modo
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

        ttk.Entry(options_frame, textvariable=self.fecha_manual, width=14).grid(row=1, column=1, sticky="w", padx=(4, 10))

        button_bar = ttk.Frame(self.main_frame)
        button_bar.pack(fill="x", pady=(0, 10))

        self.btn_generar = ttk.Button(button_bar, text="Generar reporte", command=self._generar_reporte)
        self.btn_generar.pack(side="left")

        self.btn_guardar = ttk.Button(button_bar, text="Descargar dashboard", command=self._descargar_dashboard, state="disabled")
        self.btn_guardar.pack(side="left", padx=(8, 0))

        ttk.Label(self.main_frame, textvariable=self.status_text).pack(anchor="w", pady=(4, 8))

        image_frame = ttk.LabelFrame(self.main_frame, text="Dashboard generado")
        image_frame.pack(fill="both", expand=True)

        self.image_label = ttk.Label(image_frame, text="Aún no se ha generado ningún dashboard.", anchor="center")
        self.image_label.pack(fill="both", expand=True, padx=8, pady=8)

    def _login(self) -> None:
        expected_user = "admin"
        expected_password = "claro123"

        if self.username.get().strip() == expected_user and self.password.get() == expected_password:
            assert self.login_frame is not None
            self.login_frame.destroy()
            self._build_main()
            self.status_text.set("Sesión iniciada. Selecciona fecha y genera el reporte.")
            return

        messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")

    def _generar_reporte(self) -> None:
        if self.btn_generar is not None:
            self.btn_generar.configure(state="disabled")

        self.status_text.set("Procesando información, por favor espera...")
        worker = threading.Thread(target=self._generar_reporte_worker, daemon=True)
        worker.start()

    def _generar_reporte_worker(self) -> None:
        try:
            if self.fecha_modo.get() == "manual":
                fecha_input = self.fecha_manual.get().strip()
                resolver_fecha_objetivo(fecha_input)
                result = ejecutar_proceso_ocr_con_resultado(fecha_objetivo=fecha_input, full_scan=False)
            else:
                result = ejecutar_proceso_ocr_con_resultado()

            self.root.after(0, lambda: self._post_generacion_result(result))
        except Exception as exc:
            self.root.after(0, lambda: self._post_generacion_error(exc))

    def _post_generacion_result(self, result) -> None:
        if self.btn_generar is not None:
            self.btn_generar.configure(state="normal")

        if result.dashboard_path is None:
            self.status_text.set(result.message)
            messagebox.showwarning("No se generó dashboard", result.message)
            self._intentar_configurar_root_folder(result.message)
            return

        self._dashboard_path = Path(result.dashboard_path)
        self.status_text.set(f"Dashboard generado correctamente: {self._dashboard_path.name}")
        self._mostrar_dashboard(self._dashboard_path)

        if self.btn_guardar is not None:
            self.btn_guardar.configure(state="normal")

    def _guardar_root_folder_id(self, folder_id: str) -> None:
        cfg_path = Path.cwd() / "app_config.json"
        cfg = {}
        if cfg_path.exists():
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                if not isinstance(cfg, dict):
                    cfg = {}
            except Exception:
                cfg = {}

        cfg["google_drive_root_folder_id"] = folder_id.strip()
        cfg.setdefault("google_drive_credentials_path", "credentials.json")
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    def _intentar_configurar_root_folder(self, message: str) -> bool:
        if "GOOGLE_DRIVE_ROOT_FOLDER_ID" not in message:
            return False

        folder_id = simpledialog.askstring(
            "Configuración inicial",
            "Ingresa el GOOGLE_DRIVE_ROOT_FOLDER_ID para dejar la app configurada:",
            parent=self.root,
        )
        if not folder_id:
            return False

        self._guardar_root_folder_id(folder_id)
        messagebox.showinfo("Configuración guardada", "Root Folder ID guardado. Vuelve a generar el reporte.")
        return True

    def _post_generacion_error(self, exc: Exception) -> None:
        if self.btn_generar is not None:
            self.btn_generar.configure(state="normal")

        self.status_text.set("Ocurrió un error durante la generación del reporte.")
        messagebox.showerror("Error", str(exc))

    def _mostrar_dashboard(self, path: Path) -> None:
        if self.image_label is None:
            return

        image = Image.open(path)
        image.thumbnail((1000, 520))
        self._img_ref = ImageTk.PhotoImage(image)

        self.image_label.configure(image=self._img_ref, text="")

    def _descargar_dashboard(self) -> None:
        if self._dashboard_path is None:
            messagebox.showwarning("Sin dashboard", "Primero debes generar un dashboard.")
            return

        destino = filedialog.asksaveasfilename(
            title="Guardar dashboard",
            defaultextension=".png",
            initialfile=self._dashboard_path.name,
            filetypes=[("PNG", "*.png")],
        )

        if not destino:
            return

        Path(destino).write_bytes(self._dashboard_path.read_bytes())
        messagebox.showinfo("Descarga completa", f"Dashboard guardado en:\n{destino}")


def run_desktop_app() -> None:
    root = tk.Tk()
    app = ControlDiarioApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_desktop_app()

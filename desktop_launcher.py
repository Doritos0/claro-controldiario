import os
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def _repo_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def _wait_port(host: str, port: int, timeout_s: float = 25) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            try:
                sock.connect((host, port))
                return True
            except OSError:
                time.sleep(0.25)
    return False


def _resolve_node_binary(root: Path) -> str:
    if os.name == "nt":
        packaged = root / "runtime" / "node" / "node.exe"
        if packaged.exists():
            return str(packaged)
    return "node"


def _resolve_whatsapp_command(root: Path, whatsapp_dir: Path) -> tuple[list[str], Path]:
    if os.name == "nt":
        bundled_service = root / "runtime" / "whatsapp-service" / "whatsapp-service.exe"
        if bundled_service.exists():
            return [str(bundled_service)], bundled_service.parent

    return [_resolve_node_binary(root), "src/index.js"], whatsapp_dir


def main() -> int:
    root = _repo_root()
    backend_dir = root / "backend"
    whatsapp_dir = backend_dir / "whatsapp-service"
    frontend_dist = root / "frontend" / "dist"

    env = os.environ.copy()
    env.setdefault("NODE_PORT", "3000")
    env.setdefault("FRONTEND_ORIGIN", "http://127.0.0.1:5173")

    app_data = Path(env.get("APP_DATA_DIR", Path.home() / ".claro-control-diario"))
    env["APP_DATA_DIR"] = str(app_data)
    env.setdefault("DOWNLOADS_DIR", str(app_data / "descargas"))

    processes: list[subprocess.Popen] = []

    try:
        whatsapp_cmd, whatsapp_cwd = _resolve_whatsapp_command(root, whatsapp_dir)
        processes.append(subprocess.Popen(whatsapp_cmd, cwd=whatsapp_cwd, env=env))

        py_cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ]
        processes.append(subprocess.Popen(py_cmd, cwd=backend_dir, env=env))

        if frontend_dist.exists():
            ui_cmd = [sys.executable, "-m", "http.server", "5173", "--bind", "127.0.0.1"]
            processes.append(subprocess.Popen(ui_cmd, cwd=frontend_dist, env=env))
        else:
            print("[WARN] frontend/dist no existe; la UI no se servirá.")

        if not _wait_port("127.0.0.1", 3000):
            print("[ERROR] Node no levantó en puerto 3000")
            return 1
        if not _wait_port("127.0.0.1", 8000):
            print("[ERROR] FastAPI no levantó en puerto 8000")
            return 1

        if frontend_dist.exists() and _wait_port("127.0.0.1", 5173, timeout_s=8):
            webbrowser.open("http://127.0.0.1:5173")
            print("UI abierta en http://127.0.0.1:5173")
        else:
            print("API FastAPI: http://127.0.0.1:8000/swagger")
            print("API Node: http://127.0.0.1:3000/docs")

        print("Presiona Ctrl+C para cerrar.")
        while True:
            for proc in processes:
                if proc.poll() is not None:
                    print(f"[ERROR] Proceso terminado inesperadamente: pid={proc.pid} code={proc.returncode}")
                    return 1
            time.sleep(1)

    except KeyboardInterrupt:
        return 0
    finally:
        for proc in processes:
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
        time.sleep(1)
        for proc in processes:
            if proc.poll() is None:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())

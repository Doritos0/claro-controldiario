import logging
from pathlib import Path


def configurar_log(log_file: str = "logs.txt"):
    log_path = Path(log_file)
    if not log_path.is_absolute():
        log_path = Path.cwd() / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[stream_handler, file_handler],
        force=True,
    )

    logging.getLogger().info("Logging inicializado en %s", log_path)

    # Asegurarte de que los loggers de uvicorn propaguen al root y que no tengan handlers propios duplicados
    logging.getLogger("uvicorn").handlers = []
    logging.getLogger("uvicorn").propagate = True

    logging.getLogger("uvicorn.error").handlers = []
    logging.getLogger("uvicorn.error").propagate = True

    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True

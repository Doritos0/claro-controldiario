from pathlib import Path

from dotenv import load_dotenv
from src.bd.inicializacion.bd_datos import inicializar_datos


local_path = Path(__file__).parent
env_path = local_path.parent / ".env"
load_dotenv(env_path)

def main():
    inicializar_datos()


if __name__ == "__main__":
    main()
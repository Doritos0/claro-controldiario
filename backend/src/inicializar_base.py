from pathlib import Path

from dotenv import load_dotenv

local_path = Path(__file__).parent
env_path = local_path.parent / ".env"
load_dotenv(env_path)

from src.bd.inicializacion.bd_init import inicializar_bd_sqlite

def main():
    inicializar_bd_sqlite()

if __name__ == "__main__":
    main()
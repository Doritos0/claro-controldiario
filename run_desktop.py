from src.runtime_setup import bootstrap_runtime


def main() -> None:
    bootstrap_runtime()

    from src.desktop_app import run_desktop_app

    run_desktop_app()


if __name__ == "__main__":
    main()

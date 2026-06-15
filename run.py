import argparse

from app.main import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sistema inteligente de diagnostico de fallas en logs.")
    parser.add_argument("--log", help="Ruta del archivo log a analizar", default=None)
    args = parser.parse_args()
    main(args.log)

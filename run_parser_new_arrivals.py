from pathlib import Path
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"
PARSER_FILE = BASE_DIR / "parser" / "rinkan_parser_v4.py"
OUTPUT_FILE = BASE_DIR / "rinkan_products_v4.json"


def main() -> None:
    if not VENV_PYTHON.exists():
        print(f"Не найден интерпретатор: {VENV_PYTHON}")
        print("Создай окружение проекта и поставь зависимости.")
        sys.exit(1)

    if not PARSER_FILE.exists():
        print(f"Не найден парсер: {PARSER_FILE}")
        sys.exit(1)

    command = [
        str(VENV_PYTHON),
        str(PARSER_FILE),
        "--start-url",
        "https://rinkan-online.com/new-arrivals?stockLimit=1",
        "--pages",
        "1",
        "--limit",
        "50",
        "--delay",
        "0.2",
        "--output",
        str(OUTPUT_FILE),
    ]
    subprocess.run(command, cwd=BASE_DIR, check=True)


if __name__ == "__main__":
    main()

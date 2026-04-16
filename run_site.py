from pathlib import Path
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"
BACKEND_MAIN = BASE_DIR / "backend" / "main.py"


def main() -> None:
    if not VENV_PYTHON.exists():
        print(f"Не найден интерпретатор: {VENV_PYTHON}")
        print("Создай окружение проекта и поставь зависимости.")
        sys.exit(1)

    if not BACKEND_MAIN.exists():
        print(f"Не найден файл запуска: {BACKEND_MAIN}")
        sys.exit(1)

    command = [str(VENV_PYTHON), str(BACKEND_MAIN)]
    subprocess.run(command, cwd=BASE_DIR, check=True)


if __name__ == "__main__":
    main()

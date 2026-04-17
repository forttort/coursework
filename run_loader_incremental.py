from pathlib import Path
import os
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"
LOADER_FILE = BASE_DIR / "loader" / "load_rinkan_to_postgres.py"
INPUT_FILE = BASE_DIR / "rinkan_products_v4.json"
DEFAULT_DATABASE_URL = "postgresql://danil@localhost:5432/coursework"


def main() -> None:
    if not VENV_PYTHON.exists():
        print(f"Не найден интерпретатор: {VENV_PYTHON}")
        sys.exit(1)

    if not LOADER_FILE.exists():
        print(f"Не найден loader: {LOADER_FILE}")
        sys.exit(1)

    environment = os.environ.copy()
    database_url = environment.get("DATABASE_URL", DEFAULT_DATABASE_URL)

    command = [
        str(VENV_PYTHON),
        str(LOADER_FILE),
        "--input",
        str(INPUT_FILE),
        "--dsn",
        database_url,
        "--mode",
        "incremental",
    ]
    subprocess.run(command, cwd=BASE_DIR, env=environment, check=True)


if __name__ == "__main__":
    main()

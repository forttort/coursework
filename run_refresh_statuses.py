from pathlib import Path
import os
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"
REFRESH_FILE = BASE_DIR / "loader" / "refresh_product_statuses.py"
DEFAULT_DATABASE_URL = "postgresql://danil@localhost:5432/coursework"


def main() -> None:
    if not VENV_PYTHON.exists():
        print(f"Не найден интерпретатор: {VENV_PYTHON}")
        sys.exit(1)

    if not REFRESH_FILE.exists():
        print(f"Не найден refresh script: {REFRESH_FILE}")
        sys.exit(1)

    environment = os.environ.copy()
    database_url = environment.get("DATABASE_URL", DEFAULT_DATABASE_URL)

    command = [
        str(VENV_PYTHON),
        str(REFRESH_FILE),
        "--dsn",
        database_url,
        "--limit",
        "100",
        "--delay",
        "0.2",
        "--statuses",
        "active,missing",
    ]
    subprocess.run(command, cwd=BASE_DIR, env=environment, check=True)


if __name__ == "__main__":
    main()

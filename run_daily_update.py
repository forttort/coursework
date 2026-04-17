from pathlib import Path
import os
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"
PARSER_WRAPPER = BASE_DIR / "run_parser_new_arrivals.py"
LOADER_WRAPPER = BASE_DIR / "run_loader_incremental.py"
REFRESH_WRAPPER = BASE_DIR / "run_refresh_statuses.py"


def run_step(script_path: Path, environment: dict[str, str]) -> None:
    if not script_path.exists():
        print(f"Не найден шаг pipeline: {script_path}")
        sys.exit(1)

    command = [str(VENV_PYTHON), str(script_path)]
    subprocess.run(command, cwd=BASE_DIR, env=environment, check=True)


def main() -> None:
    if not VENV_PYTHON.exists():
        print(f"Не найден интерпретатор: {VENV_PYTHON}")
        sys.exit(1)

    environment = os.environ.copy()
    run_step(PARSER_WRAPPER, environment)
    run_step(LOADER_WRAPPER, environment)
    run_step(REFRESH_WRAPPER, environment)


if __name__ == "__main__":
    main()

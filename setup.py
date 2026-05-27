import os
import sys
import subprocess
import platform
from pathlib import Path

# --- Configuration ---
REPO_URL     = 'https://github.com/VALLABHANENI-KRISHNA/Learning_Automation.git'
PROJECT_NAME = 'Learning_Automation'
PYTHON_MIN   = (3, 8)


def print_step(step: str) -> None:
    print(f"\n{'='*50}")
    print(f"  {step}")
    print(f"{'='*50}")


def check_python_version() -> None:
    """Ensure Python version meets minimum requirement."""
    print_step("Checking Python version")
    current = sys.version_info[:2]
    if current < PYTHON_MIN:
        print(f"Error: Python {PYTHON_MIN[0]}.{PYTHON_MIN[1]}+ required. You have {current[0]}.{current[1]}")
        sys.exit(1)
    print(f"Python {current[0]}.{current[1]} — OK")


def create_venv() -> Path:
    """Create virtual environment if it doesn't exist."""
    print_step("Setting up virtual environment")
    venv_path = Path('venv')

    if venv_path.exists():
        print("Virtual environment already exists — skipping")
        return venv_path

    subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
    print("Virtual environment created")
    return venv_path


def get_pip_path() -> Path:
    """Return correct pip path for current OS."""
    if platform.system() == 'Windows':
        return Path('venv') / 'Scripts' / 'pip'
    return Path('venv') / 'bin' / 'pip'


def install_dependencies() -> None:
    """Install all packages from requirements.txt."""
    print_step("Installing dependencies")
    pip      = get_pip_path()
    req_file = Path('requirements.txt')

    if not req_file.exists():
        print("Error: requirements.txt not found")
        sys.exit(1)

    subprocess.run([str(pip), 'install', '-r', 'requirements.txt'], check=True)
    print("Dependencies installed")


def check_env_files() -> None:
    """Check for .env files and warn if missing."""
    print_step("Checking environment files")
    env_dirs = ['Day_2', 'Day_4']

    for dir_name in env_dirs:
        env_path     = Path(dir_name) / '.env'
        example_path = Path(dir_name) / '.env.example'

        if env_path.exists():
            print(f"{dir_name}/.env — found")
        elif example_path.exists():
            print(f"WARNING: {dir_name}/.env missing. Copy {dir_name}/.env.example and fill in your values.")
        else:
            print(f"WARNING: {dir_name}/.env missing. Create it with required variables.")


def verify_imports() -> None:
    """Test that all required packages import correctly."""
    print_step("Verifying package imports")
    packages = ['requests', 'bs4', 'pandas', 'schedule']

    all_ok = True
    for package in packages:
        try:
            __import__(package)
            print(f"  {package} — OK")
        except ImportError:
            print(f"  {package} — MISSING")
            all_ok = False

    if not all_ok:
        print("\nSome packages failed to import. Run: pip install -r requirements.txt")
        sys.exit(1)


def print_summary() -> None:
    """Print final setup summary."""
    print_step("Setup Complete")
    print("Your environment is ready. Next steps:")
    print("  1. Copy .env.example to .env in Day_2 and Day_4")
    print("  2. Fill in your API keys and credentials")
    print("  3. Run individual day scripts from their folders")
    print("\nQuick start:")
    print("  cd Day_2 && python weather.py Hyderabad")
    print("  cd Day_3 && python scraper.py")
    print("  cd Day_4 && python daily_digest.py")


if __name__ == '__main__':
    print("\nLearning Automation — Project Setup")
    print("This script will set up your development environment.\n")

    check_python_version()
    create_venv()
    install_dependencies()
    check_env_files()
    verify_imports()
    print_summary()
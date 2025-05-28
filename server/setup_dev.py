"""
Development environment setup script.
Creates a virtual environment and installs all dependencies.
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and print the output."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False

def setup_venv(venv_path):
    """Set up a Python virtual environment."""
    if not venv_path.exists():
        print(f"Creating virtual environment at {venv_path}...")
        if not run_command([sys.executable, "-m", "venv", str(venv_path)]):
            return False
    
    # Determine the correct pip command based on the platform
    pip_cmd = [
        str(venv_path / "Scripts" / "pip") if platform.system() == "Windows" 
        else str(venv_path / "bin" / "pip")
    ]
    
    # Upgrade pip
    if not run_command([*pip_cmd, "install", "--upgrade", "pip"]):
        return False
    
    # Install requirements
    if not run_command([*pip_cmd, "install", "-r", "requirements.txt"]):
        return False
    
    return True

def main():
    """Main setup function."""
    print("Setting up development environment...")
    
    # Create necessary directories
    Path("logs").mkdir(exist_ok=True)
    Path("datasets").mkdir(exist_ok=True)
    
    # Set up virtual environment
    venv_path = Path(".venv")
    if not setup_venv(venv_path):
        print("Failed to set up virtual environment.")
        return 1
    
    print("\nSetup completed successfully!")
    print("\nTo activate the virtual environment:")
    if platform.system() == "Windows":
        print(f"  .\\{venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")
    
    print("\nTo start the server:")
    print("  python start_server.py")
    
    print("\nTo run tests:")
    print("  python -m pytest tests/")
    
    print("\nTo run the example usage:")
    print("  python example_usage.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

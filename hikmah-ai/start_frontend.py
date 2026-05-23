"""
HIKMAH AI — Frontend launcher.
Run from the hikmah-ai directory:  python start_frontend.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  HIKMAH AI — Frontend")
    print("  Opening at: http://localhost:8501")
    print("="*60 + "\n")

    subprocess.run(
        [
            sys.executable, "-m", "streamlit", "run",
            str(ROOT / "frontend" / "app.py"),
            "--server.port", "8501",
            "--server.headless", "true",
            "--theme.base", "dark",
        ],
        cwd=str(ROOT),   # working dir = project root so imports resolve
        check=True,
    )

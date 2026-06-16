"""
Chesu — Entry Point
Run with: python main.py
"""

import subprocess
import sys
import os

def main():
    # Ensure we're running from the project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("Starting Chesu...")
    print("   Open your browser at: http://127.0.0.1:8004\n")

    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app:app",
        "--host", "127.0.0.1",
        "--port", "8004",
        "--reload"
    ])

if __name__ == "__main__":
    main()

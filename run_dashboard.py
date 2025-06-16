#!/usr/bin/env python3
"""Dashboard launcher for RAGTrace."""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the Streamlit dashboard."""
    dashboard_path = Path("src/presentation/web/main.py")
    
    if not dashboard_path.exists():
        print(f"Error: Dashboard file not found at {dashboard_path}")
        sys.exit(1)
    
    try:
        subprocess.run([
            "streamlit", "run", str(dashboard_path),
            "--server.port=8501",
            "--server.address=0.0.0.0"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running dashboard: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: streamlit not found. Please install it with: pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main()
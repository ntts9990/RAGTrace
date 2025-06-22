"""
RAGTrace Dashboard Launcher

This script is the official entry point for running the Streamlit dashboard.
It ensures that the application is run within the correct package context,
which resolves all relative import issues.

To run the dashboard, execute from the project root:
streamlit run dashboard.py
"""

from src.presentation.web.main import main

if __name__ == "__main__":
    main() 
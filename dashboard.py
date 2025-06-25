"""
RAGTrace Dashboard Launcher

This script is the official entry point for running the Streamlit dashboard.
It ensures that the application is run within the correct package context,
which resolves all relative import issues.

To run the dashboard, execute from the project root:
streamlit run dashboard.py
"""

# Streamlit 앱이므로 main.py의 내용을 직접 import
from src.presentation.web.main import * 
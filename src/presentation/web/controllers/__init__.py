"""
Web Controllers Package

웹 대시보드의 컨트롤러와 라우팅을 담당합니다.
"""

from .main_controller import MainController
from .page_controller import PageController

__all__ = [
    'MainController',
    'PageController'
]
"""
Refactored RAGTrace Dashboard using MVC Pattern

MVC 패턴을 적용한 리팩토링된 RAGTrace 대시보드입니다.
"""

from .controllers.main_controller import MainController


def main():
    """메인 애플리케이션 진입점"""
    app = MainController()
    app.run()


if __name__ == "__main__":
    main()
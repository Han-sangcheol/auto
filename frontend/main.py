"""
CleonAI Trading Platform Frontend

PySide6 기반 자동매매 GUI 애플리케이션
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import Qt
from services.api_client import APIClient
from views.main_window import MainWindow


class TradingApp(QApplication):
    """Trading 애플리케이션 클래스"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # 애플리케이션 메타데이터
        self.setApplicationName("CleonAI Trading Platform")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("CleonAI")
        
        # 고해상도 디스플레이 지원
        self.setAttribute(Qt.AA_EnableHighDpiScaling)
        self.setAttribute(Qt.AA_UseHighDpiPixmaps)
        
        # API 클라이언트 초기화
        self.api_client = APIClient()
        
        # 메인 윈도우 생성
        self.main_window = None
    
    def start(self):
        """애플리케이션 시작"""
        try:
            # Backend 연결 확인
            if not self.check_backend_connection():
                self.show_error(
                    "Backend 연결 실패",
                    "Backend 서버에 연결할 수 없습니다.\n"
                    "http://localhost:8000 에서 Backend가 실행 중인지 확인하세요."
                )
                return False
            
            # 메인 윈도우 생성 및 표시
            self.main_window = MainWindow(self.api_client)
            self.main_window.show()
            
            return True
            
        except Exception as e:
            self.show_error("시작 오류", f"애플리케이션 시작 중 오류가 발생했습니다:\n{str(e)}")
            return False
    
    def check_backend_connection(self) -> bool:
        """Backend 서버 연결 확인"""
        try:
            health = self.api_client.check_health()
            return health is not None
        except Exception:
            return False
    
    def show_error(self, title: str, message: str):
        """에러 메시지 표시"""
        QMessageBox.critical(None, title, message)


def main():
    """메인 함수"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║      🚀 CleonAI Trading Platform GUI v1.0               ║
    ║                                                          ║
    ║      PySide6 기반 자동매매 시스템                        ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    app = TradingApp(sys.argv)
    
    if app.start():
        sys.exit(app.exec())
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()


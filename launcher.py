"""
CleonAI Trading Platform - 통합 런처
하나의 명령으로 모든 서비스를 시작합니다.
"""

import subprocess
import time
import sys
import os
import signal
from pathlib import Path

class CleonAILauncher:
    def __init__(self):
        self.processes = []
        self.root_dir = Path(__file__).parent
        
    def print_header(self):
        print("=" * 60)
        print("  CleonAI Trading Platform")
        print("  통합 런처")
        print("=" * 60)
        print()
        
    def start_backend(self):
        """Backend 서버 시작"""
        print("[1/3] Backend 서버 시작 중...")
        backend_dir = self.root_dir / "backend"
        
        # 간단한 테스트 서버 실행
        process = subprocess.Popen(
            [sys.executable, "test_server.py"],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
        self.processes.append(("Backend", process))
        print("   ✓ Backend 시작됨 (PID: {})".format(process.pid))
        time.sleep(3)  # Backend가 시작될 때까지 대기
        
    def start_frontend(self):
        """Frontend GUI 시작"""
        print("[2/3] Frontend GUI 시작 중...")
        frontend_dir = self.root_dir / "frontend"
        main_file = frontend_dir / "main.py"
        
        if not main_file.exists():
            print("   ⚠ Frontend 파일이 없습니다. 간단한 테스트 GUI를 생성합니다...")
            self.create_simple_frontend()
        
        # Frontend 실행 - 오류 로그를 파일로 저장
        log_file = self.root_dir / "frontend_error.log"
        with open(log_file, 'w', encoding='utf-8') as f:
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=str(frontend_dir),
                stdout=f,
                stderr=f,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
        
        self.processes.append(("Frontend", process))
        print("   ✓ Frontend 시작됨 (PID: {})".format(process.pid))
        print("   📝 오류 발생 시 frontend_error.log를 확인하세요")
        time.sleep(2)
        
        # 프로세스가 즉시 종료되었는지 확인
        if process.poll() is not None:
            print("   ⚠ Frontend가 종료되었습니다. 오류를 확인하세요:")
            with open(log_file, 'r', encoding='utf-8') as f:
                error_content = f.read()
                if error_content:
                    print("   " + "\n   ".join(error_content.split('\n')[:10]))  # 처음 10줄만
        
    def start_trading_engine(self):
        """Trading Engine 시작 (선택)"""
        print("[3/3] Trading Engine...")
        print("   ℹ Trading Engine은 32-bit Python과 키움 API가 필요합니다.")
        print("   ℹ 필요시 수동으로 실행하세요: trading-engine/engine/main.py")
        
    def create_simple_frontend(self):
        """간단한 테스트 Frontend 생성"""
        frontend_dir = self.root_dir / "frontend"
        frontend_dir.mkdir(exist_ok=True)
        
        frontend_code = '''"""
CleonAI Trading Platform - 간단한 Frontend
"""

import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QPushButton, QTextEdit, QTabWidget
)
from PySide6.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CleonAI Trading Platform")
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 제목
        title = QLabel("CleonAI Trading Platform")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 상태 표시
        self.status_label = QLabel("Backend 연결 확인 중...")
        layout.addWidget(self.status_label)
        
        # API 테스트 버튼
        test_btn = QPushButton("Backend API 테스트")
        test_btn.clicked.connect(self.test_api)
        layout.addWidget(test_btn)
        
        # 결과 표시
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        
        # 타이머로 자동 연결 확인
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_backend)
        self.timer.start(5000)  # 5초마다
        
        # 초기 연결 확인
        self.check_backend()
    
    def check_backend(self):
        """Backend 연결 확인"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                self.status_label.setText("✓ Backend 연결됨")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setText("✗ Backend 오류")
                self.status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.status_label.setText("✗ Backend 연결 안됨")
            self.status_label.setStyleSheet("color: red;")
    
    def test_api(self):
        """API 테스트"""
        self.result_text.append("\\n=== API 테스트 시작 ===")
        
        try:
            # Health check
            response = requests.get("http://localhost:8000/health")
            self.result_text.append(f"Health Check: {response.json()}")
            
            # Root endpoint
            response = requests.get("http://localhost:8000/")
            self.result_text.append(f"Root: {response.json()}")
            
            # Account endpoint
            response = requests.get("http://localhost:8000/api/v1/account")
            self.result_text.append(f"Accounts: {response.json()}")
            
            self.result_text.append("✓ 모든 테스트 성공!")
            
        except Exception as e:
            self.result_text.append(f"✗ 오류: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
'''
        
        with open(frontend_dir / "main.py", "w", encoding="utf-8") as f:
            f.write(frontend_code)
        
        print("   ✓ 간단한 Frontend 생성 완료")
    
    def check_status(self):
        """서비스 상태 확인"""
        print()
        print("=" * 60)
        print("  실행 중인 서비스")
        print("=" * 60)
        for name, process in self.processes:
            status = "실행 중" if process.poll() is None else "중지됨"
            print(f"  {name}: {status} (PID: {process.pid})")
        print()
        
    def show_info(self):
        """접속 정보 표시"""
        print("=" * 60)
        print("  접속 정보")
        print("=" * 60)
        print("  Backend API:  http://localhost:8000")
        print("  API 문서:     http://localhost:8000/docs")
        print("  Frontend:     GUI 창 열림")
        print()
        print("  종료하려면 Ctrl+C를 누르세요")
        print("=" * 60)
        
    def cleanup(self):
        """프로세스 정리"""
        print()
        print("서비스를 종료하는 중...")
        for name, process in self.processes:
            if process.poll() is None:
                print(f"  {name} 종료 중...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print("모든 서비스가 종료되었습니다.")
    
    def run(self):
        """런처 실행"""
        try:
            self.print_header()
            
            # 서비스 시작
            self.start_backend()
            self.start_frontend()
            self.start_trading_engine()
            
            # 상태 확인
            self.check_status()
            self.show_info()
            
            # 실행 유지
            print("서비스가 실행 중입니다...")
            while True:
                time.sleep(1)
                # 프로세스가 모두 종료되었는지 확인
                if all(p.poll() is not None for _, p in self.processes):
                    print("모든 서비스가 종료되었습니다.")
                    break
                    
        except KeyboardInterrupt:
            print("\n\n사용자가 종료를 요청했습니다.")
        finally:
            self.cleanup()

def main():
    launcher = CleonAILauncher()
    launcher.run()

if __name__ == "__main__":
    main()


# CleonAI Trading Platform - 빠른 시작

## 🚀 한 번에 실행하기

### 방법 1: 배치 파일 (가장 쉬움)

**Windows 탐색기에서:**
1. `START.bat` 파일을 더블클릭

**또는 PowerShell에서:**
```powershell
.\START.ps1
```

---

### 방법 2: Python 직접 실행

```powershell
python launcher.py
```

---

## ✅ 실행되는 서비스

실행하면 자동으로 다음 서비스들이 시작됩니다:

1. **Backend API Server** (http://localhost:8000)
   - REST API 서버
   - 별도 콘솔 창에서 실행

2. **Frontend GUI**
   - PySide6 기반 GUI 애플리케이션
   - 자동으로 Backend에 연결

3. **Trading Engine** (선택 사항)
   - 32-bit Python + 키움 API 필요
   - 수동 실행 권장

---

## 📊 확인 방법

### Backend API 확인
브라우저에서 다음 URL 접속:
- http://localhost:8000 - 메인 페이지
- http://localhost:8000/docs - API 문서 (Swagger UI)
- http://localhost:8000/health - 헬스 체크

### Frontend 확인
- GUI 창이 자동으로 열립니다
- "Backend API 테스트" 버튼을 클릭하여 연결 확인

---

## 🛑 종료 방법

### Ctrl+C
런처 창에서 `Ctrl+C`를 누르면 모든 서비스가 자동으로 종료됩니다.

---

## 🔧 문제 해결

### 패키지 설치 오류
```powershell
# Backend 패키지 설치
pip install fastapi uvicorn python-multipart websockets sqlalchemy pydantic python-dotenv loguru redis aioredis

# Frontend 패키지 설치
pip install PySide6 requests
```

### 포트 충돌 (8000 포트가 이미 사용 중)
```powershell
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8000

# 프로세스 종료 (PID 확인 후)
taskkill /PID <PID> /F
```

### Backend 시작 실패
`backend/test_server.py` 파일이 있는지 확인:
```powershell
ls backend/test_server.py
```

없다면 launcher.py가 자동으로 생성합니다.

---

## 📁 프로젝트 구조

```
D:\cleonAI\
├── START.bat              # ← 이 파일을 더블클릭!
├── START.ps1              # PowerShell 버전
├── launcher.py            # 통합 런처
├── backend/
│   └── test_server.py     # 간단한 테스트 서버
├── frontend/
│   └── main.py            # GUI 애플리케이션
└── trading-engine/
    └── engine/main.py     # 매매 엔진 (선택)
```

---

## 💡 다음 단계

1. **API 테스트**
   - http://localhost:8000/docs 에서 API 테스트

2. **Frontend 사용**
   - GUI에서 "Backend API 테스트" 버튼 클릭

3. **Trading Engine 연결** (선택)
   - 키움 API 설치
   - 32-bit Python 설치
   - `trading-engine/engine/main.py` 실행

---

## 📚 더 자세한 문서

- [배포 가이드](docs/DEPLOYMENT.md)
- [API 문서](docs/API.md)
- [사용자 매뉴얼](docs/USER_MANUAL.md)
- [개발자 가이드](docs/DEVELOPER_GUIDE.md)

---

**문제가 있나요?**
- GitHub Issues: https://github.com/yourusername/cleonai-trading-platform/issues
- Email: support@cleonai.com

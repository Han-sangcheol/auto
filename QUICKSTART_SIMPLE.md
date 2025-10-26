# 🚀 CleonAI Trading Platform - 초간단 시작 가이드

## 단 3단계로 시작!

### 1단계: 파일 더블클릭 ⭐

```
D:\cleonAI\ 폴더에서
START.bat 파일을 더블클릭!
```

### 2단계: 3개 창 확인

실행되면 3개의 창이 열립니다:

1. **런처 창** (메인)
   - 모든 서비스 상태 표시
   - Ctrl+C로 모두 종료 가능

2. **Backend 콘솔** 
   - API 서버 실행
   - http://localhost:8000

3. **Frontend GUI**
   - 예쁜 GUI 화면
   - Backend API 테스트 가능

### 3단계: 테스트

**Frontend GUI에서:**
- "🔍 Backend API 테스트" 버튼 클릭
- 계좌 정보가 표시되면 성공!

**또는 브라우저에서:**
- http://localhost:8000/docs
- API 문서 확인

---

## 🛑 종료 방법

**런처 창**(첫 번째 창)에서:
```
Ctrl + C 누르기
```

→ 모든 서비스가 자동으로 종료됩니다!

---

## 💡 문제 해결

### Frontend 창이 바로 닫히면?

패키지 설치:
```powershell
pip install PySide6 requests
```

### Backend가 시작 안 되면?

패키지 설치:
```powershell
pip install fastapi uvicorn
```

### 포트 충돌 (8000 포트 사용 중)?

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 📁 생성된 창 설명

| 창 | 설명 | 종료 방법 |
|----|------|-----------|
| 런처 | 메인 컨트롤 | Ctrl+C |
| Backend | API 서버 | 자동 종료 |
| Frontend | GUI | 자동 종료 |

---

## 🎯 다음 단계

1. ✅ Frontend GUI에서 "Backend API 테스트" 클릭
2. ✅ 브라우저에서 http://localhost:8000/docs 접속
3. ✅ API 문서에서 직접 API 테스트

---

## 📞 도움이 필요하면?

1. `frontend_error.log` 파일 확인
2. 런처 창의 오류 메시지 확인
3. [전체 문서](docs/DEPLOYMENT.md) 참고

---

**그게 전부입니다! 즐거운 매매 되세요! 🎉**



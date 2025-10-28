# CleonAI 빠른 시작 가이드

엔터프라이즈 자동매매 플랫폼을 5분 안에 시작하세요!

---

## ⚡ 최단 경로 (3단계)

### 1단계: START.bat 실행

```
D:\cleonAI\ 폴더에서
START.bat 파일을 더블클릭!
```

### 2단계: 3개 창 확인

자동으로 3개 창이 열립니다:

- **런처 창** - 모든 서비스 상태 표시
- **Backend 콘솔** - API 서버 (포트 8000)
- **Frontend GUI** - 매매 화면

### 3단계: 브라우저 확인 (선택)

```
http://localhost:8000/docs
```

→ Swagger UI에서 API 테스트 가능

---

## 📋 사전 요구사항

### 필수

- Windows 10/11 (64비트)
- Python 3.9 이상
- 키움증권 계좌 (모의투자 권장)

### Python 패키지 설치

프로그램이 자동으로 필요한 패키지를 설치합니다.  
수동 설치가 필요한 경우:

```powershell
# Backend
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis

# Frontend
pip install PySide6 pyqtgraph requests websocket-client
```

---

## 🎨 화면 구성

### 📊 대시보드

계좌 정보를 한눈에:

- 총 자산
- 현금
- 주식 평가액
- 손익률

### 💰 매매 화면

주문 실행:

1. 종목 코드 입력
2. 수량 입력
3. 매수/매도 버튼 클릭
4. 주문 내역 자동 표시

### 📈 차트

실시간 차트:

- 캔들스틱 차트
- 이동평균선 (MA)
- 볼린저 밴드
- 거래량

### 🚀 급등주 모니터

실시간 급등주 감지:

1. 감지 설정 (상승률, 거래량 기준)
2. 자동 감지 시작
3. 감지된 종목 자동 표시
4. 원클릭 매수 (선택)

### ⚙️ 설정

매매 전략 설정:

- **MA 전략**: 이동평균 교차
- **RSI 전략**: 과매수/과매도
- **MACD 전략**: MACD 교차
- **리스크 관리**: 손절/익절

### 📝 로그

실시간 로그 확인:

- 레벨별 필터 (DEBUG, INFO, WARNING, ERROR)
- 검색 기능
- 내보내기 (CSV)

---

## 🔧 문제 해결

### Frontend 창이 안 열리면?

```powershell
pip install PySide6 pyqtgraph requests websocket-client
```

### Backend가 시작 안 되면?

```powershell
pip install fastapi uvicorn sqlalchemy
```

### 포트 충돌 (8000 포트 사용 중)?

```powershell
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8000

# 프로세스 종료
taskkill /PID <PID번호> /F
```

### Trading Engine 오류?

32비트 Python 필요:

```powershell
cd trading-engine
# 32비트 Python 환경 활성화
.\.venv32\Scripts\Activate.ps1
```

---

## 📚 다음 단계

### 사용자

1. [사용자 매뉴얼](docs/user/USER_MANUAL.md) - 화면별 상세 사용법
2. [전략 설정](docs/user/USER_MANUAL.md#전략-설정) - 매매 전략 조정

### 개발자

1. [API 문서](docs/developer/API.md) - REST API 참조
2. [개발자 가이드](docs/developer/DEVELOPER_GUIDE.md) - 개발 환경 설정
3. [아키텍처](docs/architecture/ARCHITECTURE.md) - 시스템 구조

---

## 🔗 관련 링크

- [전체 문서](docs/)
- [프로젝트 상태](PROJECT_STATUS.md)
- [auto_trading (독립 프로젝트)](auto_trading/)

---

## 💡 팁

### 빠른 테스트

1. **모의투자 계좌 사용** (실계좌 사용 금지!)
2. **소액으로 시작** (1주씩 테스트)
3. **로그 확인** (실시간으로 동작 확인)

### 안전한 사용

1. **손절매 설정 필수** (기본값: -5%)
2. **포지션 크기 제한** (기본값: 계좌의 10%)
3. **일일 손실 한도** (기본값: -3%)

---

## ⚠️ 주의사항

- 실계좌 사용 전 모의투자로 충분히 테스트
- 리스크 관리 설정 필수
- 법적 규제 확인 (프로그램매매 신고 등)

---

**좋은 매매 되세요! 📈**

더 자세한 내용은 [docs/user/USER_MANUAL.md](docs/user/USER_MANUAL.md)를 참조하세요.


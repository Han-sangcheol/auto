# CleonAI Trading Platform - 개발자 가이드

## 목차

1. [개발 환경 설정](#개발-환경-설정)
2. [프로젝트 구조](#프로젝트-구조)
3. [코딩 규칙](#코딩-규칙)
4. [모듈 개발](#모듈-개발)
5. [테스트](#테스트)
6. [디버깅](#디버깅)
7. [기여 가이드](#기여-가이드)

---

## 개발 환경 설정

### 필수 도구

- **Python 3.10+** (64-bit for Backend/Frontend)
- **Python 3.10** (32-bit for Trading Engine)
- **Git**
- **Docker Desktop**
- **VS Code** (권장) 또는 PyCharm

### IDE 확장 프로그램 (VS Code)

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "njpwerner.autodocstring",
    "eamodio.gitlens"
  ]
}
```

### 가상환경 설정

#### Backend/Frontend (64-bit)

```powershell
# 가상환경 생성
python -m venv .venv

# 활성화
.\.venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt

# 개발 패키지 설치
pip install -r requirements-dev.txt
```

#### Trading Engine (32-bit)

```powershell
# 32-bit Python 설치 확인
where python32
# 또는
C:\Python310-32\python.exe --version

# 가상환경 생성
C:\Python310-32\python.exe -m venv .venv32

# 활성화
.\.venv32\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt
```

### 환경 변수 설정

```powershell
# .env 파일 생성
cp .env.example .env

# 필수 값 설정
# POSTGRES_PASSWORD=your_password
# REDIS_PASSWORD=your_password
# SECRET_KEY=your_secret_key
```

---

## 프로젝트 구조

### 디렉토리 구조

```
cleonai-trading-platform/
├── backend/               # FastAPI 백엔드
│   ├── app/
│   │   ├── api/          # API 엔드포인트
│   │   │   ├── v1/       # API v1
│   │   │   └── websocket.py
│   │   ├── core/         # 핵심 모듈
│   │   ├── db/           # 데이터베이스
│   │   ├── schemas/      # Pydantic 스키마
│   │   └── services/     # 비즈니스 로직
│   └── tests/            # 백엔드 테스트
│
├── frontend/             # PySide6 프론트엔드
│   ├── views/            # 화면 컴포넌트
│   ├── widgets/          # 재사용 위젯
│   ├── services/         # API/WebSocket 클라이언트
│   └── tests/            # 프론트엔드 테스트
│
├── trading-engine/       # 매매 엔진
│   ├── engine/
│   │   ├── core/         # 엔진 핵심
│   │   ├── strategies/   # 전략 모듈
│   │   ├── indicators/   # 기술 지표
│   │   ├── brokers/      # 브로커 어댑터
│   │   └── events/       # 이벤트 시스템
│   └── tests/            # 엔진 테스트
│
├── database/             # 데이터베이스 스키마
├── shared/               # 공유 라이브러리
├── docs/                 # 문서
└── scripts/              # 유틸리티 스크립트
```

### 모듈 의존성

```
Frontend ─→ Backend API (REST/WebSocket)
              ↓
         PostgreSQL
         Redis
              ↓
      Trading Engine ←─ Kiwoom API
```

---

## 코딩 규칙

### Python 스타일

- **PEP 8** 준수
- **타입 힌트** 사용
- **Docstring** 작성 (Google 스타일)
- **한글 주석** 허용 (비즈니스 로직)

### 예시

```python
from typing import List, Optional
from pydantic import BaseModel


class Order(BaseModel):
    """주문 데이터 모델
    
    Attributes:
        stock_code: 종목 코드
        quantity: 주문 수량
        price: 주문 가격
    """
    stock_code: str
    quantity: int
    price: Optional[float] = None


def create_order(
    account_id: int,
    stock_code: str,
    quantity: int,
    price: Optional[float] = None
) -> Order:
    """주문 생성
    
    Args:
        account_id: 계좌 ID
        stock_code: 종목 코드
        quantity: 주문 수량
        price: 주문 가격 (옵션)
    
    Returns:
        생성된 주문 객체
    
    Raises:
        ValueError: 수량이 0 이하인 경우
    """
    if quantity <= 0:
        raise ValueError("수량은 0보다 커야 합니다")
    
    # 주문 생성 로직
    order = Order(
        stock_code=stock_code,
        quantity=quantity,
        price=price
    )
    
    return order
```

### 네이밍 규칙

- **함수/변수**: `snake_case`
- **클래스**: `PascalCase`
- **상수**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

```python
# 좋은 예
class TradingEngine:
    MAX_STOCKS = 3
    
    def __init__(self):
        self.is_running = False
        self._internal_state = {}
    
    def start_trading(self):
        pass

# 나쁜 예
class tradingengine:  # PascalCase 사용
    maxStocks = 3     # camelCase 사용
    
    def StartTrading(self):  # snake_case 사용
        pass
```

---

## 모듈 개발

### Backend API 엔드포인트 추가

#### 1. 스키마 정의 (schemas/)

```python
# backend/app/schemas/watchlist.py
from pydantic import BaseModel
from typing import List
from datetime import datetime


class WatchlistCreate(BaseModel):
    """관심 종목 추가 요청"""
    stock_code: str
    stock_name: str
    memo: str = ""


class WatchlistResponse(BaseModel):
    """관심 종목 응답"""
    id: int
    account_id: int
    stock_code: str
    stock_name: str
    memo: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### 2. 데이터베이스 모델 (db/models.py)

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class Watchlist(Base):
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    stock_code = Column(String(6), nullable=False)
    stock_name = Column(String(50))
    memo = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("Account", back_populates="watchlists")
```

#### 3. Repository (db/repositories/)

```python
# backend/app/db/repositories/watchlist_repo.py
from typing import List
from sqlalchemy.orm import Session
from ..models import Watchlist
from ...schemas.watchlist import WatchlistCreate


class WatchlistRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, account_id: int) -> List[Watchlist]:
        """모든 관심 종목 조회"""
        return self.db.query(Watchlist).filter(
            Watchlist.account_id == account_id
        ).all()
    
    def create(
        self,
        account_id: int,
        data: WatchlistCreate
    ) -> Watchlist:
        """관심 종목 추가"""
        watchlist = Watchlist(
            account_id=account_id,
            stock_code=data.stock_code,
            stock_name=data.stock_name,
            memo=data.memo
        )
        self.db.add(watchlist)
        self.db.commit()
        self.db.refresh(watchlist)
        return watchlist
    
    def delete(self, watchlist_id: int) -> bool:
        """관심 종목 삭제"""
        watchlist = self.db.query(Watchlist).filter(
            Watchlist.id == watchlist_id
        ).first()
        if watchlist:
            self.db.delete(watchlist)
            self.db.commit()
            return True
        return False
```

#### 4. API 엔드포인트 (api/v1/)

```python
# backend/app/api/v1/watchlist.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...db.session import get_db
from ...db.repositories.watchlist_repo import WatchlistRepository
from ...schemas.watchlist import WatchlistCreate, WatchlistResponse


router = APIRouter()


@router.get("/{account_id}", response_model=List[WatchlistResponse])
def get_watchlists(
    account_id: int,
    db: Session = Depends(get_db)
):
    """관심 종목 목록 조회"""
    repo = WatchlistRepository(db)
    watchlists = repo.get_all(account_id)
    return watchlists


@router.post("/{account_id}", response_model=WatchlistResponse)
def add_watchlist(
    account_id: int,
    data: WatchlistCreate,
    db: Session = Depends(get_db)
):
    """관심 종목 추가"""
    repo = WatchlistRepository(db)
    watchlist = repo.create(account_id, data)
    return watchlist


@router.delete("/{watchlist_id}")
def delete_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db)
):
    """관심 종목 삭제"""
    repo = WatchlistRepository(db)
    if repo.delete(watchlist_id):
        return {"message": "삭제되었습니다"}
    raise HTTPException(status_code=404, detail="Not found")
```

#### 5. 라우터 등록 (main.py)

```python
# backend/app/main.py
from .api.v1 import watchlist

app.include_router(
    watchlist.router,
    prefix=f"{settings.API_V1_STR}/watchlist",
    tags=["watchlist"]
)
```

### Trading Engine 전략 추가

#### 1. 전략 클래스 생성

```python
# trading-engine/engine/strategies/volume_strategy.py
from typing import Optional
from .base import BaseStrategy, SignalType
from ..indicators.technical import calculate_volume_ratio


class VolumeStrategy(BaseStrategy):
    """거래량 돌파 전략
    
    거래량이 평균 대비 일정 비율 이상 증가하면 매수 신호
    """
    
    def __init__(
        self,
        volume_threshold: float = 2.0,
        lookback_period: int = 20
    ):
        """
        Args:
            volume_threshold: 거래량 배수 (예: 2.0 = 평균의 2배)
            lookback_period: 평균 거래량 계산 기간
        """
        super().__init__(name="VolumeStrategy")
        self.volume_threshold = volume_threshold
        self.lookback_period = lookback_period
    
    def generate_signal(
        self,
        stock_code: str,
        prices: list,
        volumes: list
    ) -> Optional[SignalType]:
        """신호 생성
        
        Args:
            stock_code: 종목 코드
            prices: 가격 리스트
            volumes: 거래량 리스트
        
        Returns:
            SignalType 또는 None
        """
        if len(volumes) < self.lookback_period:
            return None
        
        # 평균 거래량 계산
        avg_volume = sum(volumes[:-1]) / len(volumes[:-1])
        current_volume = volumes[-1]
        
        # 거래량 비율
        volume_ratio = current_volume / avg_volume
        
        # 신호 생성
        if volume_ratio >= self.volume_threshold:
            self.logger.info(
                f"{stock_code}: 거래량 돌파 ({volume_ratio:.2f}배)"
            )
            return SignalType.BUY
        
        return None
    
    def get_config(self) -> dict:
        """설정 반환"""
        return {
            "volume_threshold": self.volume_threshold,
            "lookback_period": self.lookback_period
        }
```

#### 2. 전략 등록

```python
# trading-engine/engine/core/engine.py
from ..strategies.volume_strategy import VolumeStrategy

def load_strategies(self):
    """전략 로드"""
    strategies = [
        MACrossoverStrategy(),
        RSIStrategy(),
        MACDStrategy(),
        VolumeStrategy(),  # 새 전략 추가
    ]
    return strategies
```

### Frontend 화면 추가

#### 1. View 클래스 생성

```python
# frontend/views/watchlist_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QPushButton, QLineEdit
)
from PySide6.QtCore import QTimer


class WatchlistView(QWidget):
    """관심 종목 화면"""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.account_id = 1  # TODO: 동적으로 가져오기
        self.setup_ui()
        self.load_watchlist()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 입력 폼
        form_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("종목 코드")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("종목명")
        self.add_btn = QPushButton("추가")
        self.add_btn.clicked.connect(self.add_watchlist)
        
        form_layout.addWidget(self.code_input)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.add_btn)
        layout.addLayout(form_layout)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "종목코드", "종목명", "메모", "삭제"
        ])
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def load_watchlist(self):
        """관심 종목 로드"""
        try:
            watchlists = self.api_client.get_watchlists(self.account_id)
            self.update_table(watchlists)
        except Exception as e:
            print(f"로드 실패: {e}")
    
    def add_watchlist(self):
        """관심 종목 추가"""
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()
        
        if not code or not name:
            return
        
        try:
            self.api_client.add_watchlist(
                self.account_id,
                code,
                name
            )
            self.code_input.clear()
            self.name_input.clear()
            self.load_watchlist()
        except Exception as e:
            print(f"추가 실패: {e}")
    
    def update_table(self, watchlists):
        """테이블 업데이트"""
        self.table.setRowCount(len(watchlists))
        for row, item in enumerate(watchlists):
            self.table.setItem(row, 0, QTableWidgetItem(item["stock_code"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["stock_name"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["memo"]))
            
            delete_btn = QPushButton("삭제")
            delete_btn.clicked.connect(
                lambda checked, id=item["id"]: self.delete_watchlist(id)
            )
            self.table.setCellWidget(row, 3, delete_btn)
    
    def delete_watchlist(self, watchlist_id):
        """관심 종목 삭제"""
        try:
            self.api_client.delete_watchlist(watchlist_id)
            self.load_watchlist()
        except Exception as e:
            print(f"삭제 실패: {e}")
```

#### 2. API Client 메서드 추가

```python
# frontend/services/api_client.py
def get_watchlists(self, account_id: int):
    """관심 종목 조회"""
    response = self.session.get(
        f"{self.api_v1}/watchlist/{account_id}"
    )
    response.raise_for_status()
    return response.json()

def add_watchlist(self, account_id: int, stock_code: str, stock_name: str):
    """관심 종목 추가"""
    data = {
        "stock_code": stock_code,
        "stock_name": stock_name
    }
    response = self.session.post(
        f"{self.api_v1}/watchlist/{account_id}",
        json=data
    )
    response.raise_for_status()
    return response.json()

def delete_watchlist(self, watchlist_id: int):
    """관심 종목 삭제"""
    response = self.session.delete(
        f"{self.api_v1}/watchlist/{watchlist_id}"
    )
    response.raise_for_status()
    return response.json()
```

#### 3. 메인 윈도우에 탭 추가

```python
# frontend/views/main_window.py
from .watchlist_view import WatchlistView

# 관심 종목 탭
watchlist_view = WatchlistView(self.api_client)
self.tabs.addTab(watchlist_view, "⭐ 관심 종목")
```

---

## 테스트

### 단위 테스트 (pytest)

#### Backend 테스트

```python
# backend/tests/test_watchlist.py
import pytest
from app.db.repositories.watchlist_repo import WatchlistRepository
from app.schemas.watchlist import WatchlistCreate


def test_create_watchlist(db_session):
    """관심 종목 생성 테스트"""
    repo = WatchlistRepository(db_session)
    
    data = WatchlistCreate(
        stock_code="005930",
        stock_name="삼성전자"
    )
    
    watchlist = repo.create(account_id=1, data=data)
    
    assert watchlist.id is not None
    assert watchlist.stock_code == "005930"
    assert watchlist.stock_name == "삼성전자"


def test_get_watchlists(db_session):
    """관심 종목 조회 테스트"""
    repo = WatchlistRepository(db_session)
    
    # 데이터 추가
    data1 = WatchlistCreate(stock_code="005930", stock_name="삼성전자")
    data2 = WatchlistCreate(stock_code="000660", stock_name="SK하이닉스")
    repo.create(account_id=1, data=data1)
    repo.create(account_id=1, data=data2)
    
    # 조회
    watchlists = repo.get_all(account_id=1)
    assert len(watchlists) == 2
```

#### Trading Engine 테스트

```python
# trading-engine/tests/test_volume_strategy.py
import pytest
from engine.strategies.volume_strategy import VolumeStrategy, SignalType


def test_volume_strategy_buy_signal():
    """거래량 돌파 매수 신호 테스트"""
    strategy = VolumeStrategy(volume_threshold=2.0)
    
    # 평균 거래량: 1000
    # 현재 거래량: 3000 (3배)
    volumes = [1000] * 20 + [3000]
    prices = [70000] * 21
    
    signal = strategy.generate_signal("005930", prices, volumes)
    assert signal == SignalType.BUY


def test_volume_strategy_no_signal():
    """신호 없음 테스트"""
    strategy = VolumeStrategy(volume_threshold=2.0)
    
    # 모든 거래량 동일
    volumes = [1000] * 21
    prices = [70000] * 21
    
    signal = strategy.generate_signal("005930", prices, volumes)
    assert signal is None
```

#### Frontend 테스트

```python
# frontend/tests/test_watchlist_view.py
import pytest
from PySide6.QtWidgets import QApplication
from views.watchlist_view import WatchlistView
from unittest.mock import Mock


@pytest.fixture(scope="module")
def app():
    return QApplication([])


def test_add_watchlist(app):
    """관심 종목 추가 테스트"""
    api_client = Mock()
    api_client.add_watchlist = Mock(return_value={"id": 1})
    
    view = WatchlistView(api_client)
    view.code_input.setText("005930")
    view.name_input.setText("삼성전자")
    view.add_watchlist()
    
    api_client.add_watchlist.assert_called_once_with(
        1, "005930", "삼성전자"
    )
```

### 테스트 실행

```powershell
# Backend 테스트
cd backend
pytest tests/ -v

# Trading Engine 테스트
cd trading-engine
pytest tests/ -v

# Frontend 테스트
cd frontend
pytest tests/ -v

# 커버리지 확인
pytest --cov=app tests/
```

---

## 디버깅

### 로거 사용

```python
from loguru import logger

# 일반 로그
logger.info("주문 생성: {}", order_id)
logger.warning("잔고 부족: {}", balance)
logger.error("API 오류: {}", error)

# 예외 로깅
try:
    risky_operation()
except Exception as e:
    logger.exception("예외 발생")  # 스택 트레이스 포함
```

### VS Code 디버깅

**launch.json:**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    },
    {
      "name": "Frontend",
      "type": "python",
      "request": "launch",
      "program": "main.py",
      "cwd": "${workspaceFolder}/frontend"
    },
    {
      "name": "Trading Engine",
      "type": "python",
      "request": "launch",
      "program": "engine/main.py",
      "cwd": "${workspaceFolder}/trading-engine"
    }
  ]
}
```

### 브레이크포인트

1. 코드 라인 번호 왼쪽 클릭
2. F5로 디버그 시작
3. F10: Step Over
4. F11: Step Into
5. Shift+F11: Step Out

---

## 기여 가이드

### Git 워크플로우

#### 1. 브랜치 생성

```powershell
# main에서 최신 코드 받기
git checkout main
git pull origin main

# 새 기능 브랜치 생성
git checkout -b feature/watchlist

# 버그 수정 브랜치
git checkout -b fix/order-bug
```

#### 2. 커밋

```powershell
# 변경 사항 확인
git status
git diff

# 스테이징
git add path/to/file

# 커밋
git commit -m "feat: 관심 종목 기능 추가"
```

**커밋 메시지 규칙:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `refactor`: 리팩토링
- `test`: 테스트 추가
- `chore`: 빌드 설정 등

#### 3. Pull Request

```powershell
# 원격 브랜치에 푸시
git push origin feature/watchlist

# GitHub에서 Pull Request 생성
# - 제목: 간결하고 명확하게
# - 설명: 무엇을, 왜, 어떻게 변경했는지
# - 스크린샷: UI 변경 시 포함
```

#### 4. 코드 리뷰

- 리뷰어 피드백 반영
- 테스트 통과 확인
- 승인 후 Merge

### 코드 리뷰 체크리스트

- [ ] 코드가 PEP 8을 준수하는가?
- [ ] 타입 힌트가 있는가?
- [ ] Docstring이 작성되었는가?
- [ ] 테스트가 포함되었는가?
- [ ] 로그가 적절히 추가되었는가?
- [ ] 에러 처리가 되어 있는가?
- [ ] 성능 이슈는 없는가?
- [ ] 보안 이슈는 없는가?

---

## 참고 자료

### 공식 문서
- [FastAPI](https://fastapi.tiangolo.com/)
- [PySide6](https://doc.qt.io/qtforpython-6/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [pytest](https://docs.pytest.org/)

### 내부 문서
- [API 문서](API.md)
- [아키텍처](ARCHITECTURE.md)
- [배포 가이드](DEPLOYMENT.md)
- [사용자 매뉴얼](USER_MANUAL.md)

---

**작성일**: 2025-10-24  
**버전**: 1.0  
**담당자**: CleonAI Development Team


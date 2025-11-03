# 키움 Open API 사용 현황 검토 보고서

**작성일**: 2025년 11월 2일  
**검토 대상**: CleonAI 자동매매 프로그램 v1.3  
**검토자**: AI Assistant

---

## 📋 검토 개요

본 문서는 CleonAI 자동매매 프로그램에서 키움 Open API를 사용하는 모든 기능을 조사하고, 키움 공식 문서(`C:\OpenAPI\koa_devguide.xml`)에 명시된 권장 사용법과 비교 검토한 결과를 정리합니다.

## 🔍 조사 결과

### 1. OpenAPI 참조 위치

#### 물리적 폴더
- **프로젝트 내**: `openapi` 폴더 없음 (별도 관리 불필요)
- **키움 설치 경로**: `C:\OpenAPI\`
  - 공식 개발 가이드: `koa_devguide.xml`
  - API 라이브러리: `khopenapi.ocx` (ActiveX 컨트롤)

#### 프로젝트 문서
- `auto_trading\docs\installation\KIWOOM_API_SETUP.md` - 설치 가이드
- `.cursorrules` - 개발 규칙 (OpenAPI 참조 규칙 추가됨)

### 2. OpenAPI 사용 현황

#### 핵심 파일: `kiwoom_api.py`

키움 Open API와 직접 통신하는 Python 래퍼 클래스

**사용 중인 TR 코드:**

| TR 코드 | 용도 | 위치 | 상태 |
|---------|------|------|------|
| OPW00001 | 예수금상세현황요청 (계좌 잔고 조회) | 라인 432-478 | ✅ 정상 |
| OPW00018 | 계좌평가잔고내역요청 (보유 종목 조회) | 라인 499-554 | ✅ 정상 |
| OPT10001 | 주식기본정보요청 (현재가 조회) | 라인 574-595 | ✅ 정상 |
| OPT10023 | 거래량상위요청 (거래대금 상위 종목) | 라인 626-655 | ✅ 정상 |

**사용 중인 OpenAPI 함수:**

| 함수명 | 용도 | 위치 | 문서 준수 |
|--------|------|------|----------|
| `CommConnect()` | 로그인 | 라인 155 | ✅ |
| `SetInputValue()` | TR 입력값 설정 | 라인 433-455, 502-522 등 | ✅ |
| `CommRqData()` | TR 조회 요청 | 라인 458-464, 525-531 등 | ✅ |
| `SendOrder()` | 주문 전송 (매수/매도) | 라인 738-741, 814-817 | ✅ |
| `SetRealReg()` | 실시간 시세 등록 | 라인 900-906 | ✅ |
| `GetCommData()` | TR 데이터 수신 | 라인 931-1033 | ✅ |
| `GetCommRealData()` | 실시간 데이터 수신 | 라인 1057-1087 | ✅ |
| `GetChejanData()` | 체결 데이터 수신 | 라인 1136-1140 | ✅ |
| `KOA_Functions()` | 계좌 비밀번호 등록창 표시 | 라인 211 | ✅ |

#### 의존 파일들

| 파일명 | 역할 | OpenAPI 사용 |
|--------|------|--------------|
| `main.py` | 프로그램 진입점 | KiwoomAPI 초기화 및 로그인 |
| `trading_engine.py` | 자동매매 엔진 | 실시간 데이터 수신, 매매 실행 |
| `surge_detector.py` | 급등주 감지 | 거래대금 상위 종목 조회 |
| `config.py` | 설정 관리 | API 제한 설정값 정의 |

---

## ✅ 문서 대비 사용법 검토

### 올바르게 구현된 부분

#### 1. API 호출 제한 준수 ⭐

**키움 공식 제한**:
- 초당 5건
- 일일 1,000건

**현재 구현** (`kiwoom_api.py` 라인 88-99, 296-340):
```python
# TR 조회: 초당 2건 (안전 마진 150%)
self.request_delay = 0.5  # 0.5초 간격
self.request_history = []  # 1초 내 요청 추적

# 주문: 초당 3건, 일일 100건
self.order_delay = 0.3  # 0.3초 간격
self.max_orders_per_day = 100
```

**평가**: ✅ 오히려 더 보수적으로 제한 (안전)

#### 2. 비동기 이벤트 처리

**키움 공식 권장**:
- COM 이벤트 기반 처리
- 비동기 응답 대기

**현재 구현** (라인 104-105, 133-139):
```python
# PyQt QEventLoop 사용
self.login_event_loop = QEventLoop()
self.request_event_loop = QEventLoop()

# 시그널 연결
self.ocx.OnEventConnect.connect(self._on_event_connect)
self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
self.ocx.OnReceiveRealData.connect(self._on_receive_real_data)
```

**평가**: ✅ 표준 이벤트 처리 방식 준수

#### 3. 계좌번호 처리

**키움 공식 명세**:
- 10자리 계좌번호 (HTS는 8자리 표시)
- 모의투자 계좌는 8로 시작

**현재 구현** (라인 162-188):
```python
accounts = account_list.split(';')[:-1]
if Config.USE_SIMULATION:
    sim_accounts = [acc for acc in accounts if acc.startswith('8')]
    self.account_number = sim_accounts[0]  # 10자리
```

**평가**: ✅ 올바른 계좌번호 처리

#### 4. TR 요청 흐름

**키움 공식 흐름**:
```
SetInputValue() → CommRqData() → OnReceiveTrData 이벤트 → GetCommData()
```

**현재 구현** (예: 잔고 조회, 라인 432-478):
```python
# 1. 입력값 설정
self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)

# 2. TR 요청
ret = self.ocx.dynamicCall("CommRqData(...)", "예수금상세현황요청", "OPW00001", ...)

# 3. 이벤트 대기
if ret == 0:
    self.request_event_loop.exec_()

# 4. 데이터 수신 (이벤트 핸들러에서)
def _on_receive_tr_data(...):
    cash = self.ocx.dynamicCall("GetCommData(...)", "예수금")
```

**평가**: ✅ 올바른 흐름 준수

#### 5. SendOrder 파라미터

**키움 공식 명세**:
```
LONG SendOrder(
  BSTR sRQName,        // 사용자 구분명
  BSTR sScreenNo,      // 화면번호
  BSTR sAccNo,         // 계좌번호 (10자리)
  LONG nOrderType,     // 주문유형 (1:신규매수, 2:신규매도, ...)
  BSTR sCode,          // 종목코드
  LONG nQty,           // 주문수량
  LONG nPrice,         // 주문가격
  BSTR sHogaGb,        // 거래구분 (00:지정가, 03:시장가, ...)
  BSTR sOrgOrderNo     // 원주문번호 (신규주문시 공백)
)
```

**현재 구현** (라인 738-741):
```python
ret = self.ocx.dynamicCall(
    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
    ["매수", "0101", self.account_number, 1, stock_code, quantity, price, order_type, ""]
)
```

**평가**: ✅ 파라미터 순서 및 값 올바름

#### 6. 실시간 시세 등록

**키움 공식 명세**:
- 한 번에 최대 100종목
- FID 목록으로 원하는 데이터 지정

**현재 구현** (라인 900-906):
```python
# 배치 분할 등록 (50개씩)
batch_size = 50
fids = "9001;10;11;12;13;27;28;121;125;228"  # 현재가, 등락률, 거래량 등
ret = self.ocx.dynamicCall("SetRealReg(...)", screen_no, code_list, fids, "0")
```

**평가**: ✅ 과부하 방지 배치 처리 구현

#### 7. 에러 처리

**현재 구현**:
- SendOrder 에러 코드 정의 (라인 41-59) ✅
- TR 조회 실패 시 재시도 로직 (라인 614-699, 최대 3회) ✅
- 반환값 체크 및 로깅 ✅

**평가**: ✅ 충분한 에러 처리

---

## ⚠️ 개선 권장 사항

### 1. 비밀번호 처리 (현재는 문제 없음)

**현재 구현**:
- `.env` 파일에서 비밀번호 읽기
- 모의투자는 비밀번호 필드 생략 (라인 440-450) ✅
- 로그인 시 `ShowAccountWindow` 자동 표시 (라인 211) ✅

**키움 권장**:
- 계좌 비밀번호 등록창에서 한 번 등록 후 AUTO 체크
- 이후 자동 로그인

**평가**: ✅ 이미 올바르게 구현됨 (개선 불필요)

### 2. 화면번호 관리

**현재 구현**:
- 하드코딩된 화면번호 사용 ("2000", "2001", "2002", ...)

**권장**:
- 화면번호 충돌 방지를 위해 중앙 관리 권장
- 현재는 화면번호가 충분히 분리되어 있어 문제 없음

**평가**: ⚠️ 현재는 문제 없으나, 향후 TR 추가 시 주의 필요

---

## 📊 종합 평가

### 검토 결과 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| API 호출 제한 준수 | ✅ 우수 | 안전 마진 적용 |
| 비동기 이벤트 처리 | ✅ 우수 | PyQt 표준 방식 |
| 계좌번호 처리 | ✅ 정상 | 10자리 올바름 |
| TR 요청 흐름 | ✅ 정상 | 표준 흐름 준수 |
| SendOrder 파라미터 | ✅ 정상 | 명세 준수 |
| 에러 처리 | ✅ 우수 | 재시도 로직 포함 |
| 실시간 시세 등록 | ✅ 우수 | 배치 처리 구현 |
| 비밀번호 처리 | ✅ 정상 | 권장 방식 사용 |
| 화면번호 관리 | ⚠️ 주의 | 현재는 문제 없음 |

### 전체 평가

**✅ 프로젝트는 키움 Open API를 올바르게 사용하고 있으며, 추가 수정은 불필요합니다.**

현재 구현은 키움 Open API 공식 문서의 권장 사항을 잘 따르고 있으며, 일부 영역(API 제한, 배치 처리)에서는 오히려 더 보수적이고 안전한 방식을 채택하고 있습니다.

---

## 📚 참고 문서

### 키움 공식 문서
- `C:\OpenAPI\koa_devguide.xml` - 전체 API 명세
- KOA Studio - TR 조회 및 테스트 도구

### 프로젝트 문서
- `auto_trading\docs\installation\KIWOOM_API_SETUP.md` - 설치 가이드
- `.cursorrules` - 개발 규칙 (OpenAPI 참조 규칙 포함)
- `kiwoom_api.py` - API 래퍼 구현 (Docstring 포함)

---

## 🔄 프로젝트 룰 업데이트

**업데이트 내용**: `.cursorrules` 파일에 "OpenAPI 참조 (필수)" 섹션 추가

**추가된 내용**:
1. 공식 문서 위치 명시
2. 프로그램 수정 시 필수 확인 사항 5가지
3. 현재 사용 중인 TR 코드 목록
4. API 함수 사용 패턴 예제

**목적**: 향후 프로그램 수정 시 키움 Open API 공식 문서를 참조하도록 가이드

---

## ✅ 결론

CleonAI 자동매매 프로그램은 키움 Open API를 **올바르게** 사용하고 있으며, 공식 문서의 권장 사항을 충실히 준수하고 있습니다. 추가 코드 수정은 불필요하며, 프로젝트 룰에 OpenAPI 참조 규칙을 추가하여 향후 개발 시 가이드로 활용할 수 있도록 문서화를 완료했습니다.

**검토 완료일**: 2025년 11월 2일


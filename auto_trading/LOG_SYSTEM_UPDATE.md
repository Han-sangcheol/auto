# 로그 시스템 업데이트 (날짜별 파일 생성)

**날짜**: 2025-10-26  
**업데이트**: 로그 파일 날짜별 자동 생성 기능 추가

## 🎯 개선 사항

### 이전 (단일 파일)
```
logs/
├── trading.log         # 모든 날짜의 로그가 하나의 파일에
├── error.log           # 모든 날짜의 에러가 하나의 파일에
└── trading.log.zip     # 압축된 오래된 로그
```

**문제점**:
- ❌ 특정 날짜의 로그 찾기 어려움
- ❌ 파일이 계속 커짐
- ❌ 분석이 불편함

### 현재 (날짜별 파일)
```
logs/
├── trading_2025-10-26.log      # 오늘의 거래 로그
├── trading_2025-10-25.log      # 어제의 거래 로그
├── trading_2025-10-24.log      # 그저께의 거래 로그
├── error_2025-10-26.log        # 오늘의 에러 로그
├── error_2025-10-25.log        # 어제의 에러 로그
├── trading.log                 # 최신 로그 (호환성)
├── error.log                   # 최신 에러 (호환성)
└── trading_2025-09-26.log.zip  # 30일 이전 로그는 압축
```

**장점**:
- ✅ 날짜별로 파일 자동 생성
- ✅ 특정 날짜의 로그 즉시 확인
- ✅ 파일 크기 관리 용이
- ✅ 분석 및 백업 편리
- ✅ 이전 방식과 호환 (trading.log, error.log 유지)

## 📝 파일 명명 규칙

### 날짜별 로그 파일
```
trading_YYYY-MM-DD.log      # 예: trading_2025-10-26.log
error_YYYY-MM-DD.log        # 예: error_2025-10-26.log
```

### 호환성 유지 파일
```
trading.log                 # 최신 로그 (실시간 확인용)
error.log                   # 최신 에러 (실시간 확인용)
```

## 🔄 자동 로테이션

### 날짜별 파일
- **생성**: 매일 자정(00:00)에 새 파일 자동 생성
- **보관**: 30일간 보관 (거래 로그), 60일간 보관 (에러 로그)
- **압축**: 30일 이후 자동 압축 (.zip)
- **삭제**: 보관 기간 초과 시 자동 삭제

### 최신 로그 파일
- **용도**: 실시간 모니터링용
- **보관**: 7일간만 유지
- **압축**: 없음 (빠른 접근)

## 📊 사용 예시

### 특정 날짜 로그 확인
```powershell
# 오늘의 로그 확인
Get-Content logs\trading_2025-10-26.log -Tail 50

# 어제의 로그 확인
Get-Content logs\trading_2025-10-25.log

# 실시간 로그 모니터링
Get-Content logs\trading.log -Wait -Tail 20
```

### 날짜 범위 로그 검색
```powershell
# 10월 모든 로그에서 "매수" 검색
Get-ChildItem logs\trading_2025-10-*.log | Select-String "매수"

# 최근 3일 에러 확인
Get-ChildItem logs\error_2025-10-*.log | Select-Object -Last 3 | Get-Content
```

### 로그 백업
```powershell
# 특정 월 로그 백업
Copy-Item logs\trading_2025-10-*.log D:\backup\logs\

# 전체 로그 백업 (zip 포함)
Copy-Item logs\* D:\backup\logs\ -Recurse
```

## 🔍 로그 파일 구조

### 날짜별 거래 로그 (trading_YYYY-MM-DD.log)
```
2025-10-26 09:05:32 | INFO     | trading_engine:start_trading:169 | 🚀 자동매매 시작!
2025-10-26 09:05:32 | INFO     | trading_engine:start_trading:170 | 관심 종목: 005930, 000660
2025-10-26 09:10:15 | SUCCESS  | trading_engine:execute_buy:379 | ✅ 매수 완료: 005930 10주
2025-10-26 14:30:22 | SUCCESS  | trading_engine:execute_sell:432 | ✅ 매도 완료: 005930 10주
```

### 날짜별 에러 로그 (error_YYYY-MM-DD.log)
```
2025-10-26 09:05:35 | ERROR    | kiwoom_api:get_balance:191 | 잔고 조회 실패: -202
2025-10-26 09:05:36 | ERROR    | kiwoom_api:get_holdings:246 | 보유종목 조회 실패: -202
```

## 🛠️ 설정 변경

### 보관 기간 변경
`logger.py` 파일 수정:

```python
# 날짜별 거래 로그
logger.add(
    daily_log_path,
    retention="30 days",   # 여기를 수정 (예: "60 days")
    ...
)

# 날짜별 에러 로그
logger.add(
    daily_error_log_path,
    retention="60 days",   # 여기를 수정 (예: "90 days")
    ...
)
```

### 압축 해제
압축을 원하지 않는 경우:
```python
logger.add(
    daily_log_path,
    compression=None,      # zip 대신 None
    ...
)
```

### 파일명 형식 변경
```python
# 현재: trading_2025-10-26.log
today = datetime.now().strftime("%Y-%m-%d")

# 변경 예시: trading_20251026.log
today = datetime.now().strftime("%Y%m%d")

# 변경 예시: trading_2025_10_26.log
today = datetime.now().strftime("%Y_%m_%d")
```

## 📈 디스크 공간 관리

### 예상 파일 크기
- **거래 로그**: 약 1-5 MB/일 (활동량에 따라)
- **에러 로그**: 약 100 KB/일
- **압축 후**: 약 10-20% 크기로 축소

### 30일 보관 시 예상 용량
- 날짜별 로그: 30 × 5 MB = 150 MB
- 압축 로그: 30 × 1 MB = 30 MB
- **총 예상**: 약 180 MB

### 자동 정리
- Loguru가 자동으로 오래된 파일 삭제
- 보관 기간 초과 시 자동 삭제
- 수동 정리 불필요

## 🔧 문제 해결

### 로그 파일이 생성되지 않음
**확인 사항**:
1. `logs/` 폴더 존재 여부
2. 쓰기 권한 확인
3. 디스크 공간 확인

**해결 방법**:
```powershell
# 로그 폴더 생성
New-Item -ItemType Directory -Path logs -Force

# 권한 확인
icacls logs
```

### 이전 로그 파일 (trading.log) 찾기
**위치**:
- 날짜별 파일로 변경되었지만, `trading.log`는 계속 생성됨
- 최신 로그는 `trading.log`에서 실시간 확인 가능
- 과거 로그는 `trading_YYYY-MM-DD.log`에서 확인

### 특정 날짜 로그가 없음
**원인**:
- 해당 날짜에 프로그램을 실행하지 않음
- 보관 기간 초과로 삭제됨
- 압축된 파일 확인 (`trading_YYYY-MM-DD.log.zip`)

## 📚 로그 분석 팁

### 1. 성공/실패 통계
```powershell
# 오늘의 매수 건수
(Get-Content logs\trading_2025-10-26.log | Select-String "매수 완료").Count

# 오늘의 에러 건수
(Get-Content logs\error_2025-10-26.log).Count
```

### 2. 특정 종목 추적
```powershell
# 삼성전자(005930) 관련 로그
Get-Content logs\trading_2025-10-26.log | Select-String "005930"
```

### 3. 시간대별 활동
```powershell
# 오전 9시대 로그만
Get-Content logs\trading_2025-10-26.log | Select-String "09:"
```

### 4. 수익/손실 계산
```powershell
# 매도 완료 로그에서 손익 추출
Get-Content logs\trading_2025-10-26.log | Select-String "매도 완료"
```

## 🚀 권장 사항

### 일일 체크리스트
- [ ] 전날 로그 백업 (선택)
- [ ] 에러 로그 확인
- [ ] 거래 통계 확인
- [ ] 이상 패턴 확인

### 주간 체크리스트
- [ ] 주간 로그 백업
- [ ] 디스크 공간 확인
- [ ] 오래된 로그 정리 확인
- [ ] 압축 파일 백업

### 월간 체크리스트
- [ ] 월간 로그 아카이브
- [ ] 통계 분석
- [ ] 전략 성과 평가

## 📝 마이그레이션

### 기존 로그 변환
기존 `trading.log`가 있는 경우:

```powershell
# 이전 로그를 날짜별로 분리 (수동)
# 1. 이전 로그 백업
Copy-Item logs\trading.log logs\trading_backup.log

# 2. 새 버전 실행 (자동으로 날짜별 파일 생성)
python main.py

# 3. 이전 로그는 참고용으로 보관 (선택)
```

## 🎉 결론

이제 로그 관리가 훨씬 편리합니다!

**주요 개선:**
- ✅ 날짜별 자동 파일 생성
- ✅ 파일명만으로 날짜 식별
- ✅ 자동 압축 및 정리
- ✅ 이전 방식과 호환

**다음 실행부터 자동 적용**:
- 새로운 로그 시스템이 자동으로 작동
- 별도 설정 불필요
- 기존 로그는 그대로 유지

---

**작성**: CleonAI 개발팀  
**버전**: 1.1  
**업데이트**: 2025-10-26


# 빠른 시작 가이드

이미 모든 설정을 완료한 사용자를 위한 빠른 실행 가이드입니다.

> **처음 사용하시나요?** [GETTING_STARTED.md](GETTING_STARTED.md)를 먼저 읽어주세요.

## 사전 준비 확인

다음 항목이 모두 완료되어 있어야 합니다:

- [x] Python 3.11 이상 설치
- [x] 키움 Open API+ 설치
- [x] 공동인증서 준비
- [x] 모의투자 또는 실계좌
- [x] 프로그램 설치 완료 (`setup.ps1` 또는 `setup.bat` 실행)
- [x] `.env` 파일 설정 완료

## 3단계 빠른 시작

### 1단계: 설정 확인 (30초)

`.env` 파일을 열어서 다음을 확인하세요:

```env
KIWOOM_ACCOUNT_NUMBER=8123456789    # 계좌번호
KIWOOM_ACCOUNT_PASSWORD=1234        # 계좌 비밀번호
WATCH_LIST=005930,000660,035720     # 관심 종목
USE_SIMULATION=True                 # 모의투자 여부
```

### 2단계: 프로그램 실행 (1분)

`auto_trading` 폴더에서:

**PowerShell (권장):**
```
start.ps1
```

**CMD:**
```
start.bat
```

파일을 더블클릭하거나 우클릭하여 실행합니다.

> **PowerShell 실행 정책 오류 시:**
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3단계: 로그인 및 시작 (1분)

1. **공동인증서 선택**
   - 공동인증서 창이 나타나면 본인 인증서 선택
   
2. **비밀번호 입력**
   - 공동인증서 비밀번호 입력

3. **로그인 완료 확인**
   ```
   ✅ 로그인 성공!
   ✅ 엔진 초기화 완료!
   ```

4. **자동매매 시작**
   - Enter 키를 눌러 자동매매 시작

## 완료!

프로그램이 실행 중입니다.

```
[2025-10-21 09:15:23] 실시간 시세 수신: 삼성전자 75,000원
[2025-10-21 09:15:24] 매매 신호 분석 중...
```

## 중지 방법

**Ctrl + C** 를 눌러 언제든지 중지할 수 있습니다.

## 로그 확인

```bash
# 일반 로그
type logs\trading.log

# 에러 로그
type logs\error.log
```

## 문제 발생 시

### 로그인 실패
→ KOA Studio로 로그인 테스트

### 설정 오류
→ `.env` 파일의 필수 항목 확인

### 매매가 실행되지 않음
→ 로그 파일 확인 (`logs/trading.log`)

### 자세한 도움말
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 참고

## 일일 체크리스트

매일 다음을 확인하세요:

- [ ] 프로그램 실행 상태
- [ ] 에러 로그 확인
- [ ] 계좌 잔고 확인
- [ ] 거래 내역 확인

## 다음 단계

- **전략 조정**: [STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)
- **설정 변경**: `.env` 파일 수정
- **성과 분석**: 로그 파일 분석

---

**버전**: 1.0.0  
**최종 업데이트**: 2025년 10월 21일

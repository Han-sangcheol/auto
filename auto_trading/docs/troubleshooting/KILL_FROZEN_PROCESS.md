# 응답없는 프로그램 종료 가이드

**상황**: 프로그램이 응답없음 상태일 때 안전하게 종료하는 방법

## 🚨 현재 상황

프로그램이 응답없음 상태이면 다음과 같은 증상이 나타납니다:
- 창이 움직이지 않음
- 마우스 클릭 반응 없음
- 작업 관리자에서 "응답 없음" 표시
- Ctrl+C가 작동하지 않음

## 🔧 해결 방법

### 방법 1: 작업 관리자 (권장)

**단계**:
1. `Ctrl + Shift + Esc` 키를 눌러 작업 관리자 열기
2. "프로세스" 탭에서 `python.exe` 또는 `python3.13.exe` 찾기
3. 해당 프로세스 선택 후 "작업 끝내기" 클릭
4. 모든 Python 프로세스 확인 후 응답없는 것들 모두 종료

### 방법 2: PowerShell 명령 (빠름)

```powershell
# 현재 실행 중인 Python 프로세스 확인
tasklist | findstr python

# 모든 Python 프로세스 종료
taskkill /F /IM python.exe
taskkill /F /IM python3.13.exe

# 또는 특정 PID로 종료
taskkill /F /PID 18244
taskkill /F /PID 25212
taskkill /F /PID 23932
taskkill /F /PID 59784
```

**옵션 설명**:
- `/F`: 강제 종료 (Force)
- `/IM`: 이미지 이름 (프로세스 이름)
- `/PID`: 프로세스 ID

### 방법 3: CMD 명령

```cmd
REM 현재 실행 중인 Python 프로세스 확인
tasklist | findstr python

REM 모든 Python 프로세스 종료
taskkill /F /IM python.exe
taskkill /F /IM python3.13.exe
```

## ⚠️ 주의 사항

### 종료 전 확인
- [ ] 다른 중요한 Python 프로그램이 실행 중이지 않은지 확인
- [ ] 저장되지 않은 작업이 없는지 확인
- [ ] 로그 파일은 자동으로 저장되므로 걱정 안 해도 됨

### 종료 후 확인
```powershell
# Python 프로세스가 모두 종료되었는지 확인
tasklist | findstr python

# 아무것도 출력되지 않으면 정상 종료됨
```

## 🔄 재시작

프로그램을 종료한 후 최신 버전으로 다시 시작:

```powershell
# 1. 자동매매 폴더로 이동
cd auto_trading

# 2. 최신 버전으로 업데이트 (선택)
git pull origin main

# 3. 프로그램 재시작
.\start.ps1
# 또는
python main.py
```

## 📊 현재 실행 중인 프로세스 확인

### 상세 정보 확인
```powershell
# 프로세스 이름, PID, 메모리 사용량
Get-Process python* | Format-Table Id, ProcessName, WorkingSet -AutoSize

# 프로세스 시작 시간 확인
Get-Process python* | Select-Object Id, ProcessName, StartTime

# 응답하지 않는 프로세스 확인
Get-Process python* | Where-Object {$_.Responding -eq $false}
```

### 특정 포트 사용 중인 프로세스 확인
```powershell
# 예: 8000 포트 사용 중인 프로세스
netstat -ano | findstr :8000
```

## 🛡️ 안전한 종료

### 정상 종료 시도 (권장)
```powershell
# 먼저 정상 종료 시도
Stop-Process -Name python -ErrorAction SilentlyContinue

# 5초 대기
Start-Sleep -Seconds 5

# 아직 실행 중이면 강제 종료
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force
```

### 배치 스크립트로 자동화
파일: `kill_frozen.bat`
```batch
@echo off
echo 응답없는 Python 프로세스를 종료합니다...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM python3.13.exe 2>nul
echo 완료!
pause
```

실행:
```cmd
kill_frozen.bat
```

## 📝 로그 확인

종료 후 무엇이 문제였는지 확인:

```powershell
# 최근 에러 로그 확인
Get-Content logs\error_2025-10-26.log -Tail 50

# 최근 거래 로그 확인
Get-Content logs\trading_2025-10-26.log -Tail 50

# "응답없음" 또는 "블로킹" 관련 로그 검색
Get-Content logs\trading_*.log | Select-String "error|timeout|blocking"
```

## 🚀 예방 조치

### 최신 버전 사용
**v1.0 (2025-10-26) 이상**은 GUI 응답없음 문제가 해결되었습니다.

**확인 방법**:
```powershell
# 프로그램 실행 시 다음 메시지 확인
# ✅ QTimer 기반 모니터링 시작 (5초 간격)
# 📡 PyQt 이벤트 루프 실행 중... (GUI 응답 유지)
```

이 메시지가 보이면 최신 버전입니다!

### 자동 재시작 스크립트 (선택)
파일: `auto_restart.ps1`
```powershell
# 프로그램 실행
Start-Process python -ArgumentList "main.py" -WorkingDirectory "D:\cleonAI\auto_trading"

# 2시간마다 재시작 (구 버전용)
while ($true) {
    Start-Sleep -Seconds 7200  # 2시간
    
    # 응답없는 프로세스 확인
    $frozen = Get-Process python* | Where-Object {$_.Responding -eq $false}
    
    if ($frozen) {
        Write-Host "응답없는 프로세스 감지, 재시작..."
        Stop-Process -Name python -Force
        Start-Sleep -Seconds 5
        Start-Process python -ArgumentList "main.py" -WorkingDirectory "D:\cleonAI\auto_trading"
    }
}
```

**참고**: 최신 버전(v1.0)은 재시작 불필요!

## 🔍 문제 진단

### 왜 응답없음이 발생했나요?

**구 버전 (v0.x)**:
- 블로킹 `while` 루프가 GUI 스레드를 차단
- `time.sleep()`으로 인한 멈춤
- PyQt 이벤트 루프 동작 중단

**최신 버전 (v1.0+)**:
- ✅ QTimer 기반 논블로킹 방식
- ✅ GUI 항상 응답
- ✅ 장시간 안정 실행

**상세 정보**: [GUI_FREEZE_FIX.md](GUI_FREEZE_FIX.md)

## 📞 추가 도움말

### 프로세스가 종료되지 않을 때

```powershell
# 시스템 권한으로 강제 종료
Start-Process powershell -Verb RunAs -ArgumentList "taskkill /F /IM python.exe"
```

### 포트가 계속 사용 중일 때

```powershell
# 포트 8000 사용 중인 프로세스 종료
$port = netstat -ano | findstr :8000
$pid = $port.Split()[-1]
taskkill /F /PID $pid
```

## ✅ 체크리스트

응답없는 프로그램 종료 후:

- [ ] 모든 Python 프로세스 종료 확인
- [ ] 에러 로그 확인
- [ ] 최신 버전으로 업데이트
- [ ] 프로그램 재시작
- [ ] 로그에서 "QTimer 기반 모니터링" 메시지 확인

## 🎉 최신 버전의 장점

**v1.0 (2025-10-26) 이상**:
- ✅ 응답없음 문제 완전 해결
- ✅ 강제 종료 불필요
- ✅ Ctrl+C 정상 동작
- ✅ 안정적 장시간 실행

**지금 업데이트하세요!**
```powershell
cd D:\cleonAI\auto_trading
git pull origin main
```

---

**작성**: CleonAI 개발팀  
**버전**: 1.0  
**업데이트**: 2025-10-26



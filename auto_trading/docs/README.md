# CleonAI 자동매매 프로그램 문서

키움증권 Open API 기반 독립 실행형 자동매매 프로그램의 모든 문서를 한곳에서 확인하세요.

## 📚 문서 카테고리

### 🚀 설치 (처음 사용자 필수)

| 문서 | 설명 | 소요 시간 |
|------|------|----------|
| [빠른 설치](installation/QUICK_INSTALL.md) | 원클릭 자동 설치 | 5분 |
| [완전 설치 가이드](installation/GETTING_STARTED.md) | 처음부터 끝까지 완전한 설치 | 30-40분 |
| [Python 32비트 설치](installation/SETUP_ISOLATED_PYTHON.md) | 키움 API를 위한 Python 설정 | 10분 |
| [키움 API 설정](installation/KIWOOM_API_SETUP.md) | Open API+ 신청 및 모의투자 계좌 | 20분 |

### 📖 사용 가이드

| 문서 | 설명 |
|------|------|
| [빠른 시작](guides/QUICKSTART.md) | 5분 빠른 시작 (설정 완료 후) |
| [매매 전략](guides/STRATEGY_GUIDE.md) | 전략 설명 및 파라미터 조정 |
| [데이터 시각화](guides/VISUALIZATION_GUIDE.md) | Excel, Grafana, 백테스팅 |
| [스케줄러](guides/SCHEDULER_GUIDE.md) | 자동 실행 설정 |
| [통합 가이드](guides/INTEGRATION_GUIDE.md) | 외부 시스템 연동 |
| [실행 가이드](guides/START_GUIDE.md) | 프로그램 실행 방법 |
| [스크립트 설명](guides/README_SCRIPTS.md) | 설치/실행 스크립트 설명 |

### 🔧 문제 해결

| 문서 | 설명 |
|------|------|
| [FAQ](troubleshooting/FAQ.md) | 자주 묻는 질문 |
| [트러블슈팅](troubleshooting/TROUBLESHOOTING.md) | 일반적인 문제 해결 |
| [실행 문제 해결](troubleshooting/START_TROUBLESHOOTING.md) | 실행 관련 문제 |
| [프로세스 종료](troubleshooting/KILL_FROZEN_PROCESS.md) | 응답없음 해결 |
| [GUI 프리즈 수정](troubleshooting/GUI_FREEZE_FIX.md) | GUI 응답없음 문제 |

### 📊 구현 진행

| 문서 | 설명 |
|------|------|
| [구현 로드맵](implementation/IMPLEMENTATION_ROADMAP.md) | 전체 개발 계획 |
| [구현 진행도](implementation/IMPLEMENTATION_PROGRESS.md) | 현재 개발 상태 |
| [프로젝트 완료](implementation/PROJECT_COMPLETE.md) | 프로젝트 완료 보고 |
| [Phase 1-3 완료](implementation/PHASE_1_TO_3_COMPLETE.md) | 기본 기능 완료 |
| [Phase 1 완료](implementation/PHASE1_COMPLETE.md) | 초기 설정 |
| [Phase 2 완료](implementation/PHASE2_COMPLETE.md) | 매매 전략 |
| [Phase 3 완료](implementation/PHASE3_AUTOMATION_COMPLETE.md) | 자동화 |
| [Phase 4 완료](implementation/PHASE4_COMPLETE.md) | 급등주 감지 |
| [Phase 4 에러 복구](implementation/PHASE4_ERROR_RECOVERY_COMPLETE.md) | 에러 처리 |
| [과부하 방지](implementation/OVERLOAD_PREVENTION.md) | API 제한 관리 |
| [실행 상태 체크](implementation/EXECUTION_STATUS_CHECK.md) | 정상 실행 확인 |

---

## 🗂️ 날짜별 변경 로그 (아카이브)

완료된 버그 수정 및 기능 개선 기록입니다.

### 2025-10-26

- [로깅 강화](archive/2025-10-26/ENHANCED_LOGGING_2025-10-26.md)
- [업데이트 요약](archive/2025-10-26/UPDATE_SUMMARY_2025-10-26.md)
- [로그 시스템 업데이트](archive/2025-10-26/LOG_SYSTEM_UPDATE.md)

### 2025-10-27

- [자동 승인 업데이트](archive/2025-10-27/AUTO_APPROVAL_UPDATE_2025-10-27.md)
- [Ctrl+C 종료 수정](archive/2025-10-27/CTRL_C_FIX_2025-10-27.md)
- [단타 매매 업데이트](archive/2025-10-27/DAYTRADING_UPDATE_2025-10-27.md)
- [단타 실시간 모니터](archive/2025-10-27/DAYTRADING_REALTIME_MONITOR.md)
- [즉시 매수 수정](archive/2025-10-27/IMMEDIATE_BUY_FIX_2025-10-27.md)
- [과부하 수정](archive/2025-10-27/OVERLOAD_FIX_2025-10-27.md)
- [start.bat 가이드](archive/2025-10-27/START_BAT_GUIDE.md)

### 2025-10-28

- [블로킹 수정](archive/2025-10-28/BLOCKING_FIX_2025-10-28.md)
- [콜백 파라미터 수정](archive/2025-10-28/CALLBACK_PARAMETER_FIX_2025-10-28.md)
- [GUI 통합](archive/2025-10-28/GUI_INTEGRATION_2025-10-28.md)
- [GUI 데이터 수정](archive/2025-10-28/GUI_NO_DATA_FIX_2025-10-28.md)
- [인덴트 수정](archive/2025-10-28/INDENT_FIX_2025-10-28.md)
- [미체결 분석](archive/2025-10-28/NO_TRADE_ANALYSIS_2025-10-28.md)
- [호가 분석](archive/2025-10-28/ORDERBOOK_ANALYSIS_2025-10-28.md)
- [과부하 수정](archive/2025-10-28/OVERLOAD_FIX_2025-10-28.md)
- [급등주 매수 수정](archive/2025-10-28/SURGE_BUY_FIX_2025-10-28.md)

---

## 🎯 시작 경로 추천

### 처음 사용하는 경우

1. [빠른 설치](installation/QUICK_INSTALL.md) ⭐ **가장 쉬움**
2. 또는 [완전 설치 가이드](installation/GETTING_STARTED.md) (상세)
3. [빠른 시작](guides/QUICKSTART.md)
4. [매매 전략](guides/STRATEGY_GUIDE.md)

### 문제가 발생한 경우

1. [FAQ](troubleshooting/FAQ.md)
2. [트러블슈팅](troubleshooting/TROUBLESHOOTING.md)
3. [실행 문제 해결](troubleshooting/START_TROUBLESHOOTING.md)

### 고급 사용

1. [데이터 시각화](guides/VISUALIZATION_GUIDE.md) - Excel, Grafana, 백테스팅
2. [스케줄러](guides/SCHEDULER_GUIDE.md) - 자동 실행
3. [통합 가이드](guides/INTEGRATION_GUIDE.md) - 외부 연동

---

## 📁 문서 구조

```
docs/
├── README.md                          # 이 문서
├── installation/                      # 설치 관련 (4개)
├── guides/                            # 사용 가이드 (7개)
├── troubleshooting/                   # 문제 해결 (5개)
├── implementation/                    # 구현 진행 (11개)
└── archive/                           # 변경 로그 (날짜별)
    ├── 2025-10-26/                    # 3개
    ├── 2025-10-27/                    # 7개
    └── 2025-10-28/                    # 9개
```

---

## 💡 도움이 필요하신가요?

1. **설치**: [빠른 설치](installation/QUICK_INSTALL.md) 또는 [완전 가이드](installation/GETTING_STARTED.md)
2. **사용**: [빠른 시작](guides/QUICKSTART.md) 또는 [전략 가이드](guides/STRATEGY_GUIDE.md)
3. **문제**: [FAQ](troubleshooting/FAQ.md) 또는 [트러블슈팅](troubleshooting/TROUBLESHOOTING.md)

---

**프로젝트**: CleonAI 자동매매 프로그램  
**버전**: 1.1.0  
**최종 업데이트**: 2025년 10월 28일


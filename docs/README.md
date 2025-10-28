# CleonAI 문서 가이드

엔터프라이즈 자동매매 플랫폼의 모든 문서를 한곳에서 확인하세요.

## 빠른 네비게이션

### 처음 시작하는 경우

1. [빠른 시작 (간단)](user/QUICKSTART_SIMPLE.md) - 5분 안에 시작하기
2. [빠른 시작 (상세)](user/QUICK_START.md) - 단계별 안내
3. [사용자 매뉴얼](user/USER_MANUAL.md) - 전체 기능 설명

### 개발자

1. [API 문서](developer/API.md) - REST API 참조
2. [개발자 가이드](developer/DEVELOPER_GUIDE.md) - 개발 환경 설정
3. [배포 가이드](developer/DEPLOYMENT.md) - 프로덕션 배포 방법

### 아키텍처

1. [시스템 아키텍처](architecture/ARCHITECTURE.md) - 전체 시스템 구조

### 프로젝트 진행 상황

1. [구현 상태](implementation/IMPLEMENTATION_STATUS.md) - 현재 개발 진행도

---

## 📁 문서 구조

```
docs/
├── README.md                      # 이 문서 (문서 인덱스)
├── architecture/                  # 아키텍처 문서
│   └── ARCHITECTURE.md
├── user/                          # 사용자 문서
│   ├── USER_MANUAL.md
│   ├── QUICK_START.md
│   └── QUICKSTART_SIMPLE.md
├── developer/                     # 개발자 문서
│   ├── DEVELOPER_GUIDE.md
│   ├── API.md
│   └── DEPLOYMENT.md
├── implementation/                # 구현 진행 문서
│   └── IMPLEMENTATION_STATUS.md
└── archive/                       # 완료된 개발 문서 (참고용)
    ├── phases/                    # Phase별 완료 문서
    ├── progress/                  # 진행 중 스냅샷
    ├── summaries/                 # 요약 문서
    └── fixes/                     # 수정 기록
```

---

## 📚 주제별 문서

### 사용자

- **[빠른 시작 (간단)](user/QUICKSTART_SIMPLE.md)**: 3단계로 시작
- **[빠른 시작 (상세)](user/QUICK_START.md)**: 단계별 상세 가이드
- **[사용자 매뉴얼](user/USER_MANUAL.md)**: 화면별 사용법

### 개발자

- **[API 문서](developer/API.md)**: REST API 전체 참조
- **[개발자 가이드](developer/DEVELOPER_GUIDE.md)**: 개발 환경 구성
- **[배포 가이드](developer/DEPLOYMENT.md)**: 프로덕션 배포

### 아키텍처

- **[시스템 아키텍처](architecture/ARCHITECTURE.md)**: 시스템 설계 및 구조

### 프로젝트 관리

- **[구현 상태](implementation/IMPLEMENTATION_STATUS.md)**: 개발 진행도

---

## 🗂️ 아카이브

완료된 개발 Phase 문서들은 [archive](archive/) 폴더에서 확인할 수 있습니다.

- **[phases](archive/phases/)**: Phase 1-6 완료 문서
- **[progress](archive/progress/)**: 개발 진행 중 스냅샷
- **[summaries](archive/summaries/)**: Phase별 요약
- **[fixes](archive/fixes/)**: 주요 수정 기록

---

## 🔗 관련 프로젝트

### auto_trading (독립 프로젝트)

키움 API 기반 독립 실행형 자동매매 프로그램입니다.

- **위치**: `../auto_trading/`
- **문서**: [auto_trading/README.md](../auto_trading/README.md)
- **상세 문서**: [auto_trading/docs/](../auto_trading/docs/)

---

## 💡 도움이 필요하신가요?

1. **사용 방법**: [사용자 매뉴얼](user/USER_MANUAL.md) 참조
2. **개발 방법**: [개발자 가이드](developer/DEVELOPER_GUIDE.md) 참조
3. **API 사용**: [API 문서](developer/API.md) 참조

---

**버전**: 1.0.0  
**최종 업데이트**: 2025년 10월 28일


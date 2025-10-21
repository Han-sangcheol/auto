# 🔌 증권사 Open API 분석 및 비교

## 📋 개요
자동매매 프로그램 개발을 위한 주요 증권사들의 Open API를 분석하고 비교한 문서입니다.

## 🏦 주요 증권사 API 현황

### 1. 키움증권 Open API+
**⭐ 개인투자자에게 가장 널리 사용되는 API**

#### 장점
- ✅ **개인투자자 무료 제공** (조건부)
- ✅ 실시간 시세 데이터 제공
- ✅ 자동매매 기능 완벽 지원
- ✅ 풍부한 개발자 문서 및 커뮤니티
- ✅ Python, C++, C# 등 다양한 언어 지원

#### 제약사항
- ❌ Windows 환경에서만 동작 (COM 기반)
- ❌ 하루 조회 한도 제한 (일반: 1,000건/일)
- ❌ 동시 접속 제한 (계좌당 1개 프로세스)
- ❌ 모바일 네이티브 개발 불가 (Windows DLL 의존)

#### 기술 스펙
```
- 프로토콜: COM/ActiveX
- 실시간: 이벤트 기반
- 데이터: TR(Transaction) 방식
- 인증: 공동인증서 필요
- 비용: 무료 (월 수수료 조건 충족 시)
```

### 2. 한국투자증권 KIS Developers API
**🆕 모던한 REST API 제공**

#### 장점
- ✅ **RESTful API** (HTTP 기반)
- ✅ JSON 데이터 포맷
- ✅ 모바일 앱 개발 친화적
- ✅ OAuth 2.0 인증 지원
- ✅ 실시간 WebSocket 지원

#### 제약사항
- ❌ 일부 기능 유료화
- ❌ API 호출 제한 (시간당 제한)
- ❌ 개발자 승인 과정 필요
- ❌ 문서화 수준이 키움증권 대비 부족

#### 기술 스펙
```
- 프로토콜: HTTPS REST API
- 실시간: WebSocket
- 데이터: JSON
- 인증: OAuth 2.0
- 비용: 기본 무료, 고급 기능 유료
```

### 3. 대신증권 CYBOS Plus API
**🏢 기관투자자 위주의 서비스**

#### 장점
- ✅ 안정적인 데이터 품질
- ✅ 대용량 데이터 처리 가능
- ✅ 기업 공시 정보 풍부

#### 제약사항
- ❌ **개인투자자 접근 제한적**
- ❌ 별도 계약 필요 (비용 발생)
- ❌ COM 기반 (Windows 전용)
- ❌ 복잡한 설치 과정

### 4. 미래에셋증권 HERO API
**💼 제한적 개방**

#### 특징
- 🔒 주로 기관투자자 대상
- 🔒 개인투자자 이용 제한적
- 🔒 별도 심사 과정 필요

## 🎯 모바일 앱 개발을 위한 권장 사항

### 1차 권장: 하이브리드 접근 방식

#### 아키텍처 설계
```
[모바일 앱] ↔ [백엔드 서버] ↔ [키움 Open API]
    ↕              ↕              ↕
 (Flutter)     (Node.js)      (Windows VM)
```

#### 구현 방식
1. **모바일 앱**: Flutter로 크로스플랫폼 개발
2. **백엔드 서버**: Node.js + Express
3. **API 연동 서버**: Windows VM에서 키움 API 연동
4. **통신**: WebSocket으로 실시간 데이터 전송

### 2차 권장: REST API 방식 (미래 대비)

#### 한국투자증권 KIS API 활용
```
[모바일 앱] ↔ [KIS API Server]
    ↕              ↕
 (Flutter)    (HTTPS REST)
```

## 🛠️ 기술 구현 방안

### Phase 1: POC (Proof of Concept)
```javascript
// 백엔드 서버 (Node.js)
const express = require('express');
const WebSocket = require('ws');

// 키움 API 연동 (Python 래퍼)
const kiwoomApi = require('./kiwoom-wrapper');

// 실시간 데이터 중계
app.get('/api/realtime/:stock', (req, res) => {
  const stockCode = req.params.stock;
  kiwoomApi.subscribeRealtime(stockCode, (data) => {
    ws.send(JSON.stringify(data));
  });
});
```

### Phase 2: 자동매매 구현
```python
# 키움 API 래퍼 (Python)
import pythoncom
from PyQt5.QtWidgets import *
import sys
from Kiwoom import *

class AutoTrader:
    def __init__(self):
        self.kiwoom = Kiwoom()
        
    def buy_order(self, stock_code, quantity, price):
        # 매수 주문 실행
        self.kiwoom.send_order("매수", "0101", account, 1, 
                              stock_code, quantity, price, "00", "")
```

### Phase 3: 모바일 앱
```dart
// Flutter 모바일 앱
class TradingScreen extends StatefulWidget {
  @override
  _TradingScreenState createState() => _TradingScreenState();
}

class _TradingScreenState extends State<TradingScreen> {
  WebSocketChannel channel;
  
  @override
  void initState() {
    channel = WebSocketChannel.connect(
      Uri.parse('ws://your-server.com/realtime'),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return StreamBuilder(
      stream: channel.stream,
      builder: (context, snapshot) {
        // 실시간 데이터 표시
      },
    );
  }
}
```

## 💰 비용 분석

### 개발 비용
| 항목 | 키움증권 | 한국투자증권 | 대신증권 |
|------|----------|--------------|----------|
| API 이용료 | 무료* | 무료/유료 | 유료 |
| 데이터비 | 포함 | 별도 | 별도 |
| 개발 복잡도 | 높음 | 중간 | 높음 |
| 모바일 대응 | 복잡 | 용이 | 복잡 |

*키움증권: 월 수수료 조건 충족 시 무료

### 운영 비용 (월간)
- **서버 비용**: 50-100만원
- **Windows VM**: 20-30만원 (키움 API용)
- **데이터 비용**: 0-50만원 (API별 상이)
- **총 비용**: 70-180만원/월

## 🚀 개발 로드맵

### 1단계: 기술 검증 (2-3주)
- [ ] 키움 Open API+ 개발환경 구축
- [ ] 기본 데이터 조회 기능 테스트
- [ ] 백엔드 서버 - API 연동 테스트

### 2단계: MVP 개발 (4-6주)
- [ ] 모바일 앱 UI 구현
- [ ] 실시간 시세 표시 기능
- [ ] 기본 매수/매도 기능

### 3단계: 고도화 (6-8주)
- [ ] 자동매매 알고리즘 구현
- [ ] 리스크 관리 기능
- [ ] 백테스팅 기능

## 🔍 추천 결론

### 🥇 1순위: 키움증권 Open API+
**개인투자자 자동매매 개발의 사실상 표준**
- 무료 이용 가능 (조건부)
- 풍부한 레퍼런스 및 커뮤니티
- 완성도 높은 자동매매 기능

### 🥈 2순위: 한국투자증권 KIS API
**모바일 친화적이지만 아직 성숙도 부족**
- 모바일 개발에 적합한 REST API
- 상대적으로 새로운 서비스로 안정성 검증 필요

## 📞 다음 단계 액션 아이템

1. **키움증권 계좌 개설** 및 Open API+ 신청
2. **개발환경 구축** (Windows VM 포함)
3. **POC 개발 시작** (기본 데이터 조회)
4. **법률 검토** (프로그램매매 신고 등)

---

**작성일**: 2025년 9월 12일  
**업데이트**: API 정책 변경 시 수시 업데이트 예정


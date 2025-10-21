# 🎨 자동매매 앱 UI/UX 설계

## 📋 개요
사용자 친화적이고 직관적인 자동매매 앱의 사용자 인터페이스와 사용자 경험을 설계한 문서입니다.

## 🎯 디자인 원칙

### 핵심 원칙
- **단순성 (Simplicity)**: 복잡한 금융 정보를 쉽게 이해할 수 있도록
- **신뢰성 (Trust)**: 안정감을 주는 디자인으로 사용자 신뢰 구축
- **접근성 (Accessibility)**: 모든 사용자가 쉽게 사용할 수 있도록
- **실시간성 (Real-time)**: 실시간 정보를 직관적으로 표현

### 색상 팔레트
```
주색상 (Primary):   #1565C0 (신뢰감 있는 블루)
보조색상 (Secondary): #FFC107 (포인트 옐로우)
성공 (Success):     #4CAF50 (녹색 - 수익, 매수)
위험 (Danger):      #F44336 (빨간색 - 손실, 매도)
배경 (Background):  #F5F5F5 (라이트 그레이)
텍스트 (Text):      #212121 (다크 그레이)
서브텍스트 (Sub):   #757575 (미드 그레이)
```

## 📱 1. 앱 구조 및 네비게이션

### 1.1 앱 구조도
```
┌─────────────────────────────────────┐
│             스플래시 화면            │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│            로그인/회원가입            │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│              메인 화면               │
├─────────────────────────────────────┤
│  [홈] [포트폴리오] [거래] [설정]     │
└─────────────────────────────────────┘
```

### 1.2 바텀 네비게이션 구조
```dart
// 메인 네비게이션 구조
class MainNavigation extends StatefulWidget {
  @override
  _MainNavigationState createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _selectedIndex = 0;
  
  final List<Widget> _screens = [
    DashboardScreen(),      // 홈
    PortfolioScreen(),      // 포트폴리오
    TradingScreen(),        // 거래
    SettingsScreen(),       // 설정
  ];
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        currentIndex: _selectedIndex,
        onTap: (index) => setState(() => _selectedIndex = index),
        selectedItemColor: Theme.of(context).primaryColor,
        unselectedItemColor: Colors.grey,
        items: [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard),
            label: '홈',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.pie_chart),
            label: '포트폴리오',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.trending_up),
            label: '거래',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings),
            label: '설정',
          ),
        ],
      ),
    );
  }
}
```

## 🏠 2. 홈 화면 (Dashboard)

### 2.1 화면 구성
```
┌─────────────────────────────────────┐
│  👋 안녕하세요, 김투자님              │ ← 인사말
├─────────────────────────────────────┤
│ 📊 포트폴리오 현황                   │
│ 총 자산: ₩12,500,000                │
│ 오늘 손익: +₩150,000 (+1.2%) 🟢     │
├─────────────────────────────────────┤
│ 🤖 자동매매 상태                     │
│ ● 활성화 (3개 전략 실행중)           │
│ [일시정지] [상세보기]                │
├─────────────────────────────────────┤
│ 📈 주요 종목                         │
│ 삼성전자  ₩75,000  ▲ +1.2%          │
│ SK하이닉스 ₩132,000 ▼ -0.8%         │
│ NAVER    ₩210,000  ▲ +2.1%          │
├─────────────────────────────────────┤
│ 🔔 알림                              │
│ • 삼성전자 매수 주문 체결 (09:15)    │
│ • RSI 과매수 신호 발생 (09:30)       │
└─────────────────────────────────────┘
```

### 2.2 대시보드 위젯 구현
```dart
class DashboardScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('CleonAI 자동매매'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.notifications),
            onPressed: () => Navigator.pushNamed(context, '/notifications'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: SingleChildScrollView(
          padding: EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 인사말
              _buildWelcomeCard(),
              SizedBox(height: 16),
              
              // 포트폴리오 현황
              _buildPortfolioSummaryCard(),
              SizedBox(height: 16),
              
              // 자동매매 상태
              _buildTradingStatusCard(),
              SizedBox(height: 16),
              
              // 주요 종목
              _buildWatchlistCard(),
              SizedBox(height: 16),
              
              // 최근 알림
              _buildRecentAlertsCard(),
            ],
          ),
        ),
      ),
    );
  }
  
  Widget _buildPortfolioSummaryCard() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.account_balance_wallet, color: Colors.blue),
                SizedBox(width: 8),
                Text(
                  '포트폴리오 현황',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            SizedBox(height: 16),
            
            // 총 자산
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('총 자산', style: TextStyle(fontSize: 16)),
                Text(
                  '₩12,500,000',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.blue[700],
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            
            // 오늘 손익
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('오늘 손익', style: TextStyle(fontSize: 16)),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green[50],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.trending_up, color: Colors.green, size: 16),
                      SizedBox(width: 4),
                      Text(
                        '+₩150,000 (+1.2%)',
                        style: TextStyle(
                          color: Colors.green[700],
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
```

## 📊 3. 포트폴리오 화면

### 3.1 화면 구성
```
┌─────────────────────────────────────┐
│ 📊 포트폴리오                        │ ← 헤더
├─────────────────────────────────────┤
│ [전체] [주식] [ETF] [기타]           │ ← 탭 필터
├─────────────────────────────────────┤
│ 📈 수익률 차트 (일/주/월/연)         │
│ ┌─────────────────────────────────┐ │
│ │     📈📈📈📈📈               │ │
│ │  +12.5% (지난달 대비)           │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ 💼 보유 종목                         │
│ ┌─────────────────────────────────┐ │
│ │ 삼성전자   10주   ₩750,000      │ │
│ │ +₩50,000 (+7.1%) 🟢           │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ SK하이닉스  5주   ₩660,000      │ │
│ │ -₩20,000 (-2.9%) 🔴           │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 3.2 수익률 차트 구현
```dart
import 'package:fl_chart/fl_chart.dart';

class PortfolioChart extends StatelessWidget {
  final List<PortfolioData> data;
  final ChartPeriod period;
  
  const PortfolioChart({Key? key, required this.data, required this.period});
  
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 200,
      child: LineChart(
        LineChartData(
          gridData: FlGridData(show: true),
          titlesData: FlTitlesData(
            leftTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                reservedSize: 40,
                getTitlesWidget: (value, meta) => Text(
                  '${value.toInt()}%',
                  style: TextStyle(fontSize: 10),
                ),
              ),
            ),
            bottomTitles: AxisTitles(
              sideTitles: SideTitles(
                showTitles: true,
                getTitlesWidget: (value, meta) {
                  // 기간별 라벨 처리
                  return Text(_getDateLabel(value.toInt()));
                },
              ),
            ),
          ),
          borderData: FlBorderData(show: false),
          lineBarsData: [
            LineChartBarData(
              spots: _generateSpots(),
              isCurved: true,
              color: Colors.blue,
              barWidth: 3,
              isStrokeCapRound: true,
              belowBarData: BarAreaData(
                show: true,
                color: Colors.blue.withOpacity(0.1),
              ),
              dotData: FlDotData(show: false),
            ),
          ],
        ),
      ),
    );
  }
  
  List<FlSpot> _generateSpots() {
    return data.asMap().entries.map((entry) {
      return FlSpot(entry.key.toDouble(), entry.value.returnRate);
    }).toList();
  }
}
```

## 💹 4. 거래 화면

### 4.1 화면 구성
```
┌─────────────────────────────────────┐
│ 💹 거래                              │ ← 헤더
├─────────────────────────────────────┤
│ [수동거래] [자동매매] [주문내역]      │ ← 탭
├─────────────────────────────────────┤
│ 🤖 자동매매 제어판                   │
│ ┌─────────────────────────────────┐ │
│ │ 상태: ● 활성화                  │ │
│ │ 실행 전략: 3개                  │ │
│ │ 오늘 거래: 5건                  │ │
│ │ [⏸️ 일시정지] [⚙️ 설정]        │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ 📊 실시간 신호                       │
│ ┌─────────────────────────────────┐ │
│ │ 삼성전자  🔴 매도신호 (RSI: 75) │ │
│ │ NAVER    🟢 매수신호 (MA교차)   │ │
│ │ 카카오    🟡 관망 (중립)        │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ 📈 차트 분석                         │
│ [종목검색] [1분] [5분] [일봉]        │
└─────────────────────────────────────┘
```

### 4.2 실시간 신호 위젯
```dart
class TradingSignalsWidget extends StatelessWidget {
  final List<TradingSignal> signals;
  
  const TradingSignalsWidget({Key? key, required this.signals});
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.timeline, color: Colors.orange),
                SizedBox(width: 8),
                Text(
                  '실시간 신호',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            SizedBox(height: 16),
            
            ...signals.map((signal) => _buildSignalItem(signal)),
          ],
        ),
      ),
    );
  }
  
  Widget _buildSignalItem(TradingSignal signal) {
    Color signalColor;
    IconData signalIcon;
    
    switch (signal.type) {
      case SignalType.BUY:
        signalColor = Colors.green;
        signalIcon = Icons.trending_up;
        break;
      case SignalType.SELL:
        signalColor = Colors.red;
        signalIcon = Icons.trending_down;
        break;
      default:
        signalColor = Colors.grey;
        signalIcon = Icons.remove;
    }
    
    return Container(
      margin: EdgeInsets.symmetric(vertical: 4),
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        border: Border.left(color: signalColor, width: 4),
        color: signalColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(signalIcon, color: signalColor, size: 20),
          SizedBox(width: 12),
          
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  signal.stockName,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
                Text(
                  signal.reason,
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          
          Text(
            signal.strength,
            style: TextStyle(
              color: signalColor,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
```

## ⚙️ 5. 설정 화면

### 5.1 화면 구성
```
┌─────────────────────────────────────┐
│ ⚙️ 설정                             │
├─────────────────────────────────────┤
│ 👤 계정 관리                         │
│ • 프로필 수정                        │
│ • 비밀번호 변경                      │
│ • 생체인증 설정                      │
├─────────────────────────────────────┤
│ 🤖 자동매매 설정                     │
│ • 매매 전략 설정                     │
│ • 리스크 관리 설정                   │
│ • 알림 설정                          │
├─────────────────────────────────────┤
│ 🔔 알림 설정                         │
│ • 푸시 알림 on/off                   │
│ • 거래 체결 알림                     │
│ • 신호 발생 알림                     │
├─────────────────────────────────────┤
│ 📊 데이터 및 개인정보                │
│ • 데이터 내보내기                    │
│ • 개인정보 처리방침                  │
│ • 서비스 이용약관                    │
├─────────────────────────────────────┤
│ ℹ️ 앱 정보                           │
│ • 버전 정보 (v1.0.0)                │
│ • 고객지원                           │
│ • 로그아웃                           │
└─────────────────────────────────────┘
```

### 5.2 설정 화면 구현
```dart
class SettingsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('설정'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: ListView(
        children: [
          // 계정 관리 섹션
          _buildSectionHeader('계정 관리'),
          _buildSettingItem(
            icon: Icons.person,
            title: '프로필 수정',
            onTap: () => Navigator.pushNamed(context, '/profile'),
          ),
          _buildSettingItem(
            icon: Icons.lock,
            title: '비밀번호 변경',
            onTap: () => Navigator.pushNamed(context, '/change-password'),
          ),
          _buildSettingItem(
            icon: Icons.fingerprint,
            title: '생체인증 설정',
            trailing: Switch(
              value: true,
              onChanged: (value) => _toggleBiometric(value),
            ),
          ),
          
          Divider(),
          
          // 자동매매 설정 섹션
          _buildSectionHeader('자동매매 설정'),
          _buildSettingItem(
            icon: Icons.tune,
            title: '매매 전략 설정',
            onTap: () => Navigator.pushNamed(context, '/strategy-settings'),
          ),
          _buildSettingItem(
            icon: Icons.security,
            title: '리스크 관리 설정',
            onTap: () => Navigator.pushNamed(context, '/risk-settings'),
          ),
          
          Divider(),
          
          // 알림 설정 섹션
          _buildSectionHeader('알림 설정'),
          _buildSettingItem(
            icon: Icons.notifications,
            title: '푸시 알림',
            trailing: Switch(
              value: true,
              onChanged: (value) => _toggleNotifications(value),
            ),
          ),
          
          Divider(),
          
          // 앱 정보 섹션
          _buildSectionHeader('앱 정보'),
          _buildSettingItem(
            icon: Icons.info,
            title: '버전 정보',
            subtitle: 'v1.0.0',
            onTap: () => _showVersionInfo(context),
          ),
          _buildSettingItem(
            icon: Icons.support,
            title: '고객지원',
            onTap: () => Navigator.pushNamed(context, '/support'),
          ),
          _buildSettingItem(
            icon: Icons.logout,
            title: '로그아웃',
            textColor: Colors.red,
            onTap: () => _showLogoutDialog(context),
          ),
        ],
      ),
    );
  }
  
  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: EdgeInsets.fromLTRB(16, 24, 16, 8),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.bold,
          color: Colors.grey[600],
        ),
      ),
    );
  }
  
  Widget _buildSettingItem({
    required IconData icon,
    required String title,
    String? subtitle,
    Widget? trailing,
    Color? textColor,
    VoidCallback? onTap,
  }) {
    return ListTile(
      leading: Icon(icon, color: textColor ?? Colors.grey[600]),
      title: Text(
        title,
        style: TextStyle(color: textColor),
      ),
      subtitle: subtitle != null ? Text(subtitle) : null,
      trailing: trailing ?? Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }
}
```

## 🔔 6. 알림 시스템

### 6.1 푸시 알림 유형
```dart
enum NotificationType {
  TRADE_EXECUTED,    // 거래 체결
  SIGNAL_GENERATED,  // 신호 발생
  RISK_ALERT,        // 리스크 경고
  SYSTEM_ALERT,      // 시스템 알림
  MARKET_NEWS,       // 시장 뉴스
}

class NotificationService {
  static Future<void> showLocalNotification({
    required String title,
    required String body,
    required NotificationType type,
    Map<String, dynamic>? data,
  }) async {
    final FlutterLocalNotificationsPlugin notifications = 
        FlutterLocalNotificationsPlugin();
    
    final AndroidNotificationDetails androidDetails = 
        AndroidNotificationDetails(
      'trading_channel',
      'Trading Notifications',
      channelDescription: '자동매매 알림',
      importance: Importance.high,
      priority: Priority.high,
      icon: _getNotificationIcon(type),
      color: _getNotificationColor(type),
    );
    
    final NotificationDetails notificationDetails = NotificationDetails(
      android: androidDetails,
    );
    
    await notifications.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      notificationDetails,
      payload: jsonEncode(data),
    );
  }
  
  static Color _getNotificationColor(NotificationType type) {
    switch (type) {
      case NotificationType.TRADE_EXECUTED:
        return Colors.blue;
      case NotificationType.SIGNAL_GENERATED:
        return Colors.orange;
      case NotificationType.RISK_ALERT:
        return Colors.red;
      default:
        return Colors.grey;
    }
  }
}
```

## 📊 7. 반응형 디자인

### 7.1 화면 크기별 대응
```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget tablet;
  
  const ResponsiveLayout({
    Key? key,
    required this.mobile,
    required this.tablet,
  });
  
  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 600) {
          return mobile;
        } else {
          return tablet;
        }
      },
    );
  }
}

// 사용 예시
class DashboardScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ResponsiveLayout(
      mobile: MobileDashboard(),
      tablet: TabletDashboard(),
    );
  }
}
```

## 🌙 8. 다크 테마 지원

### 8.1 테마 설정
```dart
class AppTheme {
  static ThemeData lightTheme = ThemeData(
    primarySwatch: Colors.blue,
    brightness: Brightness.light,
    scaffoldBackgroundColor: Colors.grey[50],
    cardColor: Colors.white,
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.white,
      foregroundColor: Colors.black,
      elevation: 0,
    ),
  );
  
  static ThemeData darkTheme = ThemeData(
    primarySwatch: Colors.blue,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: Colors.grey[900],
    cardColor: Colors.grey[800],
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.grey[850],
      foregroundColor: Colors.white,
      elevation: 0,
    ),
  );
}
```

## 📋 UI/UX 체크리스트

### 사용성 테스트
- [ ] 주요 기능까지 3클릭 이내 접근 가능
- [ ] 폰트 크기 조정 기능 (접근성)
- [ ] 색약자 고려한 색상 설계
- [ ] 손가락으로 조작하기 쉬운 버튼 크기 (최소 44px)

### 성능 최적화
- [ ] 이미지 지연 로딩 (Lazy Loading)
- [ ] 리스트 가상화 (Virtual Scrolling)
- [ ] 불필요한 리빌드 최소화
- [ ] 애니메이션 성능 최적화

### 사용자 경험
- [ ] 로딩 상태 명확한 표시
- [ ] 오프라인 상태 대응
- [ ] 오류 상황 친화적 메시지
- [ ] 튜토리얼 및 온보딩 제공

### 접근성
- [ ] 스크린 리더 지원
- [ ] 키보드 네비게이션 지원
- [ ] 고대비 모드 지원
- [ ] 음성 안내 기능 (선택사항)

## 🎨 디자인 시스템

### 타이포그래피
```dart
class AppTextStyles {
  static const TextStyle headline1 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    color: Colors.black87,
  );
  
  static const TextStyle headline2 = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w600,
    color: Colors.black87,
  );
  
  static const TextStyle bodyText1 = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.normal,
    color: Colors.black87,
  );
  
  static const TextStyle caption = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.normal,
    color: Colors.grey,
  );
}
```

### 스페이싱 시스템
```dart
class AppSpacing {
  static const double xs = 4.0;
  static const double sm = 8.0;
  static const double md = 16.0;
  static const double lg = 24.0;
  static const double xl = 32.0;
  static const double xxl = 48.0;
}
```

## 📱 프로토타입 이미지

### 주요 화면 목업
```
📱 모바일 화면 크기: 375 x 812 (iPhone 12 기준)

[스플래시 화면]
- 로고 중앙 배치
- 로딩 인디케이터
- 브랜드 컬러 배경

[로그인 화면]  
- 간단한 폼 레이아웃
- 생체인증 옵션
- 소셜 로그인 지원

[대시보드]
- 카드 기반 레이아웃
- 실시간 데이터 표시
- 시각적 차트 활용

[거래 화면]
- 탭 기반 네비게이션
- 실시간 차트
- 직관적인 버튼 배치
```

---

**작성일**: 2025년 9월 12일  
**디자인 시스템**: Material Design 3.0 기반  
**접근성 등급**: WCAG 2.1 AA 준수 목표








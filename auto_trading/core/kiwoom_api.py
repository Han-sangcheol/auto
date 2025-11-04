"""
키움 Open API 연동 래퍼 모듈

[파일 역할]
키움증권 Open API+와 통신하는 Python 래퍼 클래스입니다.
복잡한 COM 객체 통신을 간단한 Python 메서드로 래핑합니다.

[주요 기능]
- 공동인증서 로그인 처리
- 계좌 정보 조회 (잔고, 보유 종목)
- 주문 전송 (매수, 매도)
- 실시간 시세 데이터 수신
- TR (Transaction) 조회
- API 호출 제한 관리 (초당 5건)

[중요 사항]
- Windows 전용 (COM 객체 사용)
- 키움 Open API+ 설치 필수
- PyQt5 이벤트 루프 필요

[사용 방법]
kiwoom = KiwoomAPI()
if kiwoom.login():
    balance = kiwoom.get_account_balance()
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop
from typing import Dict, List, Optional, Callable
import time
from logger import log
from config import Config


class KiwoomAPI:
    """키움 Open API 래퍼 클래스"""
    
    # SendOrder 에러 코드
    ERROR_CODES = {
        0: "정상처리",
        -10: "실패",
        -100: "사용자정보교환 실패",
        -101: "서버 접속 실패",
        -102: "버전처리 실패",
        -200: "시세조회 과부하",
        -201: "REQUEST_INPUT_st 에러",
        -202: "시세조회 제한",
        -300: "주문 입력값 오류",
        -301: "계좌비밀번호 없음",
        -302: "타인계좌 사용 오류",
        -303: "주문가격이 주문착오 금액기준 초과",
        -304: "주문수량이 총발행주수의 1% 초과",
        -305: "주문수량은 총발행주수의 3% 초과",
        -306: "주문가격이 가격제한폭을 초과",
        -307: "주문가능수량을 초과",
        -308: "주문가능금액을 초과",
    }
    
    def __init__(self):
        """초기화"""
        from config import Config
        
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.is_connected = False
        self.account_number = None
        
        # 계좌 비밀번호 설정
        # .env 파일에서 비밀번호를 읽어옴
        self.account_password = Config.KIWOOM_ACCOUNT_PASSWORD or ""
        
        # 모의투자 기본 비밀번호 처리
        if Config.USE_SIMULATION and not self.account_password:
            self.account_password = "0000"
            log.info("모의투자: 기본 비밀번호 '0000' 사용")
        
        # 비밀번호 검증
        self._validate_password()
        
        self.callbacks = {}
        
        # 이벤트 루프
        self.login_event_loop = None
        self.request_event_loop = None
        
        # TR 요청 제한 관리 (과부하 방지)
        self.last_request_time = 0
        self.request_delay = 0.5  # 초당 최대 2건으로 제한 (안전 마진)
        self.request_count = 0  # 요청 카운트
        self.request_history = []  # 최근 요청 시간 기록
        
        # 주문 제한 관리
        self.last_order_time = 0
        self.order_delay = 0.3  # 주문 간 최소 간격 (초당 최대 3건)
        self.order_count_today = 0  # 일일 주문 카운트
        self.order_history = []  # 최근 주문 시간 기록 (1초 내)
        self.max_orders_per_day = 1000  # 일일 최대 주문 횟수 (키움 API 실제 한도)
        self.max_orders_per_second = 3  # 초당 최대 주문 횟수
        self.order_warning_threshold = 800  # 경고 임계값 (80%)
        self.order_limit_threshold = 900  # 제한 임계값 (90% - 손절/익절만 허용)
        
        # 데이터 저장
        self.data_cache = {}
        
        # 연속조회 지원 (Prev_Next)
        self.last_prev_next = "0"  # OnReceiveTrData에서 업데이트
        
        # 시그널 연결
        self._connect_signals()
        
        log.info("키움 API 초기화 완료")
    
    def _validate_password(self) -> bool:
        """
        비밀번호 유효성 검증
        
        Returns:
            검증 성공 여부
        """
        if self.account_password:
            # 길이 체크
            if len(self.account_password) != 4:
                log.warning(f"⚠️ 계좌 비밀번호는 4자리여야 합니다: {len(self.account_password)}자리")
                return False
            
            # 숫자 체크
            if not self.account_password.isdigit():
                log.warning("⚠️ 계좌 비밀번호는 숫자만 가능합니다")
                return False
            
            log.info(f"✅ 계좌 비밀번호 검증 완료: {self.account_password}")
            return True
        else:
            log.warning("⚠️ 계좌 비밀번호 미설정 - API 저장 비밀번호 사용")
            return True
    
    def _connect_signals(self):
        """이벤트 시그널 연결"""
        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveRealData.connect(self._on_receive_real_data)
        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)
    
    def login(self) -> bool:
        """
        키움 API 로그인
        
        공동인증서 창이 자동으로 표시됩니다.
        별도의 계좌 비밀번호 입력은 필요하지 않습니다.
        
        Returns:
            로그인 성공 여부
        """
        try:
            log.info("⏳ 키움 Open API 로그인 시도 중...")
            log.info("   → 공동인증서 창이 표시됩니다 (약 5-10초 소요)")
            self.login_event_loop = QEventLoop()
            self.ocx.dynamicCall("CommConnect()")
            self.login_event_loop.exec_()
            
            if self.is_connected:
                log.success("✅ 키움 Open API 연결 성공!")
                
                # 계좌번호 조회
                account_list = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
                accounts = account_list.split(';')[:-1]  # 마지막 빈 문자열 제거
                
                log.info(f"📋 발견된 계좌 수: {len(accounts)}개")
                
                if Config.USE_SIMULATION:
                    # 모의투자 계좌 찾기 (8로 시작)
                    sim_accounts = [acc for acc in accounts if acc.startswith('8')]
                    if sim_accounts:
                        self.account_number = sim_accounts[0]
                        log.success(f"✅ 모의투자 계좌 로그인 성공")
                        log.info(f"   💳 계좌번호: {self.account_number}")
                    else:
                        log.error("❌ 모의투자 계좌를 찾을 수 없습니다.")
                        log.error(f"   발견된 계좌: {accounts}")
                        return False
                else:
                    # 실계좌 (8로 시작하지 않는 계좌)
                    real_accounts = [acc for acc in accounts if not acc.startswith('8')]
                    if real_accounts:
                        self.account_number = real_accounts[0]
                        log.success(f"✅ 실계좌 로그인 성공")
                        log.info(f"   💳 계좌번호: {self.account_number}")
                    else:
                        log.error("❌ 실계좌를 찾을 수 없습니다.")
                        log.error(f"   발견된 계좌: {accounts}")
                        return False
                
                # 사용자 정보 출력
                user_name = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_NAME")
                server_type = self.ocx.dynamicCall("GetLoginInfo(QString)", "GetServerGubun")
                
                log.info(f"   👤 사용자: {user_name}")
                log.info(f"   🖥️  서버: {'모의투자 서버' if server_type == '1' else '실서버'}")
                log.info(f"   🔗 연결 상태: 정상")
                
                # 계좌 비밀번호 등록창 자동 표시
                log.info("")
                log.info("=" * 80)
                log.info("📌 계좌 비밀번호 등록")
                log.info("=" * 80)
                log.info("계좌 비밀번호 등록창이 표시됩니다.")
                log.info("계좌를 선택하고 비밀번호(4자리)를 입력한 후 '확인'을 클릭하세요.")
                log.info(f"💡 모의투자 계좌 비밀번호: 0000 (또는 원하는 4자리 숫자)")
                log.info("💡 등록 후 'AUTO' 체크박스를 선택하면 다음부터 자동 로그인됩니다.")
                log.info("=" * 80)
                log.info("")
                
                # ShowAccountWindow 호출하여 계좌 비밀번호 등록창 표시
                result = self.ocx.dynamicCall("KOA_Functions(QString, QString)", "ShowAccountWindow", "")
                log.info(f"계좌 비밀번호 등록창 호출 결과: {result}")
                
                return True
            else:
                log.error("❌ 키움 Open API 연결 실패")
                log.error("   공동인증서 로그인을 취소했거나 실패했습니다")
                return False
                
        except Exception as e:
            log.error(f"로그인 중 오류 발생: {e}")
            return False
    
    def reconnect(self) -> bool:
        """
        API 재연결 시도
        
        Returns:
            재연결 성공 여부
        """
        try:
            log.warning("🔄 API 재연결 시도 중...")
            
            # 기존 연결 해제
            if self.is_connected:
                try:
                    self.ocx.dynamicCall("CommTerminate()")
                    time.sleep(1)
                except:
                    pass
            
            self.is_connected = False
            
            # 재로그인
            success = self.login()
            
            if success:
                log.success("✅ API 재연결 성공!")
            else:
                log.error("❌ API 재연결 실패")
            
            return success
            
        except Exception as e:
            log.error(f"API 재연결 중 오류: {e}")
            return False
    
    def get_connection_status(self) -> Dict:
        """
        연결 상태 정보 반환
        
        Returns:
            연결 상태 딕셔너리
        """
        try:
            connect_state = self.ocx.dynamicCall("GetConnectState()")
            
            return {
                'is_connected': self.is_connected and connect_state == 1,
                'connect_state': connect_state,
                'account_number': self.account_number,
                'has_account': self.account_number is not None,
            }
        except Exception as e:
            log.error(f"연결 상태 조회 중 오류: {e}")
            return {
                'is_connected': False,
                'connect_state': 0,
                'account_number': None,
                'has_account': False,
                'error': str(e)
            }
    
    def _on_event_connect(self, err_code):
        """로그인 이벤트 처리"""
        if err_code == 0:
            self.is_connected = True
            log.info("로그인 연결 성공")
        else:
            self.is_connected = False
            log.error(f"로그인 연결 실패: {err_code}")
        
        if self.login_event_loop:
            self.login_event_loop.exit()
        
        return 0  # 🆕 PyQt5 COM 이벤트 핸들러는 정수 반환 필요
    
    def _wait_for_request(self):
        """
        TR 요청 제한 준수 (과부하 방지)
        
        키움 API 제한:
        - 초당 5건 (공식)
        - 우리 제한: 초당 2건 (안전 마진 150%)
        """
        import time
        current_time = time.time()
        
        # 1초 이내의 최근 요청만 유지
        self.request_history = [
            t for t in self.request_history 
            if current_time - t < 1.0
        ]
        
        # 1초 내에 2건 이상이면 대기
        if len(self.request_history) >= 2:
            oldest_request = min(self.request_history)
            wait_time = 1.0 - (current_time - oldest_request) + 0.1  # 여유 0.1초
            if wait_time > 0:
                log.warning(f"⏳ API 과부하 방지 대기: {wait_time:.1f}초")
                time.sleep(wait_time)
                current_time = time.time()
                # 대기 후 히스토리 재정리
                self.request_history = [
                    t for t in self.request_history 
                    if current_time - t < 1.0
                ]
        
        # 최소 간격 보장 (0.5초)
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        
        # 요청 시간 기록
        self.last_request_time = time.time()
        self.request_history.append(self.last_request_time)
        self.request_count += 1
        
        # 통계 로그 (100건마다)
        if self.request_count % 100 == 0:
            log.info(f"📊 API 요청 통계: 총 {self.request_count}건")
    
    def _wait_for_order(self, order_type: str = "일반") -> bool:
        """
        주문 제한 준수 (우선순위 지원)
        
        키움 API 주문 제한:
        - 초당 5건 (공식)
        - 우리 제한: 초당 3건 (안전 마진)
        - 일일 1000건 제한 (키움 API 실제 한도)
        
        Args:
            order_type: 주문 유형 ("손절", "익절", "일반")
        
        Returns:
            주문 가능 여부
        """
        import time
        current_time = time.time()
        
        # 일일 주문 한도 체크
        if self.order_count_today >= self.max_orders_per_day:
            log.error(
                f"⛔ 일일 주문 한도 초과: {self.order_count_today}/{self.max_orders_per_day}건"
            )
            return False
        
        # 경고 임계값 체크 (80%)
        if self.order_count_today >= self.order_warning_threshold:
            if self.order_count_today == self.order_warning_threshold:
                log.warning(
                    f"⚠️  일일 주문 한도 80% 도달: {self.order_count_today}/{self.max_orders_per_day}건"
                )
        
        # 제한 임계값 체크 (90% - 손절/익절만 허용)
        if self.order_count_today >= self.order_limit_threshold:
            if order_type not in ["손절", "익절"]:
                log.warning(
                    f"⚠️  일일 주문 한도 90% 초과 - {order_type} 주문 제한: "
                    f"{self.order_count_today}/{self.max_orders_per_day}건"
                )
                return False
            else:
                log.info(
                    f"✅ 중요 주문({order_type}) 허용: "
                    f"{self.order_count_today}/{self.max_orders_per_day}건"
                )
        
        # 1초 이내의 최근 주문만 유지
        self.order_history = [
            t for t in self.order_history 
            if current_time - t < 1.0
        ]
        
        # 1초 내에 3건 이상이면 대기
        if len(self.order_history) >= self.max_orders_per_second:
            oldest_order = min(self.order_history)
            wait_time = 1.0 - (current_time - oldest_order) + 0.1  # 여유 0.1초
            if wait_time > 0:
                log.warning(f"⏳ 주문 과부하 방지 대기: {wait_time:.1f}초")
                time.sleep(wait_time)
                current_time = time.time()
                # 대기 후 히스토리 재정리
                self.order_history = [
                    t for t in self.order_history 
                    if current_time - t < 1.0
                ]
        
        # 최소 간격 보장 (0.3초)
        elapsed = current_time - self.last_order_time
        if elapsed < self.order_delay:
            time.sleep(self.order_delay - elapsed)
        
        # 주문 시간 기록
        self.last_order_time = time.time()
        self.order_history.append(self.last_order_time)
        self.order_count_today += 1
        
        # 통계 로그 (10건마다)
        if self.order_count_today % 10 == 0:
            log.info(
                f"📊 주문 통계: 오늘 {self.order_count_today}건 "
                f"(한도: {self.max_orders_per_day}건)"
            )
        
        return True
    
    def reset_daily_order_count(self):
        """일일 주문 카운트 리셋 (장 시작 시 호출)"""
        self.order_count_today = 0
        self.order_history = []
        log.info("📊 일일 주문 카운트 리셋")
    
    def get_order_statistics(self) -> Dict:
        """
        주문 통계 정보 반환
        
        Returns:
            주문 통계 딕셔너리
        """
        return {
            'order_count_today': self.order_count_today,
            'max_orders_per_day': self.max_orders_per_day,
            'remaining_orders': self.max_orders_per_day - self.order_count_today,
            'orders_per_second': len(self.order_history)
        }
    
    def get_balance(self) -> Dict:
        """
        계좌 잔고 조회
        
        Returns:
            잔고 정보 딕셔너리
        """
        try:
            self._wait_for_request()
            
            # OPW00001: 예수금상세현황요청
            self.ocx.dynamicCall(
                "SetInputValue(QString, QString)",
                "계좌번호",
                self.account_number
            )
            
            # 모의투자는 비밀번호 관련 필드 모두 생략
            if not Config.USE_SIMULATION:
                self.ocx.dynamicCall(
                    "SetInputValue(QString, QString)",
                    "비밀번호",
                    Config.KIWOOM_ACCOUNT_PASSWORD
                )
                self.ocx.dynamicCall(
                    "SetInputValue(QString, QString)",
                    "비밀번호입력매체구분",
                    "00"
                )
            self.ocx.dynamicCall(
                "SetInputValue(QString, QString)",
                "조회구분",
                "2"  # 2: 일반조회
            )
            
            self.request_event_loop = QEventLoop()
            ret = self.ocx.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "예수금상세현황요청",
                "OPW00001",
                0,
                "2000"
            )
            
            if ret == 0:
                self.request_event_loop.exec_()
                balance_data = self.data_cache.get('balance', {})
                
                # 조회 성공 시 상세 로그
                if balance_data:
                    log.success(f"✅ 잔고 조회 성공")
                    log.info(f"   💰 예수금: {balance_data.get('cash', 0):,}원")
                    log.info(f"   📊 총평가: {balance_data.get('total_value', 0):,}원")
                    log.info(f"   📈 총손익: {balance_data.get('profit_loss', 0):+,}원")
                else:
                    log.warning("⚠️  잔고 조회 응답 없음 (데이터 파싱 실패 가능)")
                
                return balance_data
            else:
                log.error(f"❌ 잔고 조회 실패: {ret}")
                log.error(f"   에러 코드 -202: 조회 과부하 (잠시 후 재시도)")
                return {}
                
        except Exception as e:
            log.error(f"잔고 조회 중 오류: {e}")
            return {}
    
    def get_stock_name(self, stock_code: str) -> str:
        """
        종목 코드로 종목명 조회 (API 제한 없음)
        
        Args:
            stock_code: 종목 코드 (예: "005930")
        
        Returns:
            종목명 (예: "삼성전자") 또는 조회 실패 시 종목 코드 반환
        """
        try:
            # GetMasterCodeName: 종목명 조회 (즉시 조회, API 제한 없음)
            stock_name = self.ocx.dynamicCall(
                "GetMasterCodeName(QString)",
                stock_code
            ).strip()
            
            if stock_name:
                return stock_name
            else:
                log.warning(f"종목명 조회 실패 (빈 문자열): {stock_code}")
                return stock_code
                
        except Exception as e:
            log.error(f"종목명 조회 중 오류 ({stock_code}): {e}")
            return stock_code
    
    def search_stock_by_name(self, stock_name: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        🆕 종목명으로 종목 코드 검색 (부분 일치 지원)
        
        Args:
            stock_name: 검색할 종목명 (예: "삼성", "삼성전자")
            max_results: 최대 결과 수
        
        Returns:
            매칭된 종목 리스트 [{'code': '005930', 'name': '삼성전자'}, ...]
        """
        try:
            results = []
            search_name = stock_name.strip().upper()
            
            if not search_name:
                return results
            
            log.info(f"종목명 검색: '{stock_name}'")
            
            # 코스피(0) + 코스닥(10) 전체 종목 코드 가져오기
            for market_code in [0, 10]:
                market_name = "코스피" if market_code == 0 else "코스닥"
                
                # GetCodeListByMarket: 시장별 종목 코드 리스트 (세미콜론 구분)
                code_list_str = self.ocx.dynamicCall(
                    "GetCodeListByMarket(QString)",
                    str(market_code)
                ).strip()
                
                if not code_list_str:
                    continue
                
                # 종목 코드 분리
                code_list = code_list_str.split(';')
                
                for code in code_list:
                    code = code.strip()
                    if not code:
                        continue
                    
                    # 종목명 조회
                    name = self.get_stock_name(code)
                    name_upper = name.upper()
                    
                    # 부분 일치 검색
                    if search_name in name_upper or name_upper in search_name:
                        results.append({
                            'code': code,
                            'name': name,
                            'market': market_name
                        })
                        
                        # 최대 결과 수 제한
                        if len(results) >= max_results:
                            log.info(f"검색 완료: {len(results)}개 종목 발견")
                            return results
            
            log.info(f"검색 완료: {len(results)}개 종목 발견")
            return results
            
        except Exception as e:
            log.error(f"종목명 검색 중 오류: {e}")
            return []
    
    def get_holdings(self) -> List[Dict]:
        """
        보유 종목 조회
        
        Returns:
            보유 종목 리스트
        """
        try:
            self._wait_for_request()
            
            # OPW00018: 계좌평가잔고내역요청
            self.ocx.dynamicCall(
                "SetInputValue(QString, QString)",
                "계좌번호",
                self.account_number
            )
            
            # 모의투자는 비밀번호 관련 필드 모두 생략
            if not Config.USE_SIMULATION:
                self.ocx.dynamicCall(
                    "SetInputValue(QString, QString)",
                    "비밀번호",
                    Config.KIWOOM_ACCOUNT_PASSWORD
                )
                self.ocx.dynamicCall(
                    "SetInputValue(QString, QString)",
                    "비밀번호입력매체구분",
                    "00"
                )
            self.ocx.dynamicCall(
                "SetInputValue(QString, QString)",
                "조회구분",
                "1"  # 1: 합산, 2: 개별
            )
            
            self.request_event_loop = QEventLoop()
            ret = self.ocx.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "계좌평가잔고내역요청",
                "OPW00018",
                0,
                "2001"
            )
            
            if ret == 0:
                self.request_event_loop.exec_()
                holdings = self.data_cache.get('holdings', [])
                
                # 조회 성공 시 상세 로그
                if holdings:
                    log.success(f"✅ 보유종목 조회 성공: {len(holdings)}개")
                    for holding in holdings:
                        log.info(
                            f"   📊 {holding['name']}({holding['code']}): "
                            f"{holding['quantity']}주 @ {holding['buy_price']:,}원 "
                            f"→ {holding.get('current_price', 0):,}원 "
                            f"({holding.get('profit_loss_rate', 0):+.2f}%)"
                        )
                else:
                    log.info("📭 보유종목 없음 (초기 상태)")
                
                return holdings
            else:
                log.error(f"❌ 보유종목 조회 실패: {ret}")
                log.error(f"   에러 코드 -202: 조회 과부하 (잠시 후 재시도)")
                return []
                
        except Exception as e:
            log.error(f"보유종목 조회 중 오류: {e}")
            return []
    
    def get_stock_info(self, stock_code: str) -> Optional[dict]:
        """
        종목 정보 조회 (종목명 + 현재가 + 등락률)
        
        Args:
            stock_code: 종목코드
        
        Returns:
            종목 정보 딕셔너리 또는 None
            {
                'name': 종목명,
                'current_price': 현재가,
                'change_rate': 등락률,
                'volume': 거래량
            }
        """
        try:
            # 1. 종목명 조회 (API 제한 없음)
            stock_name = self.get_stock_name(stock_code)
            
            # 2. 현재가 조회 (API 제한 있음)
            self._wait_for_request()
            
            self.ocx.dynamicCall(
                "SetInputValue(QString, QString)",
                "종목코드",
                stock_code
            )
            
            self.request_event_loop = QEventLoop()
            ret = self.ocx.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "주식기본정보요청",
                "OPT10001",
                0,
                "2003"  # 화면번호
            )
            
            if ret == 0:
                self.request_event_loop.exec_()
                price_data = self.data_cache.get('current_price', {})
                
                if price_data:
                    return {
                        'name': stock_name,
                        'current_price': price_data.get('current_price', 0),
                        'change_rate': price_data.get('change_rate', 0),
                        'volume': price_data.get('volume', 0)
                    }
            
            log.warning(f"종목 정보 조회 실패: {stock_code}")
            return None
            
        except Exception as e:
            log.error(f"종목 정보 조회 오류: {e}")
            return None
    
    def get_current_price(self, stock_code: str) -> Optional[int]:
        """
        현재가 조회 (시간외 거래 시간 지원)
        
        Args:
            stock_code: 종목코드
        
        Returns:
            현재가 또는 None
            - 정규장: 실시간 체결가
            - 시간외: 마지막 체결가(종가) 또는 시간외 호가
        """
        try:
            self._wait_for_request()
            
            # OPT10001: 주식기본정보요청 (시간외에도 마지막 종가 조회 가능)
            self.ocx.dynamicCall(
                "SetInputValue(QString, QString)",
                "종목코드",
                stock_code
            )
            
            self.request_event_loop = QEventLoop()
            ret = self.ocx.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "주식기본정보요청",
                "OPT10001",
                0,
                "2002"
            )
            
            if ret == 0:
                self.request_event_loop.exec_()
                price_data = self.data_cache.get('current_price', {})
                price = price_data.get('current_price')
                
                if price:
                    # 시간외 거래 시간 체크 (선택적)
                    from config import Config
                    from datetime import datetime
                    current_time = datetime.now().time()
                    
                    if Config.ENABLE_AFTER_HOURS_TRADING:
                        after_hours_start = datetime.strptime(Config.MARKET_AFTER_HOURS_START, "%H:%M").time()
                        after_hours_end = datetime.strptime(Config.MARKET_AFTER_HOURS_END, "%H:%M").time()
                        
                        if after_hours_start <= current_time <= after_hours_end:
                            log.debug(f"⚡ 시간외 가격 조회: {stock_code} = {price:,}원")
                
                return price
            else:
                log.error(f"현재가 조회 실패: {ret}")
                return None
                
        except Exception as e:
            log.error(f"현재가 조회 중 오류: {e}")
            return None
    
    def get_top_traded_stocks(self, count: int = 100, use_continuous: bool = True, max_continuous: int = 3) -> List[Dict]:
        """
        당일 거래대금 상위 종목 조회 (연속조회 지원)
        
        Args:
            count: 기본 조회 수 (1회당 최대 약 100개)
            use_continuous: 연속조회 사용 여부 (True: 더 많은 종목 조회)
            max_continuous: 최대 연속조회 횟수 (1-5 권장, 기본 3)
        
        Returns:
            거래대금 상위 종목 리스트 (최대 count * max_continuous 개)
            [{'code': '005930', 'name': '삼성전자', 'price': 75000, 
              'change_rate': 2.5, 'volume': 15000000, 'trade_value': 1125000000000}, ...]
        """
        all_stocks = []
        prev_next = 0  # 0: 첫 조회, 2: 연속조회
        
        log.info(f"📊 거래대금 상위 종목 조회 시작 (연속조회: {'사용' if use_continuous else '미사용'})")
        
        for iteration in range(max_continuous if use_continuous else 1):
            try:
                # API 제한 준수
                self._wait_for_request()
                
                if iteration > 0:
                    log.info(f"   🔄 연속조회 {iteration + 1}/{max_continuous}")
                
                # OPT10023: 거래량상위요청 (거래대금 기준)
                self.ocx.dynamicCall(
                    "SetInputValue(QString, QString)",
                    "시장구분",
                    "000"  # 000: 코스피, 001: 코스닥
                )
                self.ocx.dynamicCall(
                    "SetInputValue(QString, QString)",
                    "정렬구분",
                    "1"  # 0: 거래량, 1: 거래대금
                )
                self.ocx.dynamicCall(
                    "SetInputValue(QString, QString)",
                    "관리종목포함",
                    "0"  # 0: 미포함
                )
                self.ocx.dynamicCall(
                    "SetInputValue(QString, QString)",
                    "거래량구분",
                    "0"  # 0: 전체
                )
                
                self.request_event_loop = QEventLoop()
                ret = self.ocx.dynamicCall(
                    "CommRqData(QString, QString, int, QString)",
                    "거래대금상위요청",
                    "OPT10023",
                    prev_next,  # 🆕 연속조회 파라미터
                    "2003"
                )
                
                if ret == 0:
                    self.request_event_loop.exec_()
                    batch_stocks = self.data_cache.get('top_traded_stocks', [])
                    
                    if batch_stocks:
                        all_stocks.extend(batch_stocks)
                        log.success(f"   ✅ 조회 성공: {len(batch_stocks)}개 (누적: {len(all_stocks)}개)")
                        
                        # 🆕 연속 데이터 확인 (OnReceiveTrData에서 설정)
                        if use_continuous and self.last_prev_next == "2":
                            prev_next = 2  # 다음 조회는 연속조회
                            log.info(f"   📋 연속 데이터 있음 - 다음 배치 조회 예정")
                        else:
                            log.info(f"   📋 연속 데이터 없음 - 조회 종료")
                            break
                    else:
                        log.warning("   ⚠️  조회 결과가 비어있습니다.")
                        break
                else:
                    # 에러 코드 해석
                    error_msg = {
                        -200: "시세 과부하",
                        -201: "조회 과부하",
                        -202: "조회 과부하 (잠시 후 재시도)",
                    }.get(ret, f"알 수 없는 오류 ({ret})")
                    log.error(f"   ❌ TR 요청 실패: {error_msg}")
                    break
                    
            except Exception as e:
                log.error(f"거래대금 상위 종목 조회 중 오류 (반복 {iteration + 1}/{max_continuous}): {e}")
                import traceback
                log.error(f"상세: {traceback.format_exc()}")
                break
        
        # 최종 결과
        if all_stocks:
            log.success(f"✅ 거래대금 상위 종목 조회 완료: 총 {len(all_stocks)}개")
            # 요청한 개수만큼 반환 (초과분 제거)
            result = all_stocks[:count * max_continuous]
            log.info(f"   📋 반환: {len(result)}개 종목")
            return result
        else:
            log.warning("⚠️  조회 결과 없음")
            return []
    
    def buy_order(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "00",
        max_retries: int = 3,
        priority: str = "일반"
    ) -> Optional[str]:
        """
        매수 주문 (재시도 로직 포함)
        
        Args:
            stock_code: 종목코드
            quantity: 수량
            price: 가격 (0: 시장가)
            order_type: 주문타입 (00: 지정가, 03: 시장가)
            max_retries: 최대 재시도 횟수
            priority: 주문 우선순위 ("일반", "손절", "익절")
        
        Returns:
            주문번호 또는 None
        """
        # 주문 제한 체크
        if not self._wait_for_order(order_type=priority):
            log.error(f"❌ 주문 제한 초과 - 매수 주문 불가: {stock_code}")
            return None
        
        for attempt in range(max_retries):
            try:
                if price == 0:
                    order_type = "03"  # 시장가
                
                # SendOrder 파라미터: 계좌번호는 10자리만 전달 (비밀번호는 로그인 시 계좌비밀번호 등록에서 처리)
                # 마지막 파라미터는 "원주문번호"로 신규주문은 빈 문자열
                log.debug(f"SendOrder 호출: 계좌번호={self.account_number}, 종목={stock_code}, 수량={quantity}, 가격={price}")
                
                ret = self.ocx.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    ["매수", "0101", self.account_number, 1, stock_code, quantity, price, order_type, ""]
                )
                
                if ret == 0:
                    log.success(
                        f"✅ 매수 주문 전송 성공: {stock_code} {quantity}주 @ "
                        f"{price:,}원 (시도: {attempt + 1}/{max_retries})"
                    )
                    return "주문전송완료"
                else:
                    error_msg = self.ERROR_CODES.get(ret, f"알 수 없는 오류 ({ret})")
                    log.error(f"❌ 매수 주문 실패: {error_msg} - {stock_code}")
                    
                    # 재시도 가능한 오류인지 확인
                    if ret in [-308, -307]:  # 주문 가능 수량 초과 등
                        log.error("   재시도 불가능한 오류 - 중단")
                        return None
                    
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 0.5  # 0.5초, 1초, 1.5초...
                        log.warning(f"   ⏳ {wait_time}초 후 재시도...")
                        time.sleep(wait_time)
                    else:
                        log.error(f"   ⛔ 최대 재시도 횟수 초과 ({max_retries}회)")
                        return None
                    
            except Exception as e:
                log.error(f"❌ 매수 주문 중 오류 (시도: {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5
                    log.warning(f"   ⏳ {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    log.error(f"   ⛔ 최대 재시도 횟수 초과 ({max_retries}회)")
                    return None
        
        return None
    
    def sell_order(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "00",
        max_retries: int = 3,
        priority: str = "일반"
    ) -> Optional[str]:
        """
        매도 주문 (재시도 로직 포함)
        
        Args:
            stock_code: 종목코드
            quantity: 수량
            price: 가격 (0: 시장가)
            order_type: 주문타입 (00: 지정가, 03: 시장가)
            max_retries: 최대 재시도 횟수
            priority: 주문 우선순위 ("일반", "손절", "익절")
        
        Returns:
            주문번호 또는 None
        """
        # 주문 제한 체크
        if not self._wait_for_order(order_type=priority):
            log.error(f"❌ 주문 제한 초과 - 매도 주문 불가: {stock_code}")
            return None
        
        for attempt in range(max_retries):
            try:
                if price == 0:
                    order_type = "03"  # 시장가
                
                # SendOrder 파라미터: 계좌번호는 10자리만 전달 (비밀번호는 로그인 시 계좌비밀번호 등록에서 처리)
                # 마지막 파라미터는 "원주문번호"로 신규주문은 빈 문자열
                log.debug(f"SendOrder 호출: 계좌번호={self.account_number}, 종목={stock_code}, 수량={quantity}, 가격={price}")
                
                ret = self.ocx.dynamicCall(
                    "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                    ["매도", "0101", self.account_number, 2, stock_code, quantity, price, order_type, ""]
                )
                
                if ret == 0:
                    log.success(
                        f"✅ 매도 주문 전송 성공: {stock_code} {quantity}주 @ "
                        f"{price:,}원 (시도: {attempt + 1}/{max_retries})"
                    )
                    return "주문전송완료"
                else:
                    error_msg = self.ERROR_CODES.get(ret, f"알 수 없는 오류 ({ret})")
                    log.error(f"❌ 매도 주문 실패: {error_msg} - {stock_code}")
                    
                    # 재시도 불가능한 오류 체크
                    if ret in [-308, -307]:  # 잔고 부족 등
                        log.error("   재시도 불가능한 오류 - 중단")
                        return None
                    
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 0.5
                        log.warning(f"   ⏳ {wait_time}초 후 재시도...")
                        time.sleep(wait_time)
                    else:
                        log.error(f"   ⛔ 최대 재시도 횟수 초과 ({max_retries}회)")
                        return None
                    
            except Exception as e:
                log.error(f"❌ 매도 주문 중 오류 (시도: {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5
                    log.warning(f"   ⏳ {wait_time}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    log.error(f"   ⛔ 최대 재시도 횟수 초과 ({max_retries}회)")
                    return None
        
        return None
    
    def set_real_data_callback(self, callback: Callable):
        """
        실시간 데이터 콜백 설정
        
        Args:
            callback: 콜백 함수 (stock_code, price_data)
        """
        self.callbacks['real_data'] = callback
        log.info("실시간 데이터 콜백 설정 완료")
    
    def register_real_data(self, stock_codes: List[str]):
        """
        실시간 시세 등록 (과부하 방지)
        
        Args:
            stock_codes: 종목코드 리스트
            
        Note:
            - 한 번에 최대 100종목까지 등록 가능
            - 과부하 방지를 위해 API 호출 제한 적용
        """
        try:
            from config import Config
            batch_size = Config.REAL_DATA_BATCH_SIZE
            
            # 과부하 방지: 너무 많은 종목은 분할 등록
            if len(stock_codes) > batch_size:
                log.warning(f"⚠️  종목 수가 많아 분할 등록: {len(stock_codes)}개 → {batch_size}개씩")
                for i in range(0, len(stock_codes), batch_size):
                    batch = stock_codes[i:i+batch_size]
                    log.info(f"   배치 {i//batch_size + 1}: {len(batch)}개 종목 등록 중...")
                    self.register_real_data(batch)
                    time.sleep(2.0)  # 배치 간 충분한 대기
                log.success(f"✅ 전체 {len(stock_codes)}개 종목 분할 등록 완료")
                return
            
            # API 호출 제한 준수
            self._wait_for_request()
            
            screen_no = "1000"
            # 🆕 호가 FID 추가: 거래량(13), 매도호가총잔량(121), 매수호가총잔량(125), 체결강도(228)
            fids = "9001;10;11;12;13;27;28;121;125;228"  # 현재가, 등락률, 거래량, 호가 데이터
            
            code_list = ";".join(stock_codes)
            
            ret = self.ocx.dynamicCall(
                "SetRealReg(QString, QString, QString, QString)",
                screen_no,
                code_list,
                fids,
                "0"
            )
            
            if ret >= 0:
                log.success(f"실시간 시세 등록 완료: {len(stock_codes)}개 종목")
            else:
                log.error(f"실시간 시세 등록 실패: {ret}")
                
        except Exception as e:
            log.error(f"실시간 시세 등록 중 오류: {e}")
    
    def _on_receive_tr_data(
        self,
        screen_no,
        rqname,
        trcode,
        recordname,
        prev_next,
        data_len,
        err_code,
        msg,
        splm_msg
    ):
        """TR 데이터 수신 이벤트"""
        try:
            # 🆕 연속조회 지원: prev_next 값 저장
            # "0" = 연속 데이터 없음 (마지막 페이지)
            # "2" = 연속 데이터 있음 (다음 페이지 요청 가능)
            self.last_prev_next = prev_next
            
            if rqname == "예수금상세현황요청":
                cash = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    trcode, rqname, 0, "예수금"
                )
                self.data_cache['balance'] = {
                    'cash': abs(int(cash)),
                }
            
            elif rqname == "계좌평가잔고내역요청":
                count = self.ocx.dynamicCall(
                    "GetRepeatCnt(QString, QString)",
                    trcode, rqname
                )
                holdings = []
                for i in range(count):
                    stock_code = self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "종목번호"
                    ).strip()
                    stock_name = self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "종목명"
                    ).strip()
                    quantity = int(self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "보유수량"
                    ))
                    buy_price = int(self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "매입가"
                    ))
                    current_price = int(self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "현재가"
                    ))
                    
                    holdings.append({
                        'code': stock_code,
                        'name': stock_name,
                        'quantity': quantity,
                        'buy_price': buy_price,
                        'current_price': abs(current_price),
                    })
                
                self.data_cache['holdings'] = holdings
            
            elif rqname == "주식기본정보요청":
                current_price = self.ocx.dynamicCall(
                    "GetCommData(QString, QString, int, QString)",
                    trcode, rqname, 0, "현재가"
                )
                self.data_cache['current_price'] = {
                    'current_price': abs(int(current_price))
                }
            
            elif rqname == "거래대금상위요청":
                count = self.ocx.dynamicCall(
                    "GetRepeatCnt(QString, QString)",
                    trcode, rqname
                )
                top_stocks = []
                for i in range(count):
                    stock_code = self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "종목코드"
                    ).strip()
                    stock_name = self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "종목명"
                    ).strip()
                    current_price = self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "현재가"
                    ).strip()
                    change_rate = self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "등락률"
                    ).strip()
                    volume = self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "거래량"
                    ).strip()
                    trade_value = self.ocx.dynamicCall(
                        "GetCommData(QString, QString, int, QString)",
                        trcode, rqname, i, "거래대금"
                    ).strip()
                    
                    # 빈 값 체크 및 파싱
                    if stock_code and stock_name and current_price:
                        try:
                            top_stocks.append({
                                'code': stock_code,
                                'name': stock_name,
                                'price': abs(int(current_price)),
                                'change_rate': float(change_rate) if change_rate else 0.0,
                                'volume': int(volume) if volume else 0,
                                'trade_value': int(trade_value) if trade_value else 0,
                            })
                        except ValueError:
                            # 파싱 오류 시 해당 종목 건너뛰기
                            continue
                
                self.data_cache['top_traded_stocks'] = top_stocks
            
        except Exception as e:
            log.error(f"TR 데이터 처리 중 오류: {e}")
        
        finally:
            if self.request_event_loop:
                self.request_event_loop.exit()
        
        return 0  # 🆕 PyQt5 COM 이벤트 핸들러는 정수 반환 필요
    
    def _on_receive_real_data(self, stock_code, real_type, real_data):
        """실시간 데이터 수신 이벤트"""
        try:
            # 실시간 데이터 수신 로그 (디버깅용)
            if not hasattr(self, '_real_data_count'):
                self._real_data_count = {}
            if stock_code not in self._real_data_count:
                self._real_data_count[stock_code] = 0
            self._real_data_count[stock_code] += 1
            
            # 처음 5번만 로그 출력
            if self._real_data_count[stock_code] <= 5:
                log.info(f"🔔 실시간 데이터 수신: {stock_code} | 유형: {real_type} [수신 #{self._real_data_count[stock_code]}]")
            
            if real_type == "주식체결":
                current_price = self.ocx.dynamicCall(
                    "GetCommRealData(QString, int)",
                    stock_code, 10
                )
                change_rate = self.ocx.dynamicCall(
                    "GetCommRealData(QString, int)",
                    stock_code, 12
                )
                volume = self.ocx.dynamicCall(
                    "GetCommRealData(QString, int)",
                    stock_code, 13
                )
                
                price_data = {
                    'stock_code': stock_code,
                    'current_price': abs(int(current_price)),
                    'change_rate': float(change_rate),
                    'volume': int(volume),
                }
                
                # 처음 3번만 상세 로그
                if self._real_data_count[stock_code] <= 3:
                    log.info(
                        f"   📊 가격: {price_data['current_price']:,}원 | "
                        f"등락률: {price_data['change_rate']:+.2f}% | "
                        f"거래량: {price_data['volume']:,}"
                    )
                
                # 콜백 호출
                if 'real_data' in self.callbacks:
                    self.callbacks['real_data'](stock_code, price_data)
                else:
                    if self._real_data_count[stock_code] == 1:
                        log.warning(f"⚠️  실시간 데이터 콜백이 설정되지 않았습니다: {stock_code}")
            
            elif real_type == "주식호가잔량":
                # 🆕 호가 데이터 수신 (선제적 매수 판단)
                try:
                    # 매도호가총잔량(121), 매수호가총잔량(125), 체결강도(228)
                    ask_volume = self.ocx.dynamicCall(
                        "GetCommRealData(QString, int)",
                        stock_code, 121
                    )
                    bid_volume = self.ocx.dynamicCall(
                        "GetCommRealData(QString, int)",
                        stock_code, 125
                    )
                    execution_strength = self.ocx.dynamicCall(
                        "GetCommRealData(QString, int)",
                        stock_code, 228
                    )
                    
                    order_book_data = {
                        'bid_volume': abs(int(bid_volume)) if bid_volume else 0,
                        'ask_volume': abs(int(ask_volume)) if ask_volume else 0,
                        'execution_strength': abs(int(execution_strength)) if execution_strength else 0
                    }
                    
                    # 호가 데이터 콜백 호출
                    if 'order_book_data' in self.callbacks:
                        self.callbacks['order_book_data'](stock_code, order_book_data)
                    
                except Exception as e:
                    log.debug(f"호가 데이터 파싱 오류 ({stock_code}): {e}")
            
            elif real_type in ["주식시간외호가", "ECN주식호가잔량"]:
                # 🆕 시간외 호가 데이터 수신
                try:
                    # 시간외 현재가 조회 (FID 10)
                    current_price = self.ocx.dynamicCall(
                        "GetCommRealData(QString, int)",
                        stock_code, 10
                    )
                    
                    if current_price:
                        price_data = {
                            'stock_code': stock_code,
                            'current_price': abs(int(current_price)),
                            'change_rate': 0.0,  # 시간외는 등락률 정보가 제한적
                            'volume': 0,
                            'is_after_hours': True  # 시간외 데이터 표시
                        }
                        
                        # 처음 3번만 상세 로그
                        if self._real_data_count[stock_code] <= 3:
                            log.info(
                                f"   ⚡ 시간외 가격: {price_data['current_price']:,}원"
                            )
                        
                        # 콜백 호출 (정규장과 동일한 콜백 사용)
                        if 'real_data' in self.callbacks:
                            self.callbacks['real_data'](stock_code, price_data)
                    
                except Exception as e:
                    log.debug(f"시간외 호가 데이터 파싱 오류 ({stock_code}): {e}")
            
            elif real_type == "주식시간외체결":
                # 🆕 시간외 체결 데이터 수신
                try:
                    current_price = self.ocx.dynamicCall(
                        "GetCommRealData(QString, int)",
                        stock_code, 10
                    )
                    volume = self.ocx.dynamicCall(
                        "GetCommRealData(QString, int)",
                        stock_code, 13
                    )
                    
                    price_data = {
                        'stock_code': stock_code,
                        'current_price': abs(int(current_price)),
                        'change_rate': 0.0,
                        'volume': int(volume) if volume else 0,
                        'is_after_hours': True
                    }
                    
                    # 처음 3번만 상세 로그
                    if self._real_data_count[stock_code] <= 3:
                        log.info(
                            f"   ⚡ 시간외 체결: {price_data['current_price']:,}원 | "
                            f"거래량: {price_data['volume']:,}"
                        )
                    
                    # 콜백 호출
                    if 'real_data' in self.callbacks:
                        self.callbacks['real_data'](stock_code, price_data)
                    
                except Exception as e:
                    log.debug(f"시간외 체결 데이터 파싱 오류 ({stock_code}): {e}")
            
            else:
                # 다른 유형의 실시간 데이터
                if self._real_data_count[stock_code] <= 2:
                    log.debug(f"   💡 지원하지 않는 실시간 데이터 유형: {real_type}")
                    
        except Exception as e:
            log.error(f"실시간 데이터 처리 중 오류: {e}")
            import traceback
            log.error(f"상세: {traceback.format_exc()}")
        
        return 0  # 🆕 PyQt5 COM 이벤트 핸들러는 정수 반환 필요
    
    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 데이터 수신 이벤트"""
        try:
            if gubun == "0":  # 주문체결
                order_status = self.ocx.dynamicCall("GetChejanData(int)", 913)
                stock_code = self.ocx.dynamicCall("GetChejanData(int)", 9001).strip()
                order_quantity = int(self.ocx.dynamicCall("GetChejanData(int)", 900))
                order_price = int(self.ocx.dynamicCall("GetChejanData(int)", 901))
                
                log.info(f"체결 데이터: {stock_code} {order_quantity}주 @ {order_price}원 [{order_status}]")
                
        except Exception as e:
            log.error(f"체결 데이터 처리 중 오류: {e}")
        
        return 0  # 🆕 PyQt5 COM 이벤트 핸들러는 정수 반환 필요
    
    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신 이벤트"""
        log.info(f"키움 메시지: {msg}")
        return 0  # 🆕 PyQt5 COM 이벤트 핸들러는 정수 반환 필요
    
    def disconnect(self):
        """연결 종료"""
        try:
            self.ocx.dynamicCall("CommTerminate()")
            self.is_connected = False
            log.info("키움 API 연결 종료")
        except Exception as e:
            log.error(f"연결 종료 중 오류: {e}")


# 테스트 코드
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    kiwoom = KiwoomAPI()
    
    if kiwoom.login():
        log.info("로그인 테스트 성공")
        
        # 잔고 조회 테스트
        balance = kiwoom.get_balance()
        log.info(f"잔고: {balance}")
        
        # 보유 종목 조회 테스트
        holdings = kiwoom.get_holdings()
        log.info(f"보유 종목 수: {len(holdings)}")
        
        kiwoom.disconnect()
    else:
        log.error("로그인 테스트 실패")
    
    sys.exit()


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
    
    def __init__(self):
        """초기화"""
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.is_connected = False
        self.account_number = None
        self.callbacks = {}
        
        # 이벤트 루프
        self.login_event_loop = None
        self.request_event_loop = None
        
        # TR 요청 제한 관리
        self.last_request_time = 0
        self.request_delay = 0.2  # 초당 5건 제한 (0.2초 간격)
        
        # 데이터 저장
        self.data_cache = {}
        
        # 시그널 연결
        self._connect_signals()
        
        log.info("키움 API 초기화 완료")
    
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
        
        Returns:
            로그인 성공 여부
        """
        try:
            log.info("키움 API 로그인 시도...")
            self.login_event_loop = QEventLoop()
            self.ocx.dynamicCall("CommConnect()")
            self.login_event_loop.exec_()
            
            if self.is_connected:
                # 계좌번호 조회
                account_list = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
                accounts = account_list.split(';')[:-1]  # 마지막 빈 문자열 제거
                
                if Config.USE_SIMULATION:
                    # 모의투자 계좌 찾기 (8로 시작)
                    sim_accounts = [acc for acc in accounts if acc.startswith('8')]
                    if sim_accounts:
                        self.account_number = sim_accounts[0]
                        log.success(f"모의투자 계좌 로그인 성공: {self.account_number}")
                    else:
                        log.error("모의투자 계좌를 찾을 수 없습니다.")
                        return False
                else:
                    # 실계좌 (8로 시작하지 않는 계좌)
                    real_accounts = [acc for acc in accounts if not acc.startswith('8')]
                    if real_accounts:
                        self.account_number = real_accounts[0]
                        log.success(f"실계좌 로그인 성공: {self.account_number}")
                    else:
                        log.error("실계좌를 찾을 수 없습니다.")
                        return False
                
                # 사용자 정보 출력
                user_name = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_NAME")
                log.info(f"사용자: {user_name}")
                
                return True
            else:
                log.error("로그인 실패")
                return False
                
        except Exception as e:
            log.error(f"로그인 중 오류 발생: {e}")
            return False
    
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
    
    def _wait_for_request(self):
        """TR 요청 제한 준수 (초당 5건)"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        
        self.last_request_time = time.time()
    
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
    
    def get_current_price(self, stock_code: str) -> Optional[int]:
        """
        현재가 조회
        
        Args:
            stock_code: 종목코드
        
        Returns:
            현재가 또는 None
        """
        try:
            self._wait_for_request()
            
            # OPT10001: 주식기본정보요청
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
                return price_data.get('current_price')
            else:
                log.error(f"현재가 조회 실패: {ret}")
                return None
                
        except Exception as e:
            log.error(f"현재가 조회 중 오류: {e}")
            return None
    
    def get_top_traded_stocks(self, count: int = 100) -> List[Dict]:
        """
        당일 거래대금 상위 종목 조회
        
        Args:
            count: 조회할 종목 수 (최대 100)
        
        Returns:
            거래대금 상위 종목 리스트
            [{'code': '005930', 'name': '삼성전자', 'price': 75000, 
              'change_rate': 2.5, 'volume': 15000000, 'trade_value': 1125000000000}, ...]
        """
        try:
            self._wait_for_request()
            
            # OPT10023: 거래량상위요청 (거래대금 기준으로 정렬 가능)
            self.ocx.dynamicCall(
                "SetInputValue(QString, QString)",
                "시장구분",
                "000"  # 000: 코스피, 001: 코스닥, 전체
            )
            self.ocx.dynamicCall(
                "SetInputValue(QString, QString)",
                "정렬구분",
                "1"  # 0: 거래량, 1: 거래대금
            )
            self.ocx.dynamicCall(
                "SetInputValue(QString, QString)",
                "관리종목포함",
                "0"  # 0: 미포함, 1: 포함
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
                0,
                "2003"
            )
            
            if ret == 0:
                self.request_event_loop.exec_()
                top_stocks = self.data_cache.get('top_traded_stocks', [])
                # 요청한 개수만큼만 반환
                return top_stocks[:count]
            else:
                log.error(f"거래대금 상위 종목 조회 실패: {ret}")
                return []
                
        except Exception as e:
            log.error(f"거래대금 상위 종목 조회 중 오류: {e}")
            return []
    
    def buy_order(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "00"
    ) -> Optional[str]:
        """
        매수 주문
        
        Args:
            stock_code: 종목코드
            quantity: 수량
            price: 가격 (0: 시장가)
            order_type: 주문타입 (00: 지정가, 03: 시장가)
        
        Returns:
            주문번호 또는 None
        """
        try:
            if price == 0:
                order_type = "03"  # 시장가
            
            ret = self.ocx.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                ["매수", "0101", self.account_number, 1, stock_code, quantity, price, order_type, ""]
            )
            
            if ret == 0:
                log.success(f"매수 주문 전송 성공: {stock_code} {quantity}주 @ {price}원")
                return "주문전송완료"
            else:
                log.error(f"매수 주문 실패: {ret}")
                return None
                
        except Exception as e:
            log.error(f"매수 주문 중 오류: {e}")
            return None
    
    def sell_order(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: str = "00"
    ) -> Optional[str]:
        """
        매도 주문
        
        Args:
            stock_code: 종목코드
            quantity: 수량
            price: 가격 (0: 시장가)
            order_type: 주문타입 (00: 지정가, 03: 시장가)
        
        Returns:
            주문번호 또는 None
        """
        try:
            if price == 0:
                order_type = "03"  # 시장가
            
            ret = self.ocx.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                ["매도", "0101", self.account_number, 2, stock_code, quantity, price, order_type, ""]
            )
            
            if ret == 0:
                log.success(f"매도 주문 전송 성공: {stock_code} {quantity}주 @ {price}원")
                return "주문전송완료"
            else:
                log.error(f"매도 주문 실패: {ret}")
                return None
                
        except Exception as e:
            log.error(f"매도 주문 중 오류: {e}")
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
        실시간 시세 등록
        
        Args:
            stock_codes: 종목코드 리스트
        """
        try:
            screen_no = "1000"
            fids = "9001;10;11;12;27;28"  # 현재가, 등락률, 거래량 등
            
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
    
    def _on_receive_real_data(self, stock_code, real_type, real_data):
        """실시간 데이터 수신 이벤트"""
        try:
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
                
                # 콜백 호출
                if 'real_data' in self.callbacks:
                    self.callbacks['real_data'](stock_code, price_data)
                    
        except Exception as e:
            log.error(f"실시간 데이터 처리 중 오류: {e}")
    
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
    
    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신 이벤트"""
        log.info(f"키움 메시지: {msg}")
    
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


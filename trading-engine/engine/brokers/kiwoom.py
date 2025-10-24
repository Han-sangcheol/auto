"""
키움 증권 브로커 어댑터

키움 OpenAPI를 BaseBroker 인터페이스로 래핑합니다.

[파일 역할]
키움증권 Open API+와 통신하는 Python 브로커 어댑터입니다.
BaseBroker 인터페이스를 구현하여 다른 증권사와 통일된 인터페이스를 제공합니다.

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
- 32-bit Python만 지원
"""

import sys
import time
from typing import List, Dict, Optional, Callable
from PyQt5.QtWidgets import QApplication
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop
from loguru import logger
from .base import BaseBroker


class KiwoomBroker(BaseBroker):
    """키움 증권 브로커 어댑터"""
    
    def __init__(self, config=None):
        """
        초기화
        
        Args:
            config: 설정 객체 (선택적)
        """
        logger.info("KiwoomBroker 초기화")
        
        self.config = config
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.is_connected = False
        self.account_number = None
        self.callbacks = {}
        
        # 이벤트 루프
        self.login_event_loop = None
        self.request_event_loop = None
        
        # TR 요청 제한 관리
        self.last_request_time = 0
        self.request_delay = 0.2  # 초당 5건 제한
        
        # 데이터 캐시
        self.data_cache = {}
        
        # 시그널 연결
        self._connect_signals()
        
        logger.success("키움 API 초기화 완료")
    
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
            logger.info("키움 API 로그인 시도...")
            self.login_event_loop = QEventLoop()
            self.ocx.dynamicCall("CommConnect()")
            self.login_event_loop.exec_()
            
            if self.is_connected:
                # 계좌번호 조회
                account_list = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
                accounts = account_list.split(';')[:-1]
                
                # 모의투자 계좌 우선
                use_simulation = getattr(self.config, 'USE_SIMULATION', True) if self.config else True
                
                if use_simulation:
                    sim_accounts = [acc for acc in accounts if acc.startswith('8')]
                    if sim_accounts:
                        self.account_number = sim_accounts[0]
                        logger.success(f"모의투자 계좌 로그인 성공: {self.account_number}")
                    else:
                        logger.error("모의투자 계좌를 찾을 수 없습니다.")
                        return False
                else:
                    real_accounts = [acc for acc in accounts if not acc.startswith('8')]
                    if real_accounts:
                        self.account_number = real_accounts[0]
                        logger.success(f"실계좌 로그인 성공: {self.account_number}")
                    else:
                        logger.error("실계좌를 찾을 수 없습니다.")
                        return False
                
                user_name = self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_NAME")
                logger.info(f"사용자: {user_name}")
                
                return True
            else:
                logger.error("로그인 실패")
                return False
                
        except Exception as e:
            logger.error(f"로그인 중 오류 발생: {e}")
            return False
    
    def _on_event_connect(self, err_code):
        """로그인 이벤트 처리"""
        if err_code == 0:
            self.is_connected = True
            logger.info("로그인 연결 성공")
        else:
            self.is_connected = False
            logger.error(f"로그인 연결 실패: {err_code}")
        
        if self.login_event_loop:
            self.login_event_loop.exit()
    
    def _wait_for_request(self):
        """TR 요청 제한 준수 (초당 5건)"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        
        self.last_request_time = time.time()
    
    def get_account_info(self) -> dict:
        """계좌 정보 조회"""
        return {
            "account_number": self.account_number or "모의투자",
            "name": self.ocx.dynamicCall("GetLoginInfo(QString)", "USER_NAME") if self.is_connected else "사용자",
            "balance": self.get_balance()
        }
    
    def get_balance(self) -> int:
        """예수금 조회"""
        try:
            self._wait_for_request()
            
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
            
            self.request_event_loop = QEventLoop()
            ret = self.ocx.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "예수금상세현황요청", "OPW00001", 0, "2000"
            )
            
            if ret == 0:
                self.request_event_loop.exec_()
                balance = self.data_cache.get('balance', {})
                return balance.get('cash', 0)
            else:
                logger.error(f"잔고 조회 실패: {ret}")
                return 0
                
        except Exception as e:
            logger.error(f"잔고 조회 중 오류: {e}")
            return 0
    
    def get_positions(self) -> List[Dict]:
        """보유 포지션 조회"""
        try:
            self._wait_for_request()
            
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
            
            self.request_event_loop = QEventLoop()
            ret = self.ocx.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "계좌평가잔고내역요청", "OPW00018", 0, "2001"
            )
            
            if ret == 0:
                self.request_event_loop.exec_()
                return self.data_cache.get('holdings', [])
            else:
                logger.error(f"보유종목 조회 실패: {ret}")
                return []
                
        except Exception as e:
            logger.error(f"보유종목 조회 중 오류: {e}")
            return []
    
    def buy(self, stock_code: str, quantity: int, price: Optional[int] = None) -> dict:
        """매수 주문"""
        try:
            order_type = "03" if price is None or price == 0 else "00"
            price = price or 0
            
            ret = self.ocx.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                ["매수", "0101", self.account_number, 1, stock_code, quantity, price, order_type, ""]
            )
            
            if ret == 0:
                logger.success(f"매수 주문 전송 성공: {stock_code} {quantity}주 @ {price}원")
                return {"order_id": "주문전송완료", "status": "pending"}
            else:
                logger.error(f"매수 주문 실패: {ret}")
                return {"order_id": None, "status": "failed"}
                
        except Exception as e:
            logger.error(f"매수 주문 중 오류: {e}")
            return {"order_id": None, "status": "error"}
    
    def sell(self, stock_code: str, quantity: int, price: Optional[int] = None) -> dict:
        """매도 주문"""
        try:
            order_type = "03" if price is None or price == 0 else "00"
            price = price or 0
            
            ret = self.ocx.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                ["매도", "0101", self.account_number, 2, stock_code, quantity, price, order_type, ""]
            )
            
            if ret == 0:
                logger.success(f"매도 주문 전송 성공: {stock_code} {quantity}주 @ {price}원")
                return {"order_id": "주문전송완료", "status": "pending"}
            else:
                logger.error(f"매도 주문 실패: {ret}")
                return {"order_id": None, "status": "failed"}
                
        except Exception as e:
            logger.error(f"매도 주문 중 오류: {e}")
            return {"order_id": None, "status": "error"}
    
    def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        logger.info(f"주문 취소: {order_id}")
        # TODO: 실제 취소 로직 구현
        return True
    
    def get_stock_info(self, stock_code: str) -> dict:
        """종목 정보 조회"""
        try:
            self._wait_for_request()
            
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
            
            self.request_event_loop = QEventLoop()
            ret = self.ocx.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "주식기본정보요청", "OPT10001", 0, "2002"
            )
            
            if ret == 0:
                self.request_event_loop.exec_()
                price_data = self.data_cache.get('current_price', {})
                return {
                    "code": stock_code,
                    "name": "종목명",
                    "price": price_data.get('current_price', 0)
                }
            else:
                logger.error(f"종목 정보 조회 실패: {ret}")
                return {"code": stock_code, "name": "", "price": 0}
                
        except Exception as e:
            logger.error(f"종목 정보 조회 중 오류: {e}")
            return {"code": stock_code, "name": "", "price": 0}
    
    def register_realtime(self, stock_codes: List[str]):
        """실시간 데이터 수신 등록"""
        try:
            screen_no = "1000"
            fids = "9001;10;11;12;27;28"
            code_list = ";".join(stock_codes)
            
            ret = self.ocx.dynamicCall(
                "SetRealReg(QString, QString, QString, QString)",
                screen_no, code_list, fids, "0"
            )
            
            if ret >= 0:
                logger.success(f"실시간 시세 등록 완료: {len(stock_codes)}개 종목")
            else:
                logger.error(f"실시간 시세 등록 실패: {ret}")
                
        except Exception as e:
            logger.error(f"실시간 시세 등록 중 오류: {e}")
    
    def unregister_realtime(self, stock_codes: List[str]):
        """실시간 데이터 수신 해제"""
        logger.info(f"실시간 해제: {stock_codes}")
        # TODO: 실제 해제 로직 구현
    
    def set_real_data_callback(self, callback: Callable):
        """실시간 데이터 콜백 설정"""
        self.callbacks['real_data'] = callback
        logger.info("실시간 데이터 콜백 설정 완료")
    
    def get_top_traded_stocks(self, count: int = 100) -> List[Dict]:
        """거래대금 상위 종목 조회"""
        try:
            self._wait_for_request()
            
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "시장구분", "000")
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "정렬구분", "1")
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "관리종목포함", "0")
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "거래량구분", "0")
            
            self.request_event_loop = QEventLoop()
            ret = self.ocx.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                "거래대금상위요청", "OPT10023", 0, "2003"
            )
            
            if ret == 0:
                self.request_event_loop.exec_()
                top_stocks = self.data_cache.get('top_traded_stocks', [])
                return top_stocks[:count]
            else:
                logger.error(f"거래대금 상위 종목 조회 실패: {ret}")
                return []
                
        except Exception as e:
            logger.error(f"거래대금 상위 종목 조회 중 오류: {e}")
            return []
    
    def _on_receive_tr_data(self, screen_no, rqname, trcode, recordname, prev_next, data_len, err_code, msg, splm_msg):
        """TR 데이터 수신 이벤트"""
        try:
            if rqname == "예수금상세현황요청":
                cash = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "예수금")
                self.data_cache['balance'] = {'cash': abs(int(cash))}
            
            elif rqname == "계좌평가잔고내역요청":
                count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
                holdings = []
                for i in range(count):
                    stock_code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목번호").strip()
                    stock_name = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명").strip()
                    quantity = int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "보유수량"))
                    buy_price = int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "매입가"))
                    current_price = int(self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가"))
                    
                    holdings.append({
                        'code': stock_code,
                        'name': stock_name,
                        'quantity': quantity,
                        'buy_price': buy_price,
                        'current_price': abs(current_price),
                    })
                
                self.data_cache['holdings'] = holdings
            
            elif rqname == "주식기본정보요청":
                current_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, 0, "현재가")
                self.data_cache['current_price'] = {'current_price': abs(int(current_price))}
            
            elif rqname == "거래대금상위요청":
                count = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
                top_stocks = []
                for i in range(count):
                    stock_code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목코드").strip()
                    stock_name = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목명").strip()
                    current_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "현재가").strip()
                    change_rate = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "등락률").strip()
                    volume = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래량").strip()
                    trade_value = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "거래대금").strip()
                    
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
                            continue
                
                self.data_cache['top_traded_stocks'] = top_stocks
            
        except Exception as e:
            logger.error(f"TR 데이터 처리 중 오류: {e}")
        
        finally:
            if self.request_event_loop:
                self.request_event_loop.exit()
    
    def _on_receive_real_data(self, stock_code, real_type, real_data):
        """실시간 데이터 수신 이벤트"""
        try:
            if real_type == "주식체결":
                current_price = self.ocx.dynamicCall("GetCommRealData(QString, int)", stock_code, 10)
                change_rate = self.ocx.dynamicCall("GetCommRealData(QString, int)", stock_code, 12)
                volume = self.ocx.dynamicCall("GetCommRealData(QString, int)", stock_code, 13)
                
                price_data = {
                    'stock_code': stock_code,
                    'current_price': abs(int(current_price)),
                    'change_rate': float(change_rate),
                    'volume': int(volume),
                }
                
                if 'real_data' in self.callbacks:
                    self.callbacks['real_data'](stock_code, price_data)
                    
        except Exception as e:
            logger.error(f"실시간 데이터 처리 중 오류: {e}")
    
    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 데이터 수신 이벤트"""
        try:
            if gubun == "0":
                order_status = self.ocx.dynamicCall("GetChejanData(int)", 913)
                stock_code = self.ocx.dynamicCall("GetChejanData(int)", 9001).strip()
                order_quantity = int(self.ocx.dynamicCall("GetChejanData(int)", 900))
                order_price = int(self.ocx.dynamicCall("GetChejanData(int)", 901))
                
                logger.info(f"체결 데이터: {stock_code} {order_quantity}주 @ {order_price}원 [{order_status}]")
                
        except Exception as e:
            logger.error(f"체결 데이터 처리 중 오류: {e}")
    
    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신 이벤트"""
        logger.info(f"키움 메시지: {msg}")
    
    def disconnect(self):
        """연결 종료"""
        try:
            self.ocx.dynamicCall("CommTerminate()")
            self.is_connected = False
            logger.info("키움 API 연결 종료")
        except Exception as e:
            logger.error(f"연결 종료 중 오류: {e}")


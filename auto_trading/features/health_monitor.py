"""
헬스 체크 및 모니터링 모듈

[파일 역할]
프로그램의 상태를 주기적으로 체크하고 이상 감지 시 자동 조치를 취합니다.

[주요 기능]
- API 연결 상태 체크
- 메모리/CPU 사용량 모니터링
- 프로그램 응답 체크
- 이상 감지 시 자동 복구 시도
- 헬스 체크 이력 저장

[사용 방법]
from health_monitor import HealthMonitor
monitor = HealthMonitor(trading_engine, kiwoom_api)
monitor.start()
"""

import time
import threading
import psutil
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from utils.logger import log


class HealthMonitor:
    """
    프로그램 헬스 체크 및 모니터링 클래스
    """
    def __init__(
        self,
        trading_engine,
        kiwoom_api,
        check_interval: int = 60,
        enable_auto_recovery: bool = True
    ):
        """
        Args:
            trading_engine: TradingEngine 인스턴스
            kiwoom_api: KiwoomAPI 인스턴스
            check_interval: 체크 간격 (초)
            enable_auto_recovery: 자동 복구 활성화
        """
        self.trading_engine = trading_engine
        self.kiwoom = kiwoom_api
        self.check_interval = check_interval
        self.enable_auto_recovery = enable_auto_recovery
        
        # 모니터링 상태
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 헬스 체크 결과
        self.last_check_time: Optional[datetime] = None
        self.check_history: List[Dict] = []
        self.max_history = 1000  # 최대 히스토리 개수
        
        # 에러 카운트
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        self.total_errors = 0
        
        # 리소스 임계값
        self.max_memory_percent = 80.0  # 메모리 사용률 80% 이상 경고
        self.max_cpu_percent = 90.0     # CPU 사용률 90% 이상 경고
        
        # 복구 시도 카운트
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
        log.info(f"헬스 모니터 초기화 완료 (체크 간격: {check_interval}초)")
    
    def start(self):
        """헬스 모니터링 시작"""
        if self.is_monitoring:
            log.warning("헬스 모니터링이 이미 실행 중입니다.")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="HealthMonitor"
        )
        self.monitor_thread.start()
        log.success("🏥 헬스 모니터링 시작")
    
    def stop(self):
        """헬스 모니터링 중지"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        log.info("🏥 헬스 모니터링 중지")
    
    def _monitoring_loop(self):
        """모니터링 루프 (별도 스레드)"""
        log.info("헬스 모니터링 루프 시작")
        
        while self.is_monitoring:
            try:
                # 헬스 체크 수행
                health_result = self.check_health()
                
                # 결과 저장
                self._save_health_result(health_result)
                
                # 이상 감지 시 처리
                if not health_result['is_healthy']:
                    self._handle_unhealthy(health_result)
                else:
                    # 정상이면 에러 카운트 리셋
                    self.consecutive_errors = 0
                
                # 대기
                time.sleep(self.check_interval)
                
            except Exception as e:
                log.error(f"헬스 모니터링 중 오류: {e}")
                self.consecutive_errors += 1
                self.total_errors += 1
                
                if self.consecutive_errors >= self.max_consecutive_errors:
                    log.error(f"연속 {self.consecutive_errors}회 헬스 체크 실패. 모니터링을 중지합니다.")
                    break
                
                time.sleep(self.check_interval)
        
        log.info("헬스 모니터링 루프 종료")
    
    def check_health(self) -> Dict:
        """
        헬스 체크 수행
        
        Returns:
            헬스 체크 결과 딕셔너리
        """
        result = {
            'timestamp': datetime.now(),
            'is_healthy': True,
            'issues': [],
            'warnings': [],
            'api_connected': False,
            'engine_running': False,
            'memory_percent': 0.0,
            'cpu_percent': 0.0,
        }
        
        # 1. API 연결 상태 체크
        try:
            if hasattr(self.kiwoom, 'is_connected'):
                # is_connected는 속성(property)이므로 괄호 없이 접근
                result['api_connected'] = self.kiwoom.is_connected
            else:
                # 대체 방법: login_event 체크
                result['api_connected'] = hasattr(self.kiwoom, 'login_event') and \
                                         self.kiwoom.login_event is not None
            
            if not result['api_connected']:
                result['is_healthy'] = False
                result['issues'].append("API 연결 끊김")
                log.warning("⚠️ 헬스 체크: API 연결 상태 이상")
        except Exception as e:
            result['is_healthy'] = False
            result['issues'].append(f"API 상태 체크 실패: {e}")
            log.error(f"API 상태 체크 오류: {e}")
        
        # 2. 엔진 실행 상태 체크
        try:
            result['engine_running'] = self.trading_engine.is_running
            
            if not result['engine_running']:
                result['warnings'].append("자동매매 엔진이 실행되지 않음")
                log.debug("ℹ️ 헬스 체크: 엔진이 실행 중이 아님 (정상일 수 있음)")
        except Exception as e:
            result['warnings'].append(f"엔진 상태 체크 실패: {e}")
            log.error(f"엔진 상태 체크 오류: {e}")
        
        # 3. 메모리 사용률 체크
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            result['memory_percent'] = memory_percent
            result['memory_mb'] = memory_info.rss / (1024 * 1024)  # MB
            
            if memory_percent > self.max_memory_percent:
                result['warnings'].append(f"메모리 사용률 높음: {memory_percent:.1f}%")
                log.warning(f"⚠️ 헬스 체크: 메모리 사용률 {memory_percent:.1f}% (임계값: {self.max_memory_percent}%)")
        except Exception as e:
            result['warnings'].append(f"메모리 체크 실패: {e}")
            log.error(f"메모리 체크 오류: {e}")
        
        # 4. CPU 사용률 체크
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=0.1)
            result['cpu_percent'] = cpu_percent
            
            if cpu_percent > self.max_cpu_percent:
                result['warnings'].append(f"CPU 사용률 높음: {cpu_percent:.1f}%")
                log.warning(f"⚠️ 헬스 체크: CPU 사용률 {cpu_percent:.1f}% (임계값: {self.max_cpu_percent}%)")
        except Exception as e:
            result['warnings'].append(f"CPU 체크 실패: {e}")
            log.error(f"CPU 체크 오류: {e}")
        
        # 5. 스레드 상태 체크
        try:
            thread_count = threading.active_count()
            result['thread_count'] = thread_count
            
            # 스레드가 너무 많으면 경고 (일반적으로 10개 이하)
            if thread_count > 20:
                result['warnings'].append(f"스레드 수 많음: {thread_count}개")
                log.warning(f"⚠️ 헬스 체크: 활성 스레드 {thread_count}개")
        except Exception as e:
            result['warnings'].append(f"스레드 체크 실패: {e}")
            log.error(f"스레드 체크 오류: {e}")
        
        # 6. 최종 판정
        if len(result['issues']) > 0:
            result['is_healthy'] = False
        
        self.last_check_time = result['timestamp']
        
        # 정상이면 DEBUG 레벨로, 이상이면 INFO 레벨로
        if result['is_healthy'] and len(result['warnings']) == 0:
            log.debug(
                f"✅ 헬스 체크 정상 - "
                f"API: {'연결' if result['api_connected'] else '끊김'}, "
                f"엔진: {'실행' if result['engine_running'] else '중지'}, "
                f"메모리: {result['memory_percent']:.1f}%, "
                f"CPU: {result['cpu_percent']:.1f}%"
            )
        else:
            log.info(
                f"{'⚠️' if result['is_healthy'] else '❌'} 헬스 체크 - "
                f"이슈: {len(result['issues'])}개, "
                f"경고: {len(result['warnings'])}개"
            )
        
        return result
    
    def _save_health_result(self, result: Dict):
        """헬스 체크 결과 저장"""
        self.check_history.append(result)
        
        # 히스토리가 너무 길면 오래된 것 삭제
        if len(self.check_history) > self.max_history:
            self.check_history = self.check_history[-self.max_history:]
    
    def _handle_unhealthy(self, health_result: Dict):
        """
        이상 감지 시 처리
        
        Args:
            health_result: 헬스 체크 결과
        """
        self.consecutive_errors += 1
        self.total_errors += 1
        
        log.error("=" * 70)
        log.error("🚨 프로그램 이상 감지!")
        log.error(f"연속 에러: {self.consecutive_errors}회")
        log.error(f"이슈: {', '.join(health_result['issues'])}")
        if health_result['warnings']:
            log.error(f"경고: {', '.join(health_result['warnings'])}")
        log.error("=" * 70)
        
        # 자동 복구 시도
        if self.enable_auto_recovery and self.recovery_attempts < self.max_recovery_attempts:
            self._attempt_recovery(health_result)
        else:
            if self.recovery_attempts >= self.max_recovery_attempts:
                log.error(f"최대 복구 시도 횟수 ({self.max_recovery_attempts}회) 도달. 수동 개입 필요.")
            else:
                log.info("자동 복구가 비활성화되어 있습니다.")
    
    def _attempt_recovery(self, health_result: Dict):
        """
        자동 복구 시도
        
        Args:
            health_result: 헬스 체크 결과
        """
        self.recovery_attempts += 1
        
        log.warning("=" * 70)
        log.warning(f"🔧 자동 복구 시도 중... ({self.recovery_attempts}/{self.max_recovery_attempts})")
        log.warning("=" * 70)
        
        recovery_success = False
        
        # API 연결 끊김 복구
        if not health_result['api_connected']:
            log.info("API 재연결 시도...")
            if self._reconnect_api():
                log.success("✅ API 재연결 성공")
                recovery_success = True
                self.consecutive_errors = 0
            else:
                log.error("❌ API 재연결 실패")
        
        # 추가 복구 로직 (향후 확장)
        # - 엔진 재시작
        # - 메모리 정리
        # - 로그 파일 정리
        
        if recovery_success:
            self.recovery_attempts = 0  # 성공 시 카운트 리셋
            log.success("🎉 자동 복구 성공!")
        else:
            log.error("🚨 자동 복구 실패")
    
    def _reconnect_api(self) -> bool:
        """
        API 재연결 시도
        
        Returns:
            재연결 성공 여부
        """
        try:
            # 키움 API 재연결 로직
            # (실제 구현은 kiwoom_api.py에 reconnect() 메서드 추가 필요)
            if hasattr(self.kiwoom, 'reconnect'):
                return self.kiwoom.reconnect()
            else:
                log.warning("kiwoom_api.py에 reconnect() 메서드가 없습니다.")
                return False
        except Exception as e:
            log.error(f"API 재연결 중 오류: {e}")
            return False
    
    def get_health_summary(self) -> Dict:
        """
        헬스 체크 요약 정보 반환
        
        Returns:
            요약 정보 딕셔너리
        """
        if not self.check_history:
            return {
                'status': 'no_data',
                'message': '아직 헬스 체크 이력이 없습니다.'
            }
        
        # 최근 10개 체크 결과 분석
        recent_checks = self.check_history[-10:]
        healthy_count = sum(1 for c in recent_checks if c['is_healthy'])
        health_rate = (healthy_count / len(recent_checks)) * 100
        
        latest = self.check_history[-1]
        
        return {
            'status': 'healthy' if latest['is_healthy'] else 'unhealthy',
            'last_check': latest['timestamp'],
            'health_rate': health_rate,
            'consecutive_errors': self.consecutive_errors,
            'total_errors': self.total_errors,
            'recovery_attempts': self.recovery_attempts,
            'api_connected': latest['api_connected'],
            'engine_running': latest['engine_running'],
            'memory_percent': latest.get('memory_percent', 0),
            'cpu_percent': latest.get('cpu_percent', 0),
            'thread_count': latest.get('thread_count', 0),
        }
    
    def print_health_summary(self):
        """헬스 체크 요약 출력"""
        summary = self.get_health_summary()
        
        if summary['status'] == 'no_data':
            print(summary['message'])
            return
        
        print("=" * 70)
        print("🏥 헬스 체크 요약")
        print("=" * 70)
        print(f"상태: {'✅ 정상' if summary['status'] == 'healthy' else '❌ 이상'}")
        print(f"마지막 체크: {summary['last_check'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"건강률 (최근 10회): {summary['health_rate']:.1f}%")
        print(f"연속 에러: {summary['consecutive_errors']}회")
        print(f"총 에러: {summary['total_errors']}회")
        print(f"복구 시도: {summary['recovery_attempts']}회")
        print(f"\nAPI 연결: {'✅' if summary['api_connected'] else '❌'}")
        print(f"엔진 실행: {'✅' if summary['engine_running'] else '⏸️'}")
        print(f"메모리 사용률: {summary['memory_percent']:.1f}%")
        print(f"CPU 사용률: {summary['cpu_percent']:.1f}%")
        print(f"활성 스레드: {summary['thread_count']}개")
        print("=" * 70)


if __name__ == "__main__":
    # 테스트용 Mock 클래스
    class MockTradingEngine:
        def __init__(self):
            self.is_running = True
    
    class MockKiwoomAPI:
        def __init__(self):
            self.login_event = True
            self.is_connected = True  # 속성으로 변경 (실제 KiwoomAPI와 동일)
        
        def reconnect(self):
            return True
    
    print("헬스 모니터 테스트를 시작합니다...\n")
    
    engine = MockTradingEngine()
    kiwoom = MockKiwoomAPI()
    
    monitor = HealthMonitor(
        trading_engine=engine,
        kiwoom_api=kiwoom,
        check_interval=5,
        enable_auto_recovery=True
    )
    
    # 헬스 체크 1회 실행
    print("1. 즉시 헬스 체크:")
    result = monitor.check_health()
    print(f"  - 결과: {'정상' if result['is_healthy'] else '이상'}")
    print(f"  - API 연결: {result['api_connected']}")
    print(f"  - 엔진 실행: {result['engine_running']}")
    print(f"  - 메모리: {result['memory_percent']:.1f}%")
    print(f"  - CPU: {result['cpu_percent']:.1f}%\n")
    
    # 모니터링 시작
    print("2. 지속적 모니터링 시작 (10초간):")
    monitor.start()
    time.sleep(10)
    monitor.stop()
    
    # 요약 출력
    print("\n3. 헬스 체크 요약:")
    monitor.print_health_summary()
    
    print("\n테스트 완료!")


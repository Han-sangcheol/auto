"""
뉴스 크롤링 모듈

[파일 역할]
주요 금융 뉴스 사이트에서 종목 관련 뉴스를 실시간으로 수집합니다.

[주요 기능]
- 네이버 금융 뉴스 크롤링
- 다음 금융 뉴스 크롤링
- 한국경제 뉴스 크롤링
- 종목코드별 뉴스 필터링
- 주기적 자동 갱신 (별도 스레드)

[데이터 형식]
{
    'title': '뉴스 제목',
    'content': '뉴스 본문',
    'date': '발행일시',
    'source': '출처',
    'url': 'URL',
    'related_stocks': ['005930', '000660', ...]
}

[사용 방법]
crawler = NewsCrawler()
news_list = crawler.get_latest_news('005930')  # 삼성전자 뉴스
crawler.start_auto_update(interval=300)  # 5분마다 자동 갱신
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading
import time
import re
from collections import defaultdict

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  requests, beautifulsoup4가 설치되지 않았습니다.")
    print("   pip install requests beautifulsoup4")

from logger import log


class NewsItem:
    """뉴스 아이템 클래스"""
    
    def __init__(
        self,
        title: str,
        content: str,
        date: datetime,
        source: str,
        url: str,
        related_stocks: List[str] = None
    ):
        self.title = title
        self.content = content
        self.date = date
        self.source = source
        self.url = url
        self.related_stocks = related_stocks or []
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'title': self.title,
            'content': self.content,
            'date': self.date.isoformat() if self.date else None,
            'source': self.source,
            'url': self.url,
            'related_stocks': self.related_stocks
        }
    
    def __repr__(self):
        return f"NewsItem(title='{self.title[:30]}...', source='{self.source}')"


class NewsCrawler:
    """뉴스 크롤러 클래스"""
    
    def __init__(self):
        self.news_cache: Dict[str, List[NewsItem]] = defaultdict(list)
        self.last_update_time = None
        self.is_running = False
        self.update_thread = None
        
        # 종목명-코드 매핑 (주요 종목)
        self.stock_name_map = {
            '삼성전자': '005930',
            'SK하이닉스': '000660',
            'LG전자': '066570',
            '현대차': '005380',
            '기아': '000270',
            'POSCO': '005490',
            'LG화학': '051910',
            '삼성바이오로직스': '207940',
            '카카오': '035720',
            'NAVER': '035420',
        }
        
        # 역 매핑 (코드 -> 이름)
        self.stock_code_map = {v: k for k, v in self.stock_name_map.items()}
        
        if not REQUESTS_AVAILABLE:
            log.warning("⚠️  requests 라이브러리가 없어 뉴스 크롤링이 비활성화됩니다.")
        else:
            log.info("뉴스 크롤러 초기화 완료")
    
    def crawl_naver_finance_news(
        self,
        stock_code: str = None,
        max_count: int = 10
    ) -> List[NewsItem]:
        """
        네이버 금융 뉴스 크롤링
        
        Args:
            stock_code: 종목 코드 (None이면 전체 뉴스)
            max_count: 최대 수집 개수
        
        Returns:
            뉴스 리스트
        """
        if not REQUESTS_AVAILABLE:
            return []
        
        news_list = []
        
        try:
            # 네이버 금융 뉴스 URL
            if stock_code:
                # 종목 뉴스
                url = f"https://finance.naver.com/item/news.naver?code={stock_code}"
            else:
                # 전체 증시 뉴스
                url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 뉴스 아이템 찾기
            news_items = soup.select('.newsList .articleSubject')
            
            for item in news_items[:max_count]:
                try:
                    # 제목 및 링크
                    link = item.get('href', '')
                    if not link.startswith('http'):
                        link = 'https://finance.naver.com' + link
                    
                    title = item.get_text(strip=True)
                    
                    # 간단한 본문 추출 (제목만 사용)
                    content = title
                    
                    # 날짜 (현재 시간으로 임시 설정)
                    news_date = datetime.now()
                    
                    # 종목 코드 추출 (제목/URL에서)
                    related_stocks = []
                    if stock_code:
                        related_stocks = [stock_code]
                    else:
                        # 제목에서 종목명 찾기
                        for stock_name, code in self.stock_name_map.items():
                            if stock_name in title:
                                related_stocks.append(code)
                    
                    news_item = NewsItem(
                        title=title,
                        content=content,
                        date=news_date,
                        source='네이버금융',
                        url=link,
                        related_stocks=related_stocks
                    )
                    
                    news_list.append(news_item)
                    
                except Exception as e:
                    log.debug(f"뉴스 아이템 파싱 오류: {e}")
                    continue
            
            if news_list:
                log.info(f"✅ 네이버 금융 뉴스 {len(news_list)}개 수집 완료")
            
        except Exception as e:
            log.error(f"❌ 네이버 금융 뉴스 크롤링 오류: {e}")
        
        return news_list
    
    def crawl_daum_finance_news(
        self,
        stock_code: str = None,
        max_count: int = 10
    ) -> List[NewsItem]:
        """
        다음 금융 뉴스 크롤링
        
        Args:
            stock_code: 종목 코드
            max_count: 최대 수집 개수
        
        Returns:
            뉴스 리스트
        """
        if not REQUESTS_AVAILABLE:
            return []
        
        news_list = []
        
        try:
            # 다음 금융 뉴스 URL
            if stock_code:
                # A 접두사 추가 (다음 종목 코드 형식)
                url = f"https://finance.daum.net/quotes/A{stock_code}#news"
            else:
                url = "https://finance.daum.net/news"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 뉴스 아이템 찾기
            news_items = soup.select('.news_list .link_news')
            
            for item in news_items[:max_count]:
                try:
                    link = item.get('href', '')
                    title = item.get_text(strip=True)
                    
                    # 종목 코드 추출
                    related_stocks = []
                    if stock_code:
                        related_stocks = [stock_code]
                    else:
                        for stock_name, code in self.stock_name_map.items():
                            if stock_name in title:
                                related_stocks.append(code)
                    
                    news_item = NewsItem(
                        title=title,
                        content=title,
                        date=datetime.now(),
                        source='다음금융',
                        url=link,
                        related_stocks=related_stocks
                    )
                    
                    news_list.append(news_item)
                    
                except Exception as e:
                    log.debug(f"뉴스 아이템 파싱 오류: {e}")
                    continue
            
            if news_list:
                log.info(f"✅ 다음 금융 뉴스 {len(news_list)}개 수집 완료")
            
        except Exception as e:
            log.error(f"❌ 다음 금융 뉴스 크롤링 오류: {e}")
        
        return news_list
    
    def get_latest_news(
        self,
        stock_code: str = None,
        max_count: int = 20
    ) -> List[NewsItem]:
        """
        최신 뉴스 가져오기 (모든 소스 통합)
        
        Args:
            stock_code: 종목 코드 (None이면 전체)
            max_count: 최대 개수
        
        Returns:
            뉴스 리스트
        """
        all_news = []
        
        # 네이버 금융
        naver_news = self.crawl_naver_finance_news(stock_code, max_count // 2)
        all_news.extend(naver_news)
        
        # 다음 금융
        daum_news = self.crawl_daum_finance_news(stock_code, max_count // 2)
        all_news.extend(daum_news)
        
        # 날짜순 정렬 (최신순)
        all_news.sort(key=lambda x: x.date, reverse=True)
        
        # 캐시에 저장
        cache_key = stock_code or 'all'
        self.news_cache[cache_key] = all_news[:max_count]
        self.last_update_time = datetime.now()
        
        return all_news[:max_count]
    
    def get_cached_news(
        self,
        stock_code: str = None
    ) -> List[NewsItem]:
        """
        캐시된 뉴스 가져오기
        
        Args:
            stock_code: 종목 코드
        
        Returns:
            뉴스 리스트
        """
        cache_key = stock_code or 'all'
        return self.news_cache.get(cache_key, [])
    
    def start_auto_update(self, interval: int = 300):
        """
        자동 갱신 시작 (별도 스레드)
        
        Args:
            interval: 갱신 간격 (초), 기본 5분
        """
        if self.is_running:
            log.warning("이미 자동 갱신이 실행 중입니다.")
            return
        
        self.is_running = True
        
        def update_loop():
            log.info(f"🔄 뉴스 자동 갱신 시작 (간격: {interval}초)")
            
            while self.is_running:
                try:
                    # 전체 뉴스 갱신
                    self.get_latest_news(max_count=20)
                    log.info(f"✅ 뉴스 자동 갱신 완료: {datetime.now().strftime('%H:%M:%S')}")
                    
                    # 대기
                    for _ in range(interval):
                        if not self.is_running:
                            break
                        time.sleep(1)
                    
                except Exception as e:
                    log.error(f"❌ 뉴스 자동 갱신 오류: {e}")
                    time.sleep(interval)
            
            log.info("🛑 뉴스 자동 갱신 중지")
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def stop_auto_update(self):
        """자동 갱신 중지"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.update_thread:
            self.update_thread.join(timeout=5)
        
        log.info("뉴스 자동 갱신이 중지되었습니다.")
    
    def get_statistics(self) -> Dict:
        """
        통계 정보 반환
        
        Returns:
            통계 딕셔너리
        """
        total_news = sum(len(news_list) for news_list in self.news_cache.values())
        
        return {
            'total_news': total_news,
            'cached_stocks': list(self.news_cache.keys()),
            'last_update': self.last_update_time.isoformat() if self.last_update_time else None,
            'is_running': self.is_running
        }
    
    def print_news_summary(self, stock_code: str = None):
        """뉴스 요약 출력"""
        news_list = self.get_cached_news(stock_code)
        
        if not news_list:
            print(f"\n{'=' * 60}")
            print("📰 뉴스 없음")
            print(f"{'=' * 60}\n")
            return
        
        print(f"\n{'=' * 60}")
        print(f"📰 최신 뉴스 ({len(news_list)}개)")
        if stock_code:
            stock_name = self.stock_code_map.get(stock_code, stock_code)
            print(f"종목: {stock_name} ({stock_code})")
        print(f"{'=' * 60}")
        
        for i, news in enumerate(news_list[:10], 1):
            print(f"\n{i}. [{news.source}] {news.title[:50]}...")
            if news.related_stocks:
                stocks_str = ', '.join([
                    f"{self.stock_code_map.get(code, code)}({code})" 
                    for code in news.related_stocks[:3]
                ])
                print(f"   관련 종목: {stocks_str}")
        
        print(f"\n{'=' * 60}\n")


# 테스트 코드
if __name__ == "__main__":
    print("뉴스 크롤러 테스트")
    print("=" * 60)
    
    if not REQUESTS_AVAILABLE:
        print("⚠️  requests 라이브러리를 설치해주세요:")
        print("   pip install requests beautifulsoup4")
        exit(1)
    
    # 크롤러 생성
    crawler = NewsCrawler()
    
    # 삼성전자 뉴스 수집
    print("\n삼성전자 뉴스 수집 중...")
    news_list = crawler.get_latest_news('005930', max_count=10)
    
    # 결과 출력
    crawler.print_news_summary('005930')
    
    # 통계
    stats = crawler.get_statistics()
    print(f"총 뉴스: {stats['total_news']}개")
    print(f"캐시된 종목: {', '.join(stats['cached_stocks'])}")
    
    print("\n=" * 60)
    print("✅ 테스트 완료")


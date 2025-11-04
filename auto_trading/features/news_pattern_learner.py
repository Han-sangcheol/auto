"""
뉴스 크롤링 패턴 자동 학습 모듈

[파일 역할]
HTML 구조 변경 시 자동으로 다른 CSS 셀렉터를 시도하고 성공 패턴을 학습하여
다음 실행 시 최적의 셀렉터를 먼저 사용할 수 있도록 합니다.

[주요 기능]
- CSS 셀렉터 후보군 관리
- 셀렉터 성공/실패 기록
- 성공률 기반 최적 셀렉터 선택
- JSON 파일로 패턴 저장/로드 (압축 및 최적화)
- 자동 보정 (동작하는 셀렉터 자동 탐색)

[사용 방법]
learner = NewsPatternLearner()
best_selector = learner.get_best_selector('naver')
working_selector = learner.find_working_selector('naver', soup)
learner.record_success('naver', selector)
learner.save_patterns()
"""

import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from logger import log

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class NewsPatternLearner:
    """뉴스 크롤링 패턴 자동 학습 및 보정"""
    
    def __init__(self, pattern_file: str = "news_crawling_patterns.json"):
        """
        패턴 학습기 초기화
        
        Args:
            pattern_file: 패턴 저장 파일명 (logs 폴더에 저장)
        """
        self.pattern_file = os.path.join("logs", pattern_file)
        
        # 시도할 CSS 셀렉터 후보군 (우선순위 순)
        self.selector_candidates = {
            'naver': [
                '.newsList .articleSubject',  # 기본 패턴
                '.news_list .articleSubject',  # 변형 1
                '.articleSubject a',  # 변형 2
                '.news_wrap .news_tit',  # 변형 3
                'a.articleSubject',  # 변형 4
                '.today_list .articleSubject',  # 변형 5
                '.news_area .news_tit',  # 변형 6
                'div.newsList a',  # 변형 7
                '.realtimeNewsList a',  # 변형 8
            ],
            'daum': [
                '.news_list .link_news',  # 기본 패턴
                '.list_news .link_txt',  # 변형 1
                'a.link_news',  # 변형 2
                '.news_item a',  # 변형 3
                'div.news_list a',  # 변형 4
                '.list_newsflash a',  # 변형 5
            ],
            'hankyung': [
                '.news-list .news-tit',  # 기본 패턴
                '.article-list .tit',  # 변형 1
                'a.news-tit',  # 변형 2
            ]
        }
        
        # 패턴 데이터 로드
        self.patterns = self.load_patterns()
        
        log.info("뉴스 패턴 학습기 초기화 완료")
    
    def load_patterns(self) -> Dict:
        """
        저장된 패턴 로드 (최적화)
        
        Returns:
            패턴 딕셔너리
        """
        if not os.path.exists(self.pattern_file):
            log.info(f"패턴 파일 없음, 기본 패턴으로 초기화: {self.pattern_file}")
            return self._create_default_patterns()
        
        try:
            with open(self.pattern_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            
            log.success(f"✅ 뉴스 크롤링 패턴 로드 완료: {len(patterns.get('sources', {}))}개 소스")
            return patterns
            
        except Exception as e:
            log.error(f"❌ 패턴 로드 실패: {e}, 기본 패턴으로 초기화")
            return self._create_default_patterns()
    
    def _create_default_patterns(self) -> Dict:
        """기본 패턴 생성"""
        patterns = {
            'sources': {},
            'version': '1.0',
            'last_updated': datetime.now().isoformat()
        }
        
        # 각 소스별 기본 패턴 초기화
        for source, selectors in self.selector_candidates.items():
            patterns['sources'][source] = {
                'current_best': selectors[0],  # 첫 번째를 기본으로
                'patterns': {}
            }
            
            # 모든 후보 셀렉터 초기화
            for selector in selectors:
                patterns['sources'][source]['patterns'][selector] = {
                    'success_count': 0,
                    'fail_count': 0,
                    'last_success': None,
                    'last_failure': None,
                    'success_rate': 0.0
                }
        
        return patterns
    
    def save_patterns(self):
        """패턴 저장 (압축 및 최적화)"""
        try:
            # logs 디렉토리 생성
            os.makedirs(os.path.dirname(self.pattern_file), exist_ok=True)
            
            # 타임스탬프 업데이트
            self.patterns['last_updated'] = datetime.now().isoformat()
            
            # JSON 저장 (압축)
            with open(self.pattern_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, ensure_ascii=False, indent=2)
            
            log.success(f"✅ 뉴스 크롤링 패턴 저장 완료: {self.pattern_file}")
            
        except Exception as e:
            log.error(f"❌ 패턴 저장 실패: {e}")
    
    def get_best_selector(self, source: str) -> str:
        """
        최적 셀렉터 반환 (성공률 기반)
        
        Args:
            source: 뉴스 소스 ('naver', 'daum', 'hankyung')
        
        Returns:
            최적 CSS 셀렉터
        """
        if source not in self.patterns['sources']:
            # 소스가 없으면 기본 후보 첫 번째 반환
            if source in self.selector_candidates:
                return self.selector_candidates[source][0]
            return ''
        
        source_data = self.patterns['sources'][source]
        return source_data.get('current_best', '')
    
    def find_working_selector(self, source: str, soup: 'BeautifulSoup') -> Optional[str]:
        """
        동작하는 셀렉터 찾기 (후보군에서 순차 시도)
        
        Args:
            source: 뉴스 소스
            soup: BeautifulSoup 객체
        
        Returns:
            동작하는 셀렉터 (없으면 None)
        """
        if not BS4_AVAILABLE:
            return None
        
        if source not in self.selector_candidates:
            log.warning(f"⚠️  알 수 없는 소스: {source}")
            return None
        
        # 성공률 순으로 정렬된 셀렉터 목록 가져오기
        sorted_selectors = self._get_sorted_selectors(source)
        
        for selector in sorted_selectors:
            try:
                elements = soup.select(selector)
                if elements and len(elements) > 0:
                    # 유효한 요소 찾음
                    log.info(f"✅ [{source}] 동작하는 셀렉터 발견: {selector} ({len(elements)}개 요소)")
                    return selector
            except Exception as e:
                log.debug(f"셀렉터 시도 실패 ({selector}): {e}")
                continue
        
        return None
    
    def _get_sorted_selectors(self, source: str) -> List[str]:
        """
        성공률 순으로 정렬된 셀렉터 목록
        
        Args:
            source: 뉴스 소스
        
        Returns:
            정렬된 셀렉터 리스트
        """
        if source not in self.patterns['sources']:
            # 패턴 없으면 기본 후보군 반환
            return self.selector_candidates.get(source, [])
        
        source_data = self.patterns['sources'][source]
        patterns = source_data.get('patterns', {})
        
        # 성공률 계산 및 정렬
        selector_scores = []
        for selector, stats in patterns.items():
            success_count = stats.get('success_count', 0)
            fail_count = stats.get('fail_count', 0)
            total = success_count + fail_count
            
            if total > 0:
                success_rate = success_count / total
            else:
                success_rate = 0.0
            
            # 최근 성공 시간도 고려 (최근일수록 우선)
            last_success = stats.get('last_success')
            recency_bonus = 0.0
            if last_success:
                try:
                    last_success_time = datetime.fromisoformat(last_success)
                    days_ago = (datetime.now() - last_success_time).days
                    recency_bonus = max(0, 1.0 - (days_ago / 30))  # 최대 30일
                except:
                    pass
            
            # 최종 점수 = 성공률 (70%) + 최근성 (30%)
            final_score = success_rate * 0.7 + recency_bonus * 0.3
            
            selector_scores.append((selector, final_score, success_rate))
        
        # 점수 순으로 정렬
        selector_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 점수가 매겨진 셀렉터 + 나머지 후보군
        sorted_selectors = [item[0] for item in selector_scores]
        
        # 후보군에 있지만 아직 시도 안 된 셀렉터 추가
        all_candidates = self.selector_candidates.get(source, [])
        for candidate in all_candidates:
            if candidate not in sorted_selectors:
                sorted_selectors.append(candidate)
        
        return sorted_selectors
    
    def record_success(self, source: str, selector: str):
        """
        성공 패턴 기록 및 우선순위 조정
        
        Args:
            source: 뉴스 소스
            selector: 성공한 셀렉터
        """
        if source not in self.patterns['sources']:
            self.patterns['sources'][source] = {
                'current_best': selector,
                'patterns': {}
            }
        
        source_data = self.patterns['sources'][source]
        
        # 패턴 통계 업데이트
        if selector not in source_data['patterns']:
            source_data['patterns'][selector] = {
                'success_count': 0,
                'fail_count': 0,
                'last_success': None,
                'last_failure': None,
                'success_rate': 0.0
            }
        
        pattern = source_data['patterns'][selector]
        pattern['success_count'] += 1
        pattern['last_success'] = datetime.now().isoformat()
        
        # 성공률 계산
        total = pattern['success_count'] + pattern['fail_count']
        pattern['success_rate'] = pattern['success_count'] / total if total > 0 else 0.0
        
        # current_best 업데이트 (성공률이 더 높으면 교체)
        current_best = source_data['current_best']
        if current_best != selector:
            current_best_stats = source_data['patterns'].get(current_best, {})
            current_best_rate = current_best_stats.get('success_rate', 0.0)
            
            if pattern['success_rate'] > current_best_rate:
                log.info(f"📊 [{source}] 최적 셀렉터 변경: {current_best} → {selector}")
                source_data['current_best'] = selector
    
    def record_failure(self, source: str, selector: str):
        """
        실패 패턴 기록
        
        Args:
            source: 뉴스 소스
            selector: 실패한 셀렉터
        """
        if source not in self.patterns['sources']:
            self.patterns['sources'][source] = {
                'current_best': '',
                'patterns': {}
            }
        
        source_data = self.patterns['sources'][source]
        
        # 패턴 통계 업데이트
        if selector not in source_data['patterns']:
            source_data['patterns'][selector] = {
                'success_count': 0,
                'fail_count': 0,
                'last_success': None,
                'last_failure': None,
                'success_rate': 0.0
            }
        
        pattern = source_data['patterns'][selector]
        pattern['fail_count'] += 1
        pattern['last_failure'] = datetime.now().isoformat()
        
        # 성공률 재계산
        total = pattern['success_count'] + pattern['fail_count']
        pattern['success_rate'] = pattern['success_count'] / total if total > 0 else 0.0
    
    def get_statistics(self, source: str = None) -> Dict:
        """
        통계 정보 반환
        
        Args:
            source: 특정 소스 (None이면 전체)
        
        Returns:
            통계 딕셔너리
        """
        if source:
            if source not in self.patterns['sources']:
                return {}
            
            source_data = self.patterns['sources'][source]
            total_success = sum(p.get('success_count', 0) for p in source_data['patterns'].values())
            total_failure = sum(p.get('fail_count', 0) for p in source_data['patterns'].values())
            
            return {
                'source': source,
                'current_best': source_data.get('current_best', ''),
                'total_success': total_success,
                'total_failure': total_failure,
                'total_attempts': total_success + total_failure,
                'overall_success_rate': total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 0.0,
                'pattern_count': len(source_data['patterns'])
            }
        else:
            # 전체 통계
            stats = {}
            for src in self.patterns['sources'].keys():
                stats[src] = self.get_statistics(src)
            return stats


# 테스트 코드
if __name__ == "__main__":
    learner = NewsPatternLearner("test_patterns.json")
    
    print("=== 초기 최적 셀렉터 ===")
    print(f"네이버: {learner.get_best_selector('naver')}")
    print(f"다음: {learner.get_best_selector('daum')}")
    
    # 성공 기록
    learner.record_success('naver', '.newsList .articleSubject')
    learner.record_success('naver', '.newsList .articleSubject')
    learner.record_success('naver', '.news_list .articleSubject')
    learner.record_failure('naver', '.news_wrap .news_tit')
    
    print("\n=== 기록 후 최적 셀렉터 ===")
    print(f"네이버: {learner.get_best_selector('naver')}")
    
    print("\n=== 통계 ===")
    stats = learner.get_statistics('naver')
    print(f"총 시도: {stats['total_attempts']}회")
    print(f"성공률: {stats['overall_success_rate']*100:.1f}%")
    
    # 저장
    learner.save_patterns()
    
    print(f"\n✅ 패턴 파일 저장: {learner.pattern_file}")



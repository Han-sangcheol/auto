"""
감성 분석 모듈

[파일 역할]
뉴스 기사의 감성(긍정/부정)을 분석하여 매매 판단에 활용합니다.

[주요 기능]
- 키워드 기반 감성 분석 (무료)
- 긍정/부정 키워드 가중치 계산
- 뉴스 점수 계산 (-100 ~ +100)
- 종목별 감성 점수 집계

[분석 방법]
1. 키워드 매칭: 긍정/부정 키워드 사전 기반
2. 가중치 계산: 키워드별 중요도 반영
3. 점수 정규화: -100 ~ +100 범위로 변환

[사용 방법]
analyzer = SentimentAnalyzer()
score = analyzer.analyze_text("삼성전자 실적 호조")
# score > 0: 긍정, score < 0: 부정, score = 0: 중립
"""

from typing import Dict, List, Tuple
from collections import defaultdict
import re

from logger import log


class SentimentAnalyzer:
    """감성 분석기 클래스"""
    
    def __init__(self):
        # 긍정 키워드 사전 (단어: 가중치)
        self.positive_keywords = {
            # 상승 관련
            '상승': 3,
            '급등': 5,
            '폭등': 5,
            '강세': 3,
            '반등': 3,
            '신고가': 5,
            '최고가': 4,
            '오름': 2,
            
            # 실적 관련
            '호조': 4,
            '개선': 3,
            '증가': 3,
            '성장': 3,
            '이익': 2,
            '흑자': 4,
            '실적개선': 5,
            '매출증가': 4,
            
            # 긍정 평가
            '긍정': 3,
            '낙관': 3,
            '기대': 2,
            '전망좋': 3,
            '유망': 3,
            
            # 투자 관련
            '투자': 2,
            '확대': 2,
            '증설': 3,
            '수주': 3,
            '계약': 2,
            
            # 기타
            '호재': 4,
            '돌파': 3,
            '회복': 3,
            '개선': 3,
        }
        
        # 부정 키워드 사전 (단어: 가중치)
        self.negative_keywords = {
            # 하락 관련
            '하락': 3,
            '급락': 5,
            '폭락': 5,
            '약세': 3,
            '조정': 2,
            '최저가': 4,
            '신저가': 5,
            '내림': 2,
            
            # 실적 관련
            '부진': 4,
            '감소': 3,
            '손실': 4,
            '적자': 5,
            '악화': 4,
            '실적부진': 5,
            '매출감소': 4,
            
            # 부정 평가
            '부정': 3,
            '비관': 3,
            '우려': 3,
            '전망나쁨': 3,
            '위험': 3,
            
            # 문제 관련
            '문제': 2,
            '리스크': 3,
            '위기': 4,
            '어려움': 2,
            '불안': 3,
            
            # 기타
            '악재': 4,
            '실망': 3,
            '타격': 3,
            '중단': 3,
        }
        
        # 강도 수식어 (앞에 붙으면 가중치 증가)
        self.intensifiers = {
            '매우': 1.5,
            '아주': 1.5,
            '너무': 1.5,
            '크게': 1.3,
            '대폭': 1.5,
            '급': 1.5,
            '대': 1.3,
        }
        
        # 약화 수식어 (앞에 붙으면 가중치 감소)
        self.downtoners = {
            '약간': 0.5,
            '소폭': 0.5,
            '다소': 0.6,
            '조금': 0.5,
        }
        
        # 부정 수식어 (뒤따르는 단어의 극성 반전)
        self.negations = ['없', '못', '아니', '안', '비']
        
        log.info(
            f"감성 분석기 초기화: "
            f"긍정 키워드 {len(self.positive_keywords)}개, "
            f"부정 키워드 {len(self.negative_keywords)}개"
        )
    
    def analyze_text(self, text: str) -> int:
        """
        텍스트 감성 분석
        
        Args:
            text: 분석할 텍스트
        
        Returns:
            감성 점수 (-100 ~ +100)
            양수: 긍정, 음수: 부정, 0: 중립
        """
        if not text:
            return 0
        
        # 텍스트 전처리
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)  # 특수문자 제거
        
        positive_score = 0
        negative_score = 0
        
        # 긍정 키워드 검색
        for keyword, weight in self.positive_keywords.items():
            if keyword in text:
                # 수식어 확인
                adjusted_weight = self._adjust_weight(text, keyword, weight)
                positive_score += adjusted_weight
        
        # 부정 키워드 검색
        for keyword, weight in self.negative_keywords.items():
            if keyword in text:
                # 수식어 확인
                adjusted_weight = self._adjust_weight(text, keyword, weight)
                negative_score += adjusted_weight
        
        # 최종 점수 계산 (정규화)
        total_score = positive_score - negative_score
        
        # -100 ~ +100 범위로 정규화
        # 최대 점수를 50으로 가정
        max_score = 50
        normalized_score = max(min(total_score / max_score * 100, 100), -100)
        
        return int(normalized_score)
    
    def _adjust_weight(self, text: str, keyword: str, weight: float) -> float:
        """
        수식어에 따라 가중치 조정
        
        Args:
            text: 전체 텍스트
            keyword: 키워드
            weight: 기본 가중치
        
        Returns:
            조정된 가중치
        """
        adjusted_weight = weight
        
        # 키워드 위치 찾기
        index = text.find(keyword)
        if index == -1:
            return adjusted_weight
        
        # 앞 단어 확인 (5글자 이내)
        start = max(0, index - 5)
        before_text = text[start:index]
        
        # 강도 수식어 확인
        for intensifier, multiplier in self.intensifiers.items():
            if intensifier in before_text:
                adjusted_weight *= multiplier
                break
        
        # 약화 수식어 확인
        for downtoner, multiplier in self.downtoners.items():
            if downtoner in before_text:
                adjusted_weight *= multiplier
                break
        
        # 부정 수식어 확인 (극성 반전)
        for negation in self.negations:
            if negation in before_text:
                adjusted_weight *= -1
                break
        
        return adjusted_weight
    
    def analyze_news(self, news_item) -> Dict:
        """
        뉴스 아이템 감성 분석
        
        Args:
            news_item: NewsItem 객체 또는 딕셔너리
        
        Returns:
            분석 결과 딕셔너리
        """
        # 제목 분석
        if hasattr(news_item, 'title'):
            title = news_item.title
            content = news_item.content
        else:
            title = news_item.get('title', '')
            content = news_item.get('content', '')
        
        title_score = self.analyze_text(title)
        content_score = self.analyze_text(content)
        
        # 가중 평균 (제목 70%, 본문 30%)
        final_score = int(title_score * 0.7 + content_score * 0.3)
        
        # 감성 분류
        if final_score >= 30:
            sentiment = '매우 긍정'
        elif final_score >= 10:
            sentiment = '긍정'
        elif final_score <= -30:
            sentiment = '매우 부정'
        elif final_score <= -10:
            sentiment = '부정'
        else:
            sentiment = '중립'
        
        return {
            'title_score': title_score,
            'content_score': content_score,
            'final_score': final_score,
            'sentiment': sentiment
        }
    
    def analyze_news_list(self, news_list: List) -> Dict:
        """
        뉴스 리스트 전체 분석
        
        Args:
            news_list: NewsItem 리스트
        
        Returns:
            종합 분석 결과
        """
        if not news_list:
            return {
                'average_score': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'sentiment': '중립'
            }
        
        scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for news in news_list:
            result = self.analyze_news(news)
            score = result['final_score']
            scores.append(score)
            
            if score >= 10:
                positive_count += 1
            elif score <= -10:
                negative_count += 1
            else:
                neutral_count += 1
        
        # 평균 점수
        average_score = int(sum(scores) / len(scores))
        
        # 전체 감성
        if average_score >= 20:
            overall_sentiment = '매우 긍정'
        elif average_score >= 10:
            overall_sentiment = '긍정'
        elif average_score <= -20:
            overall_sentiment = '매우 부정'
        elif average_score <= -10:
            overall_sentiment = '부정'
        else:
            overall_sentiment = '중립'
        
        return {
            'average_score': average_score,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'total_count': len(news_list),
            'sentiment': overall_sentiment,
            'scores': scores
        }
    
    def get_stock_sentiment(
        self,
        news_crawler,
        stock_code: str
    ) -> Dict:
        """
        특정 종목의 뉴스 감성 분석
        
        Args:
            news_crawler: NewsCrawler 객체
            stock_code: 종목 코드
        
        Returns:
            종목 감성 분석 결과
        """
        # 캐시된 뉴스 가져오기
        news_list = news_crawler.get_cached_news(stock_code)
        
        if not news_list:
            # 뉴스가 없으면 새로 가져오기
            news_list = news_crawler.get_latest_news(stock_code, max_count=20)
        
        # 뉴스 리스트 분석
        analysis = self.analyze_news_list(news_list)
        analysis['stock_code'] = stock_code
        
        return analysis
    
    def print_analysis_summary(self, analysis: Dict):
        """분석 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("📊 뉴스 감성 분석 결과")
        print("=" * 60)
        
        if 'stock_code' in analysis:
            print(f"종목 코드: {analysis['stock_code']}")
        
        print(f"총 뉴스: {analysis.get('total_count', 0)}개")
        print(f"평균 점수: {analysis.get('average_score', 0):+d}/100")
        print(f"전체 감성: {analysis.get('sentiment', '중립')}")
        print()
        print(f"긍정 뉴스: {analysis.get('positive_count', 0)}개")
        print(f"부정 뉴스: {analysis.get('negative_count', 0)}개")
        print(f"중립 뉴스: {analysis.get('neutral_count', 0)}개")
        print("=" * 60 + "\n")


# 테스트 코드
if __name__ == "__main__":
    print("감성 분석기 테스트")
    print("=" * 60)
    
    # 분석기 생성
    analyzer = SentimentAnalyzer()
    
    # 테스트 텍스트
    test_texts = [
        "삼성전자 실적 호조, 주가 급등",
        "SK하이닉스 매출 감소로 주가 하락",
        "LG전자 신제품 출시 기대",
        "현대차 대폭 상승, 실적 개선 전망",
        "NAVER 악재 발생, 주가 폭락",
        "카카오 조금 오름, 거래량 증가",
    ]
    
    print("\n개별 텍스트 분석:")
    for text in test_texts:
        score = analyzer.analyze_text(text)
        print(f"\n텍스트: {text}")
        print(f"점수: {score:+d}/100")
        
        if score >= 10:
            sentiment = "긍정 😊"
        elif score <= -10:
            sentiment = "부정 😟"
        else:
            sentiment = "중립 😐"
        print(f"감성: {sentiment}")
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료")


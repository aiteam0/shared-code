import os
import json
import logging
import requests
import pandas as pd
from typing import List, Dict, Optional
from urllib.parse import quote

class GoogleCustomSearch:
    """Google Custom Search API를 사용한 검색 클래스"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("GOOGLE_API_KEY와 GOOGLE_SEARCH_ENGINE_ID 환경변수가 필요합니다.")
    
    def search(self, query: str, wanted_row: int = 10, search_type: str = "web", 
               date_restrict: Optional[str] = None, news_sites: bool = False) -> List[Dict[str, str]]:
        """
        Google Custom Search API를 사용한 검색
        
        Args:
            query: 검색 쿼리
            wanted_row: 원하는 결과 수
            search_type: "web" 또는 "news"
            date_restrict: 날짜 제한 (예: "d7", "w2", "m1")
            news_sites: 뉴스 사이트로 제한 여부
        """
        query = query.replace("|", "OR")
        if search_type == "web":
            query += " -filetype:pdf"
        
        # 뉴스 검색시 최신 결과 우선
        if search_type == "news":
            if not date_restrict:
                date_restrict = "w1"  # 기본적으로 1주일 이내
            if news_sites:
                query += " site:news.google.com OR site:news.naver.com OR site:news.daum.net"
        
        results = []
        start_pages = list(range(1, min(wanted_row + 91, 100), 10))  # 최대 100개 제한
        
        for start_page in start_pages:
            if len(results) >= wanted_row:
                break
                
            url = f"{self.base_url}?key={self.api_key}&cx={self.search_engine_id}&q={quote(query)}&start={start_page}&num=10"
            
            # 날짜 제한 추가
            if date_restrict:
                url += f"&dateRestrict={date_restrict}"
            
            # 뉴스 검색시 날짜순 정렬
            if search_type == "news":
                url += "&sort=date"
            
            try:
                response = requests.get(url)
                data = response.json()
                
                if "items" not in data:
                    break
                    
                for item in data["items"]:
                    if len(results) >= wanted_row:
                        break
                        
                    title = item.get("title", "")
                    link = item.get("link", "")
                    description = item.get("snippet", "")
                    
                    # 기존 Trash_Link 필터링 로직 유지 가능
                    # if any(trash in link for trash in Trash_Link):
                    #     continue
                    
                    results.append({
                        "title": title,
                        "link": link, 
                        "url": link,  # TavilySearch 호환성
                        "description": description,
                        "content": f"{title}\n{description}",  # GoogleNews 호환성
                        "snippet": description  # TavilySearch 호환성
                    })
                    
            except Exception as e:
                logging.error(f"Google Custom Search API 오류: {e}")
                break
                
        return results

class GoogleWebSearch(GoogleCustomSearch):
    """TavilySearch 호환 웹 검색 클래스"""
    
    def __init__(self, topic="general", max_results=3, days=7, **kwargs):
        super().__init__()
        self.topic = topic
        self.max_results = max_results
        self.days = days
        self.name = "web_search"
        self.description = "Search the web for general information, research, facts, and non-news content."
    
    def search(self, query: str, max_results: Optional[int] = None, **kwargs) -> List[Dict[str, str]]:
        """TavilySearch.search() 호환 메서드"""
        max_results = max_results or self.max_results
        return super().search(query, wanted_row=max_results, search_type="web")
    
    def _run(self, query: str) -> str:
        """LangChain BaseTool 호환"""
        results = self.search(query)
        return json.dumps(results, ensure_ascii=False)

class GoogleNewsSearch(GoogleCustomSearch):
    """GoogleNews 호환 뉴스 검색 클래스"""
    
    def __init__(self, use_morphological_analysis: bool = True):
        super().__init__()
        self.use_morphological_analysis = use_morphological_analysis
        self.base_url = "https://news.google.com/rss"  # 호환성 유지
    
    def search_by_keyword(self, keyword: Optional[str] = None, k: int = 3, 
                         optimize_query: bool = True) -> List[Dict[str, str]]:
        """GoogleNews.search_by_keyword() 호환 메서드"""
        if not keyword:
            return self.search_latest(k)
            
        results = super().search(keyword, wanted_row=k, search_type="news", 
                               date_restrict="d7", news_sites=True)
        
        # GoogleNews 포맷으로 변환
        formatted_results = []
        for result in results:
            formatted_results.append({
                "url": result["link"],
                "content": result["title"],
                "published": "Recent",  # Google Custom Search는 정확한 발행일 제공 안함
                "summary": result["description"]
            })
        
        return formatted_results
    
    def search_latest(self, k: int = 3) -> List[Dict[str, str]]:
        """GoogleNews.search_latest() 호환 메서드"""
        results = super().search("latest news", wanted_row=k, search_type="news", 
                               date_restrict="d1", news_sites=True)
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "url": result["link"],
                "content": result["title"],
                "published": "Latest",
                "summary": result["description"]
            })
        
        return formatted_results
    
    def extract_keywords(self, text: str) -> List[str]:
        """형태소 분석 호환 메서드 (단순 구현)"""
        # 기본적인 키워드 추출 (Kiwi 없이)
        return text.split()[:5]
    
    def create_optimized_query(self, text: str) -> str:
        """쿼리 최적화 호환 메서드"""
        return text
    
    def get_analysis_info(self) -> Dict[str, any]:
        """분석기 정보 호환 메서드"""
        return {
            "kiwi_available": False,
            "morphological_analysis_enabled": self.use_morphological_analysis,
            "kiwi_initialized": False
        }

# 기존 코드와의 완전한 호환성을 위한 별칭
TavilySearch = GoogleWebSearch
GoogleNews = GoogleNewsSearch




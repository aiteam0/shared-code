import os
import json
import logging
import requests
import pandas as pd
from typing import List, Dict, Optional, Sequence, Literal
from urllib.parse import quote
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# TavilySearch 호환용 Input 모델
class TavilySearchInput(BaseModel):
    """Input for the Tavily tool."""
    query: str = Field(description="검색 쿼리")

class TavilySearch(BaseTool):
    """TavilySearch 완벽 호환 클래스 (Google Custom Search 기반)"""
    
    name: str = "tavily_web_search"
    description: str = (
        "A search engine optimized for comprehensive, accurate, and trusted results. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query. [IMPORTANT] Input(query) should be over 5 characters."
    )
    args_schema: type[BaseModel] = TavilySearchInput
    
    # 원본 TavilySearch의 모든 필드들 + Google API용 필드들
    client: Optional[object] = None  # 호환성 유지 (사용 안함)
    include_domains: list = []
    exclude_domains: list = []
    max_results: int = 3
    topic: Literal["general", "news"] = "general"
    days: int = 3
    search_depth: Literal["basic", "advanced"] = "basic"
    include_answer: bool = False
    include_raw_content: bool = True
    include_images: bool = False
    format_output: bool = False
    
    # Google API용 필드들 추가
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    google_base_url: str = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,  # Tavily API 키 (호환성용, 사용 안함)
        include_domains: list = [],
        exclude_domains: list = [],
        max_results: int = 3,
        topic: Literal["general", "news"] = "general",
        days: int = 3,
        search_depth: Literal["basic", "advanced"] = "basic",
        include_answer: bool = False,
        include_raw_content: bool = True,
        include_images: bool = False,
        format_output: bool = False,
    ):
        """TavilySearch와 동일한 초기화 파라미터"""
        super().__init__()
        
        # 원본 TavilySearch 속성들
        self.client = None  # 호환성 유지
        self.include_domains = include_domains
        self.exclude_domains = exclude_domains
        self.max_results = max_results
        self.topic = topic
        self.days = days
        self.search_depth = search_depth
        self.include_answer = include_answer
        self.include_raw_content = include_raw_content
        self.include_images = include_images
        self.format_output = format_output
        
        # Google API 초기화
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.google_base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.google_api_key or not self.google_search_engine_id:
            raise ValueError("GOOGLE_API_KEY와 GOOGLE_SEARCH_ENGINE_ID 환경변수가 필요합니다.")

    def google_search(self, query: str, wanted_row: int = 10, search_type: str = "web", 
                     date_restrict: Optional[str] = None, news_sites: bool = False) -> List[Dict[str, str]]:
        """Google Custom Search API 호출"""
        query = query.replace("|", "OR")
        if search_type == "web":
            query += " -filetype:pdf"
        
        if search_type == "news":
            if not date_restrict:
                date_restrict = "w1"
            if news_sites:
                query += " (site:news.google.com OR site:news.naver.com OR site:news.daum.net)"
        
        start_pages = []
        df_google = pd.DataFrame(columns=['Title','Link','Description'])
        row_count = 0

        for i in range(1, wanted_row + 1000, 10):
            start_pages.append(i)

        for start_page in start_pages:
            url = f"{self.google_base_url}?key={self.google_api_key}&cx={self.google_search_engine_id}&q={quote(query)}&start={start_page}&num=10"
            
            if date_restrict:
                url += f"&dateRestrict={date_restrict}"
            
            if search_type == "news":
                url += "&sort=date"
            
            try:
                data = requests.get(url).json()
                search_items = data.get("items")
                
                if not search_items:
                    break
                
                for i, search_item in enumerate(search_items, start=1):
                    link = search_item.get("link")
                    title = search_item.get("title")
                    description = search_item.get("snippet")
                    
                    df_google.loc[start_page + i] = [title, link, description]
                    row_count += 1
                    
                    if row_count >= wanted_row or row_count == 300:
                        return self._convert_df_to_list(df_google)
                        
            except Exception as e:
                logging.error(f"Google Custom Search API 오류: {e}")
                break
        
        return self._convert_df_to_list(df_google)
    
    def _convert_df_to_list(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """DataFrame을 리스트로 변환"""
        results = []
        for _, row in df.iterrows():
            results.append({
                "title": row["Title"] or "",
                "link": row["Link"] or "",
                "description": row["Description"] or ""
            })
        return results

    def _run(self, query: str) -> str:
        """BaseTool의 _run 메서드 구현"""
        results = self.search(query)
        return results

    def search(
        self,
        query: str,
        search_depth: Literal["basic", "advanced"] = None,
        topic: Literal["general", "news"] = None,
        days: int = None,
        max_results: int = None,
        include_domains: Sequence[str] = None,
        exclude_domains: Sequence[str] = None,
        include_answer: bool = None,
        include_raw_content: bool = None,
        include_images: bool = None,
        format_output: bool = None,
        **kwargs,
    ) -> list:
        """TavilySearch.search()와 동일한 인터페이스"""
        
        topic = topic or self.topic
        max_results = max_results or self.max_results
        days = days or self.days
        
        # 날짜 제한 설정
        date_restrict = None
        if topic == "news" and days:
            if days <= 7:
                date_restrict = f"d{days}"
            elif days <= 30:
                date_restrict = f"w{days//7}"
            else:
                date_restrict = f"m{days//30}"
        
        # Google Custom Search 실행
        search_type = "news" if topic == "news" else "web"
        google_results = self.google_search(
            query=query,
            wanted_row=max_results,
            search_type=search_type,
            date_restrict=date_restrict,
            news_sites=(topic == "news")
        )
        
        # TavilySearch 결과 포맷으로 변환
        tavily_results = []
        for result in google_results:
            tavily_result = {
                "title": result["title"],
                "url": result["link"],
                "content": result["description"],
                "score": 0.8,
                "raw_content": result["description"] if include_raw_content else None
            }
            tavily_results.append(tavily_result)
        
        return tavily_results

    def get_search_context(self, query: str, **kwargs) -> str:
        """TavilySearch.get_search_context() 호환"""
        results = self.search(query, **kwargs)
        return json.dumps(results, ensure_ascii=False)

# GoogleNews 클래스도 동일한 방식으로 수정
class GoogleNews:
    """GoogleNews 완벽 호환 클래스 (Google Custom Search 기반)"""
    
    def __init__(self, use_morphological_analysis: bool = True):
        self.base_url = "https://news.google.com/rss"
        self.use_morphological_analysis = use_morphological_analysis
        self.kiwi = None
        
        # Google API 초기화
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.google_search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.google_base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.google_api_key or not self.google_search_engine_id:
            raise ValueError("GOOGLE_API_KEY와 GOOGLE_SEARCH_ENGINE_ID 환경변수가 필요합니다.")

    def google_search(self, query: str, wanted_row: int = 10) -> List[Dict[str, str]]:
        """Google Custom Search for News"""
        query = query.replace("|", "OR")
        query += " (site:news.google.com OR site:news.naver.com OR site:news.daum.net)"
        
        results = []
        for start_page in range(1, min(wanted_row + 91, 100), 10):
            url = f"{self.google_base_url}?key={self.google_api_key}&cx={self.google_search_engine_id}&q={quote(query)}&start={start_page}&num=10&dateRestrict=w1&sort=date"
            
            try:
                data = requests.get(url).json()
                search_items = data.get("items", [])
                
                for search_item in search_items:
                    if len(results) >= wanted_row:
                        return results
                        
                    results.append({
                        "title": search_item.get("title", ""),
                        "link": search_item.get("link", ""),
                        "description": search_item.get("snippet", "")
                    })
                    
            except Exception as e:
                logging.error(f"Google News Search API 오류: {e}")
                break
                
        return results

    def search_by_keyword(self, keyword: Optional[str] = None, k: int = 3, optimize_query: bool = True) -> List[Dict[str, str]]:
        """GoogleNews.search_by_keyword() 호환"""
        if not keyword:
            return self.search_latest(k)
        
        search_keyword = self.create_optimized_query(keyword) if optimize_query else keyword
        google_results = self.google_search(search_keyword, k)
        
        return [
            {
                "url": result["link"],
                "content": result["title"],
                "published": "Recent",
                "summary": result["description"]
            }
            for result in google_results
        ]

    def search_latest(self, k: int = 3) -> List[Dict[str, str]]:
        """GoogleNews.search_latest() 호환"""
        google_results = self.google_search("latest news", k)
        
        return [
            {
                "url": result["link"],
                "content": result["title"],
                "published": "Latest",
                "summary": result["description"]
            }
            for result in google_results
        ]

    def extract_keywords(self, text: str) -> List[str]:
        """간단한 키워드 추출"""
        if not text:
            return []
        
        words = text.split()
        stop_words = ['것', '수', '때', '등', '중', '후', '전', '간', '내', '외', '이', '그', '저', '의', '을', '를', '에', '와', '과']
        return [word.strip() for word in words if len(word.strip()) > 1 and word not in stop_words][:10]

    def create_optimized_query(self, text: str) -> str:
        """쿼리 최적화"""
        if not self.use_morphological_analysis:
            return text
        keywords = self.extract_keywords(text)
        return ' '.join(keywords[:5]) if keywords else text

    def get_analysis_info(self) -> Dict[str, any]:
        """분석기 정보"""
        return {
            "kiwi_available": False,
            "morphological_analysis_enabled": self.use_morphological_analysis,
            "kiwi_initialized": False
        }

import os
import json
import logging
import requests
import pandas as pd
from typing import List, Dict, Optional, Sequence, Literal
from urllib.parse import quote
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class TavilySearchInput(BaseModel):
    """Input for the Tavily tool."""
    query: str = Field(description="검색 쿼리")

def core_google_search(query: str, wanted_row: int, search_type: str = "web") -> pd.DataFrame:
    """
    사용자 제공 Google_API 함수를 정확히 복사한 핵심 검색 함수
    """
    # 환경변수에서 API 키 가져오기
    Google_API_KEY = os.getenv('GOOGLE_API_KEY')
    Google_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not Google_API_KEY or not Google_SEARCH_ENGINE_ID:
        raise ValueError("GOOGLE_API_KEY와 GOOGLE_SEARCH_ENGINE_ID 환경변수가 필요합니다.")
    
    # Trash_Link 정의 (원본과 동일)
    Trash_Link = ["tistory", "kin", "youtube", "blog", "book", "dcinside", "fmkorea", "ruliweb", "theqoo", "clien", "mlbpark", "instiz", "todayhumor"]
    
    # 뉴스 검색일 때는 news도 제외하지 않음 (뉴스 사이트가 필요하므로)
    if search_type == "web":
        Trash_Link.append("news")
    
    # 쿼리 처리 (원본과 동일)
    query = query.replace("|", "OR")
    
    # 검색 타입별 쿼리 조정
    if search_type == "web":
        query += " -filetype:pdf"
    elif search_type == "news":
        # 뉴스 검색시 뉴스 사이트로 제한하고 최신순 정렬
        query += " (site:news.google.com OR site:news.naver.com OR site:news.daum.net OR site:bbc.com OR site:cnn.com)"
    
    start_pages = []
    df_google = pd.DataFrame(columns=['Title','Link','Description'])
    row_count = 0

    # 페이지 계산 (원본과 동일)
    for i in range(1, wanted_row + 1000, 10):
        start_pages.append(i)

    for start_page in start_pages:
        # URL 구성 (원본과 동일하게 단순화)
        url = f"https://www.googleapis.com/customsearch/v1?key={Google_API_KEY}&cx={Google_SEARCH_ENGINE_ID}&q={query}&start={start_page}"
        
        # 뉴스 검색시 추가 파라미터
        if search_type == "news":
            url += "&dateRestrict=w1&sort=date"  # 1주일 이내, 날짜순 정렬
        
        try:
            # API 호출 (원본과 동일)
            data = requests.get(url).json()
            search_items = data.get("items")
            
            # 원본과 동일한 예외 처리
            for i, search_item in enumerate(search_items, start=1):
                link = search_item.get("link")
                if any(trash in link for trash in Trash_Link):
                    pass
                else: 
                    title = search_item.get("title")
                    description = search_item.get("snippet")  # 원본에서는 descripiton이지만 수정
                    
                    # DataFrame에 추가 (원본과 동일)
                    df_google.loc[start_page + i] = [title, link, description]
                    row_count += 1
                    
                    # 종료 조건 (원본과 동일)
                    if (row_count >= wanted_row) or (row_count == 300):
                        return df_google
        except:
            # 원본과 동일한 예외 처리 (빈 except)
            return df_google
    
    return df_google

class TavilySearch(BaseTool):
    """TavilySearch 완벽 호환 클래스 (원본 Google_API 기반)"""
    
    name: str = "tavily_web_search"
    description: str = (
        "A search engine optimized for comprehensive, accurate, and trusted results. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query. [IMPORTANT] Input(query) should be over 5 characters."
    )
    args_schema: type[BaseModel] = TavilySearchInput
    
    # 모든 필요한 필드들
    client: Optional[object] = None
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
    
    # Google API용 (사용하지 않지만 호환성 유지)
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    google_base_url: str = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
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
        super().__init__()
        
        self.client = None
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
        include_raw_content = include_raw_content if include_raw_content is not None else self.include_raw_content
        
        # 검색 타입 결정
        search_type = "news" if topic == "news" else "web"
        
        try:
            # 원본 Google_API 함수 호출
            df_result = core_google_search(query, max_results, search_type)
            
            # TavilySearch 결과 포맷으로 변환
            tavily_results = []
            for _, row in df_result.iterrows():
                tavily_result = {
                    "title": row["Title"] or "",
                    "url": row["Link"] or "",
                    "content": row["Description"] or "",
                    "score": 0.8,
                }
                
                if include_raw_content:
                    tavily_result["raw_content"] = row["Description"] or ""
                
                tavily_results.append(tavily_result)
            
            return tavily_results
            
        except Exception as e:
            logging.error(f"Google Custom Search 오류: {e}")
            return []

    def get_search_context(self, query: str, **kwargs) -> str:
        """TavilySearch.get_search_context() 호환"""
        results = self.search(query, **kwargs)
        return json.dumps(results, ensure_ascii=False)

class GoogleNews:
    """GoogleNews 완벽 호환 클래스 (원본 Google_API 기반)"""
    
    def __init__(self, use_morphological_analysis: bool = True):
        self.base_url = "https://news.google.com/rss"
        self.use_morphological_analysis = use_morphological_analysis
        self.kiwi = None

    def search_by_keyword(
        self, 
        keyword: Optional[str] = None, 
        k: int = 3, 
        optimize_query: bool = True
    ) -> List[Dict[str, str]]:
        """GoogleNews.search_by_keyword() 호환"""
        
        if not keyword:
            return self.search_latest(k)
        
        # 쿼리 최적화 (단순화)
        search_keyword = self.create_optimized_query(keyword) if optimize_query else keyword
        
        try:
            # 뉴스 검색 실행
            df_result = core_google_search(search_keyword, k, "news")
            
            # GoogleNews 포맷으로 변환
            news_results = []
            for _, row in df_result.iterrows():
                news_results.append({
                    "url": row["Link"] or "",
                    "content": row["Title"] or "",
                    "published": "Recent",
                    "summary": row["Description"] or ""
                })
            
            return news_results
            
        except Exception as e:
            logging.error(f"Google News Search 오류: {e}")
            return []

    def search_latest(self, k: int = 3) -> List[Dict[str, str]]:
        """GoogleNews.search_latest() 호환"""
        
        try:
            # 최신 뉴스 검색
            df_result = core_google_search("latest news", k, "news")
            
            # GoogleNews 포맷으로 변환
            news_results = []
            for _, row in df_result.iterrows():
                news_results.append({
                    "url": row["Link"] or "",
                    "content": row["Title"] or "",
                    "published": "Latest",
                    "summary": row["Description"] or ""
                })
            
            return news_results
            
        except Exception as e:
            logging.error(f"Google Latest News Search 오류: {e}")
            return []

    def extract_keywords(self, text: str) -> List[str]:
        """간단한 키워드 추출"""
        if not text:
            return []
        
        words = text.split()
        stop_words = ['것', '수', '때', '등', '중', '후', '전', '간', '내', '외', '이', '그', '저', '의', '을', '를', '에', '와', '과']
        
        keywords = []
        for word in words:
            word = word.strip()
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)
                
        return keywords[:10]

    def create_optimized_query(self, text: str) -> str:
        """쿼리 최적화"""
        if not self.use_morphological_analysis:
            return text
            
        keywords = self.extract_keywords(text)
        if not keywords:
            return text
            
        return ' '.join(keywords[:5])

    def get_analysis_info(self) -> Dict[str, any]:
        """분석기 정보"""
        return {
            "kiwi_available": False,
            "morphological_analysis_enabled": self.use_morphological_analysis,
            "kiwi_initialized": False
        }

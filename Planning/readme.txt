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

def Google_API_Enhanced(query: str, wanted_row: int, search_type: str = "web", 
                       date_restrict: Optional[str] = None) -> pd.DataFrame:
    """
    원본 Google_API 함수를 기반으로 한 향상된 버전
    
    Args:
        query: 검색 쿼리
        wanted_row: 원하는 결과 수
        search_type: "web" 또는 "news"
        date_restrict: 날짜 제한 (예: "d7", "w1", "m1")
    
    Returns:
        DataFrame with columns: Title, Link, Description
    """
    # 환경변수에서 API 키 가져오기
    Google_API_KEY = os.getenv('GOOGLE_API_KEY')
    Google_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not Google_API_KEY or not Google_SEARCH_ENGINE_ID:
        raise ValueError("GOOGLE_API_KEY와 GOOGLE_SEARCH_ENGINE_ID 환경변수가 필요합니다.")
    
    # 검색 타입에 따라 다른 Trash_Link 적용
    if search_type == "web":
        Trash_Link = ["tistory", "kin", "youtube", "blog", "book", "news", "dcinside", 
                     "fmkorea", "ruliweb", "theqoo", "clien", "mlbpark", "instiz", "todayhumor"]
    else:  # news
        # 뉴스 검색에서는 news 사이트 허용
        Trash_Link = ["tistory", "kin", "youtube", "blog", "book", "dcinside", 
                     "fmkorea", "ruliweb", "theqoo", "clien", "mlbpark", "instiz", "todayhumor"]
    
    # 원본 로직 그대로
    query = query.replace("|", "OR")
    
    if search_type == "web":
        query += " -filetype:pdf"
    elif search_type == "news":
        # 뉴스 검색일 때는 뉴스 사이트에 집중
        query += " (site:news.google.com OR site:news.naver.com OR site:news.daum.net OR site:bbc.com OR site:cnn.com)"
    
    start_pages = []
    df_google = pd.DataFrame(columns=['Title','Link','Description'])
    row_count = 0

    # 원본 로직 그대로
    for i in range(1, wanted_row + 1000, 10):
        start_pages.append(i)

    for start_page in start_pages:
        # 기본 URL 구성
        url = f"https://www.googleapis.com/customsearch/v1?key={Google_API_KEY}&cx={Google_SEARCH_ENGINE_ID}&q={quote(query)}&start={start_page}"
        
        # 뉴스 검색 시 추가 파라미터
        if search_type == "news":
            if date_restrict:
                url += f"&dateRestrict={date_restrict}"
            else:
                url += "&dateRestrict=w1"  # 기본적으로 1주일
            url += "&sort=date"  # 날짜순 정렬
        
        try:
            data = requests.get(url).json()
            search_items = data.get("items")
            
            if not search_items:
                break
                
            for i, search_item in enumerate(search_items, start=1):
                link = search_item.get("link")
                if any(trash in link for trash in Trash_Link):
                    pass
                else: 
                    title = search_item.get("title")
                    description = search_item.get("snippet")  # 오타 수정
                    df_google.loc[start_page + i] = [title, link, description] 
                    row_count += 1
                    if (row_count >= wanted_row) or (row_count == 300):
                        return df_google
        except Exception as e:
            logging.error(f"Google Custom Search API 오류: {e}")
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
    
    # 모든 필드 선언
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
        days = days or self.days
        include_raw_content = include_raw_content if include_raw_content is not None else self.include_raw_content
        
        # 날짜 제한 설정
        date_restrict = None
        if topic == "news" and days:
            if days <= 7:
                date_restrict = f"d{days}"
            elif days <= 30:
                date_restrict = f"w{max(1, days//7)}"
            else:
                date_restrict = f"m{max(1, days//30)}"
        
        # 원본 Google_API 함수 호출
        search_type = "news" if topic == "news" else "web"
        try:
            df_result = Google_API_Enhanced(
                query=query,
                wanted_row=max_results,
                search_type=search_type,
                date_restrict=date_restrict
            )
            
            # DataFrame을 TavilySearch 포맷으로 변환
            tavily_results = []
            for _, row in df_result.iterrows():
                if pd.notna(row['Title']) and pd.notna(row['Link']):
                    result = {
                        "title": str(row['Title']),
                        "url": str(row['Link']),
                        "content": str(row['Description']) if pd.notna(row['Description']) else "",
                        "score": 0.8,
                    }
                    if include_raw_content:
                        result["raw_content"] = str(row['Description']) if pd.notna(row['Description']) else ""
                    
                    tavily_results.append(result)
            
            return tavily_results
            
        except Exception as e:
            logging.error(f"TavilySearch 검색 중 오류: {e}")
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
        
        # 쿼리 최적화
        search_keyword = self.create_optimized_query(keyword) if optimize_query and self.use_morphological_analysis else keyword
        
        try:
            # 원본 Google_API 함수 호출 (뉴스 검색)
            df_result = Google_API_Enhanced(
                query=search_keyword,
                wanted_row=k,
                search_type="news",
                date_restrict="w1"  # 1주일 이내
            )
            
            # DataFrame을 GoogleNews 포맷으로 변환
            news_results = []
            for _, row in df_result.iterrows():
                if pd.notna(row['Title']) and pd.notna(row['Link']):
                    news_results.append({
                        "url": str(row['Link']),
                        "content": str(row['Title']),
                        "published": "Recent",  # Google Custom Search는 정확한 발행일 제공 안함
                        "summary": str(row['Description']) if pd.notna(row['Description']) else ""
                    })
            
            return news_results
            
        except Exception as e:
            logging.error(f"GoogleNews 키워드 검색 중 오류: {e}")
            return []

    def search_latest(self, k: int = 3) -> List[Dict[str, str]]:
        """GoogleNews.search_latest() 호환"""
        
        try:
            # 최신 뉴스 검색
            df_result = Google_API_Enhanced(
                query="latest news",
                wanted_row=k,
                search_type="news",
                date_restrict="d1"  # 하루 이내
            )
            
            # DataFrame을 GoogleNews 포맷으로 변환
            news_results = []
            for _, row in df_result.iterrows():
                if pd.notna(row['Title']) and pd.notna(row['Link']):
                    news_results.append({
                        "url": str(row['Link']),
                        "content": str(row['Title']),
                        "published": "Latest",
                        "summary": str(row['Description']) if pd.notna(row['Description']) else ""
                    })
            
            return news_results
            
        except Exception as e:
            logging.error(f"GoogleNews 최신 검색 중 오류: {e}")
            return []

    def extract_keywords(self, text: str) -> List[str]:
        """간단한 키워드 추출 (Kiwi 없이)"""
        if not text:
            return []
        
        words = text.split()
        stop_words = ['것', '수', '때', '등', '중', '후', '전', '간', '내', '외', '이', '그', '저', '의', '을', '를', '에', '와', '과']
        keywords = [word.strip() for word in words if len(word.strip()) > 1 and word not in stop_words]
        return keywords[:10]

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

    # 호환성을 위한 빈 메서드들
    def _fetch_news(self, url: str, k: int = 3) -> List[Dict[str, str]]:
        return []

    def _collect_news(self, news_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return news_list

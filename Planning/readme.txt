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

class GoogleCustomSearch:
    """Google Custom Search API 기본 클래스"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("GOOGLE_API_KEY와 GOOGLE_SEARCH_ENGINE_ID 환경변수가 필요합니다.")
    
    def google_search(self, query: str, wanted_row: int = 10, search_type: str = "web", 
                     date_restrict: Optional[str] = None, news_sites: bool = False) -> List[Dict[str, str]]:
        """
        사용자 제공 Google_API 함수 개선 버전
        """
        # 기본 쿼리 처리
        query = query.replace("|", "OR")
        if search_type == "web":
            query += " -filetype:pdf"
        
        # 뉴스 검색 최적화
        if search_type == "news":
            if not date_restrict:
                date_restrict = "w1"
            if news_sites:
                query += " (site:news.google.com OR site:news.naver.com OR site:news.daum.net OR site:bbc.com OR site:cnn.com)"
        
        start_pages = []
        df_google = pd.DataFrame(columns=['Title','Link','Description'])
        row_count = 0

        # 페이지 계산
        for i in range(1, wanted_row + 1000, 10):
            start_pages.append(i)

        for start_page in start_pages:
            url = f"{self.base_url}?key={self.api_key}&cx={self.search_engine_id}&q={quote(query)}&start={start_page}&num=10"
            
            # 날짜 제한 추가
            if date_restrict:
                url += f"&dateRestrict={date_restrict}"
            
            # 뉴스 검색시 날짜순 정렬
            if search_type == "news":
                url += "&sort=date"
            
            try:
                data = requests.get(url).json()
                search_items = data.get("items")
                
                if not search_items:
                    break
                
                for i, search_item in enumerate(search_items, start=1):
                    link = search_item.get("link")
                    
                    # Trash_Link 필터링 (사용자 코드와 동일)
                    # if any(trash in link for trash in Trash_Link):
                    #     continue
                    
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

class TavilySearch(BaseTool, GoogleCustomSearch):
    """TavilySearch 완벽 호환 클래스"""
    
    name: str = "tavily_web_search"
    description: str = (
        "A search engine optimized for comprehensive, accurate, and trusted results. "
        "Useful for when you need to answer questions about current events. "
        "Input should be a search query. [IMPORTANT] Input(query) should be over 5 characters."
    )
    args_schema: type[BaseModel] = TavilySearchInput
    
    # TavilySearch와 동일한 속성들
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
        api_key: Optional[str] = None,  # 호환성 유지 (실제로는 사용 안함)
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
        BaseTool.__init__(self)
        GoogleCustomSearch.__init__(self)
        
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
        """BaseTool의 _run 메서드 구현 (원본과 동일)"""
        results = self.search(query)
        return results  # 원본은 JSON 문자열 반환 안함

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
        
        # 파라미터 설정
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
                "score": 0.8,  # 기본 점수
                "raw_content": result["description"] if include_raw_content else None
            }
            tavily_results.append(tavily_result)
        
        return tavily_results

    def get_search_context(self, query: str, **kwargs) -> str:
        """TavilySearch.get_search_context() 호환"""
        results = self.search(query, **kwargs)
        return json.dumps(results, ensure_ascii=False)

class GoogleNews(GoogleCustomSearch):
    """GoogleNews 완벽 호환 클래스"""
    
    def __init__(self, use_morphological_analysis: bool = True):
        """GoogleNews와 동일한 초기화"""
        super().__init__()
        self.base_url = "https://news.google.com/rss"  # 호환성 유지
        self.use_morphological_analysis = use_morphological_analysis
        self.kiwi = None  # Kiwi 사용 안함을 명시

    def extract_keywords(self, text: str) -> List[str]:
        """GoogleNews.extract_keywords() 호환"""
        if not text:
            return []
        
        # 간단한 키워드 추출 (Kiwi 없이)
        words = text.split()
        keywords = []
        
        # 의미없는 단어 제거
        stop_words = ['것', '수', '때', '등', '중', '후', '전', '간', '내', '외', '이', '그', '저', '의', '을', '를', '에', '와', '과']
        
        for word in words:
            word = word.strip()
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)
        
        return keywords[:10]  # 최대 10개

    def create_optimized_query(self, text: str) -> str:
        """GoogleNews.create_optimized_query() 호환"""
        if not self.use_morphological_analysis:
            return text
            
        keywords = self.extract_keywords(text)
        if not keywords:
            return text
            
        return ' '.join(keywords[:5])

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
        if optimize_query and self.use_morphological_analysis:
            search_keyword = self.create_optimized_query(keyword)
        else:
            search_keyword = keyword
        
        # Google Custom Search로 뉴스 검색
        google_results = self.google_search(
            query=search_keyword,
            wanted_row=k,
            search_type="news",
            date_restrict="w1",  # 1주일 이내
            news_sites=True
        )
        
        # GoogleNews 포맷으로 변환
        news_results = []
        for result in google_results:
            news_results.append({
                "url": result["link"],
                "content": result["title"],
                "published": "Recent",  # 정확한 발행일은 Google Custom Search에서 제공 안함
                "summary": result["description"]
            })
        
        return news_results

    def search_latest(self, k: int = 3) -> List[Dict[str, str]]:
        """GoogleNews.search_latest() 호환"""
        
        # 최신 뉴스 검색
        google_results = self.google_search(
            query="latest news",
            wanted_row=k,
            search_type="news",
            date_restrict="d1",  # 하루 이내
            news_sites=True
        )
        
        # GoogleNews 포맷으로 변환
        news_results = []
        for result in google_results:
            news_results.append({
                "url": result["link"],
                "content": result["title"],
                "published": "Latest",
                "summary": result["description"]
            })
        
        return news_results

    def get_analysis_info(self) -> Dict[str, any]:
        """GoogleNews.get_analysis_info() 호환"""
        return {
            "kiwi_available": False,
            "morphological_analysis_enabled": self.use_morphological_analysis,
            "kiwi_initialized": False
        }

    def _fetch_news(self, url: str, k: int = 3) -> List[Dict[str, str]]:
        """GoogleNews._fetch_news() 호환 (사용 안함)"""
        return []

    def _collect_news(self, news_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """GoogleNews._collect_news() 호환 (사용 안함)"""
        return news_list

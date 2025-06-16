import os
import requests
import pandas as pd
import json
from typing import List, Dict, Optional, Literal
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class GoogleSearchInput(BaseModel):
    """Google Custom Search API 입력 스키마"""
    query: str = Field(description="검색 쿼리")

class GoogleCustomSearch(BaseTool):
    """Google Custom Search API를 사용한 웹 검색 도구"""
    
    name: str = "google_web_search"
    description: str = (
        "Google Custom Search API를 사용한 웹 검색 도구입니다. "
        "일반적인 웹 정보, 연구 자료, 사실 확인 등에 사용하세요. "
        "최신 뉴스가 아닌 일반적인 정보 검색에 최적화되어 있습니다."
    )
    args_schema: type[BaseModel] = GoogleSearchInput
    
    def __init__(
        self,
        max_results: int = 3,
        search_type: str = "web",  # "web" or "news"
        date_restrict: Optional[str] = None,  # "d1", "w1", "m1", "y1" 등
        site_search: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.max_results = max_results
        self.search_type = search_type
        self.date_restrict = date_restrict
        self.site_search = site_search
        
        # 환경변수에서 API 키와 검색 엔진 ID 가져오기
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("GOOGLE_API_KEY와 GOOGLE_SEARCH_ENGINE_ID 환경변수가 필요합니다.")

    def _run(self, query: str) -> str:
        """검색 실행"""
        try:
            results = self._google_search(query, self.max_results)
            return json.dumps(results, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Google 검색 중 오류 발생: {e}")
            return json.dumps([{
                "title": "Error",
                "url": "",
                "content": f"검색 중 오류가 발생했습니다: {str(e)}",
                "score": 0.0
            }], ensure_ascii=False)

    def _google_search(self, query: str, wanted_row: int) -> List[Dict]:
        """Google Custom Search API 호출"""
        # 기존 Google_API 함수 로직을 클래스 메서드로 변환
        trash_links = ["tistory", "kin", "youtube", "blog", "book", "dcinside", 
                      "fmkorea", "ruliweb", "theqoo", "clien", "mlbpark", "instiz", "todayhumor"]
        
        # 뉴스 검색인 경우 필터링 제외
        if self.search_type == "news":
            trash_links = ["tistory", "kin", "youtube", "blog", "book"]  # 뉴스는 덜 필터링
        
        query = query.replace("|", "OR")
        query += " -filetype:pdf"
        
        results = []
        row_count = 0
        
        for start_page in range(1, wanted_row + 1000, 10):
            url = f"https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "start": start_page,
                "num": 10
            }
            
            # 뉴스 검색 특화 파라미터
            if self.search_type == "news":
                if self.date_restrict:
                    params["dateRestrict"] = self.date_restrict
                params["sort"] = "date"  # 날짜순 정렬
                # 뉴스 사이트 우선 검색
                if not self.site_search:
                    params["siteSearch"] = "site:news.google.com OR site:naver.com OR site:daum.net"
            
            if self.site_search:
                params["siteSearch"] = self.site_search
                
            try:
                response = requests.get(url, params=params)
                data = response.json()
                search_items = data.get("items", [])
                
                for item in search_items:
                    link = item.get("link", "")
                    
                    # 트래시 링크 필터링
                    if any(trash in link for trash in trash_links):
                        continue
                    
                    title = item.get("title", "")
                    description = item.get("snippet", "")
                    
                    result = {
                        "title": title,
                        "url": link,
                        "content": description,
                        "score": 0.8,
                        "source_type": "NEWS" if self.search_type == "news" else "WEB"
                    }
                    
                    results.append(result)
                    row_count += 1
                    
                    if row_count >= wanted_row or row_count >= 300:
                        return results
                        
            except Exception as e:
                logger.error(f"API 호출 중 오류: {e}")
                break
                
        return results

class GoogleNewsSearch(GoogleCustomSearch):
    """Google Custom Search API를 사용한 뉴스 검색 도구"""
    
    name: str = "google_news_search"
    description: str = (
        "Google Custom Search API를 사용한 뉴스 검색 도구입니다. "
        "최신 뉴스, 시사, 현재 이슈 검색에 특화되어 있습니다. "
        "일반적인 웹 검색보다 최신성과 뉴스 관련성이 높습니다."
    )
    
    def __init__(self, max_results: int = 3, date_restrict: str = "w1", **kwargs):
        super().__init__(
            max_results=max_results,
            search_type="news",
            date_restrict=date_restrict,  # 기본적으로 1주일 이내
            **kwargs
        )

# 기존 import 주석 처리하고 새로운 import 추가
# from langchain_utils.tools.tavily import TavilySearch
from langchain_utils.tools.google_search import GoogleCustomSearch

class WebSearchTool(BaseTool[GoogleCustomSearch]):  # TavilySearch -> GoogleCustomSearch
    """웹 검색을 수행하는 도구 클래스"""

    def _create_tool(self) -> GoogleCustomSearch:  # TavilySearch -> GoogleCustomSearch
        """GoogleCustomSearch 객체를 생성하고 설정하는 내부 메서드"""
        search = GoogleCustomSearch(
            max_results=self.max_results,
            search_type="web"
        )
        search.name = "web_search"
        search.description = "Search the web for general information, research, facts, and non-news content. Use this for comprehensive web searches when you need general information that is not specifically about recent news or current events."
        return search

# 기존 import 주석 처리하고 새로운 import 추가
# from langchain_utils.tools.news import GoogleNews
from langchain_utils.tools.google_search import GoogleNewsSearch

class NewsSearchTool(BaseTool[GoogleNewsSearch]):  # 기존 클래스 구조 유지
    """Google Custom Search API를 사용한 뉴스 검색 도구 클래스"""

    def __init__(self, max_results: int = 3, search_type: str = "keyword"):
        super().__init__()
        self.max_results = max_results
        self.search_type = search_type

    def _create_tool(self) -> GoogleNewsSearch:
        """GoogleNewsSearch 객체를 생성하고 설정하는 내부 메서드"""
        search = GoogleNewsSearch(
            max_results=self.max_results,
            date_restrict="w1"  # 1주일 이내 뉴스
        )
        search.name = "news_search"
        search.description = "Search for recent news articles and current events using Google Custom Search API. This tool is specifically designed for finding latest news, breaking news, current events, and recent updates."
        return search


import os
import requests
import pandas as pd
from typing import List, Dict, Optional, Literal
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import json


class GoogleSearchInput(BaseModel):
    """Google Custom Search API 입력"""
    query: str = Field(description="검색 쿼리")
    num_results: int = Field(default=5, description="검색 결과 개수 (1-10)")


class GoogleCustomSearch(BaseTool):
    """Google Custom Search API를 사용한 웹 검색 도구"""
    
    name: str = "google_web_search"
    description: str = (
        "Google Custom Search API를 사용한 웹 검색. "
        "일반적인 웹 검색과 최신 정보 검색에 유용합니다."
    )
    args_schema: type[BaseModel] = GoogleSearchInput
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("Google_API_KEY")
        self.search_engine_id = os.getenv("Google_SEARCH_ENGINE_ID")
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("Google_API_KEY와 Google_SEARCH_ENGINE_ID 환경변수가 필요합니다.")
    
    def _run(self, query: str, num_results: int = 5) -> str:
        """웹 검색 실행"""
        results = self._google_search(query, num_results, search_type="web")
        return json.dumps(results, ensure_ascii=False)
    
    def _google_search(self, query: str, num_results: int, search_type: str = "web") -> List[Dict]:
        """Google Custom Search API 호출"""
        url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10)
        }
        
        # 웹 검색용 추가 파라미터
        if search_type == "web":
            params["dateRestrict"] = "m1"  # 최근 1개월
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "displayLink": item.get("displayLink", "")
                })
            
            return results
            
        except Exception as e:
            return [{"error": f"검색 중 오류 발생: {str(e)}"}]


class GoogleNewsSearch(BaseTool):
    """Google Custom Search API를 사용한 뉴스 검색 도구"""
    
    name: str = "google_news_search"  
    description: str = (
        "Google Custom Search API를 사용한 뉴스 검색. "
        "최신 뉴스와 시사 정보 검색에 특화되어 있습니다."
    )
    args_schema: type[BaseModel] = GoogleSearchInput
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("Google_API_KEY")
        self.search_engine_id = os.getenv("Google_SEARCH_ENGINE_ID")
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("Google_API_KEY와 Google_SEARCH_ENGINE_ID 환경변수가 필요합니다.")
    
    def _run(self, query: str, num_results: int = 3) -> str:
        """뉴스 검색 실행"""
        results = self._google_news_search(query, num_results)
        return json.dumps(results, ensure_ascii=False)
    
    def _google_news_search(self, query: str, num_results: int) -> List[Dict]:
        """뉴스 전용 Google Custom Search API 호출"""
        url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10),
            "dateRestrict": "d3",  # 최근 3일
            "sort": "date",  # 날짜순 정렬
            "siteSearch": "news.google.com OR naver.com OR daum.net OR chosun.com OR joongang.co.kr"
        }
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "publishedTime": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time", ""),
                    "source": item.get("displayLink", "")
                })
            
            return results
            
        except Exception as e:
            return [{"error": f"뉴스 검색 중 오류 발생: {str(e)}"}]



# 기존 imports 이후에 추가
from langchain_utils.tools.google_search import GoogleCustomSearch, GoogleNewsSearch

# get_tools 함수 내부에 조건 추가 (기존 tools 리스트에 추가)
def get_tools(mode="web_search"):
    tools = []
    
    # 기존 코드...
    
    # Google Custom Search API 도구 추가
    try:
        google_web_search = GoogleCustomSearch()
        google_news_search = GoogleNewsSearch()
        
        if mode in ["web_search", "all"]:
            tools.append(google_web_search)
        
        if mode in ["news_search", "all"]:
            tools.append(google_news_search)
            
    except ValueError as e:
        print(f"Google Search 도구 초기화 실패: {e}")
    
    return tools

# line 30-40 근처에 추가
def get_available_tools():
    """사용 가능한 도구 확인 및 반환"""
    tools = []
    
    # Google Custom Search 우선 시도
    try:
        from langchain_utils.tools.google_search import GoogleCustomSearch, GoogleNewsSearch
        tools.extend([GoogleCustomSearch(), GoogleNewsSearch()])
        print("Google Custom Search API 도구 사용")
    except:
        # 기존 도구 사용
        try:
            from langchain_utils.tools.tavily import TavilySearch
            from langchain_utils.tools.news import GoogleNews
            # 기존 도구 추가 로직...
        except:
            print("검색 도구를 사용할 수 없습니다.")
    
    return tools

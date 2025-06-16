import os
import requests
import json
import logging
from typing import List, Dict, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class GoogleSearchInput(BaseModel):
    """Google Custom Search API 입력 스키마"""
    query: str = Field(description="검색 쿼리")

class GoogleCustomSearch(BaseTool):
    """Google Custom Search API를 사용한 웹 검색 도구 (원본 로직 기반)"""
    
    name: str = Field(default="google_web_search")
    description: str = Field(default="Google Custom Search API를 사용하여 글로벌 웹 검색을 수행합니다.")
    args_schema: type[BaseModel] = Field(default=GoogleSearchInput)
    
    # API 관련 필드
    api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    search_engine_id: str = Field(default_factory=lambda: os.getenv("GOOGLE_SEARCH_ENGINE_ID", ""))
    
    # 검색 파라미터 필드들
    max_results: int = Field(default=3, description="검색 결과 개수")
    search_type: str = Field(default="web", description="검색 타입")
    topic: str = Field(default="general", description="검색 주제")
    days: int = Field(default=7, description="날짜 제한 (일)")
    include_domains: List[str] = Field(default_factory=list, description="포함할 도메인 리스트")
    exclude_domains: List[str] = Field(default_factory=list, description="제외할 도메인 리스트")
    include_answer: bool = Field(default=False, description="답변 포함 여부")
    include_raw_content: bool = Field(default=False, description="원본 콘텐츠 포함 여부")
    include_images: bool = Field(default=False, description="이미지 검색 여부")
    format_output: bool = Field(default=False, description="출력 형식화 여부")
    date_restrict: Optional[str] = Field(default=None, description="날짜 제한 파라미터")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(self, query: str, run_manager=None) -> str:
        """검색 실행 메서드 - 원본 Google_API 로직 기반"""
        try:
            # API 키 확인
            if not self.api_key or not self.search_engine_id:
                return json.dumps({
                    "error": "Google API 키 또는 검색 엔진 ID가 설정되지 않았습니다.",
                    "results": []
                }, ensure_ascii=False)
            
            # Trash_Link 정의 (원본과 동일)
            trash_link = [
                "tistory", "kin", "youtube", "blog", "book", "news", 
                "dcinside", "fmkorea", "ruliweb", "theqoo", "clien", 
                "mlbpark", "instiz", "todayhumor"
            ]
            
            # 쿼리 전처리 (원본과 동일)
            processed_query = query.replace("|", "OR")
            processed_query += " -filetype:pdf"
            
            # 페이징 설정 (원본과 동일)
            start_pages = []
            wanted_row = min(self.max_results, 100)  # 최대 100개로 제한
            
            for i in range(1, wanted_row + 1000, 10):
                start_pages.append(i)
            
            results = []
            row_count = 0
            
            # 각 페이지별 검색 (원본 로직과 동일)
            for start_page in start_pages:
                try:
                    # URL 구성 (원본과 동일한 방식)
                    encoded_query = quote_plus(processed_query)
                    url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.search_engine_id}&q={encoded_query}&start={start_page}"
                    
                    # 글로벌 검색 파라미터 추가
                    url += "&gl=us&hl=en"
                    
                    # API 호출
                    response = requests.get(url, timeout=10)
                    
                    # 응답 상태 확인
                    if response.status_code != 200:
                        logger.error(f"API 응답 에러: {response.status_code}, {response.text}")
                        continue
                    
                    # JSON 파싱 (안전하게)
                    try:
                        data = response.json()
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 파싱 에러: {e}")
                        continue
                    
                    # API 에러 응답 확인
                    if "error" in data:
                        logger.error(f"Google API 에러: {data['error']}")
                        continue
                    
                    # 검색 결과 추출
                    search_items = data.get("items")
                    
                    # search_items가 None인 경우 처리 (원본과 동일)
                    if search_items is None:
                        logger.warning(f"검색 결과가 없습니다. 페이지: {start_page}")
                        continue
                    
                    # 각 검색 결과 처리 (원본과 동일한 로직)
                    for i, search_item in enumerate(search_items, start=1):
                        try:
                            link = search_item.get("link", "")
                            
                            # Trash_Link 필터링 (원본과 동일)
                            if any(trash in link.lower() for trash in trash_link):
                                continue
                            
                            # 결과 저장
                            title = search_item.get("title", "")
                            description = search_item.get("snippet", "")
                            
                            result = {
                                "title": title,
                                "link": link,
                                "description": description,
                                "displayLink": search_item.get("displayLink", "")
                            }
                            
                            results.append(result)
                            row_count += 1
                            
                            # 결과 개수 제한 (원본과 동일)
                            if row_count >= wanted_row or row_count >= 300:
                                return json.dumps({
                                    "query": query,
                                    "results": results,
                                    "total_results": len(results)
                                }, ensure_ascii=False, indent=2)
                                
                        except Exception as e:
                            logger.error(f"검색 결과 처리 에러: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"페이지 {start_page} 검색 에러: {e}")
                    continue
            
            # 최종 결과 반환
            return json.dumps({
                "query": query,
                "results": results,
                "total_results": len(results)
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Google Custom Search 전체 에러: {str(e)}")
            return json.dumps({
                "error": f"검색 중 오류가 발생했습니다: {str(e)}",
                "results": []
            }, ensure_ascii=False)

class GoogleNewsSearch(BaseTool):
    """Google Custom Search API를 사용한 뉴스 검색 도구 (뉴스 특화)"""
    
    name: str = Field(default="google_news_search")
    description: str = Field(default="Google Custom Search API를 사용하여 글로벌 뉴스를 검색합니다.")
    args_schema: type[BaseModel] = Field(default=GoogleSearchInput)
    
    # API 관련 필드
    api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    search_engine_id: str = Field(default_factory=lambda: os.getenv("GOOGLE_SEARCH_ENGINE_ID", ""))
    
    # 뉴스 검색 파라미터 필드들
    max_results: int = Field(default=3, description="검색 결과 개수")
    days: int = Field(default=7, description="날짜 제한 (일)")
    country: str = Field(default="", description="국가 코드")
    language: str = Field(default="", description="언어 코드")
    category: str = Field(default="", description="뉴스 카테고리")
    date_restrict: Optional[str] = Field(default=None, description="날짜 제한 파라미터")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _run(self, query: str, run_manager=None) -> str:
        """뉴스 검색 실행 메서드"""
        try:
            # API 키 확인
            if not self.api_key or not self.search_engine_id:
                return json.dumps({
                    "error": "Google API 키 또는 검색 엔진 ID가 설정되지 않았습니다.",
                    "results": []
                }, ensure_ascii=False)
            
            # 뉴스 사이트 리스트 (글로벌 뉴스 사이트)
            news_sites = [
                "cnn.com", "bbc.com", "reuters.com", "ap.org", 
                "bloomberg.com", "wsj.com", "nytimes.com", "guardian.com",
                "npr.org", "abcnews.go.com", "cbsnews.com", "nbcnews.com"
            ]
            
            # 뉴스 특화 쿼리 구성
            processed_query = query.replace("|", "OR")
            
            # 뉴스 사이트 제한 추가
            site_query = " OR ".join([f"site:{site}" for site in news_sites])
            processed_query = f"({processed_query}) AND ({site_query})"
            
            results = []
            wanted_row = min(self.max_results, 50)  # 뉴스는 50개로 제한
            
            try:
                # URL 구성
                encoded_query = quote_plus(processed_query)
                url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.search_engine_id}&q={encoded_query}&start=1"
                
                # 뉴스 특화 파라미터
                url += "&gl=us&hl=en"
                
                # 날짜 제한 추가
                if self.days and self.days > 0:
                    if self.days <= 7:
                        url += f"&dateRestrict=d{self.days}"
                    elif self.days <= 30:
                        url += f"&dateRestrict=w{self.days//7}"
                    else:
                        url += f"&dateRestrict=m{self.days//30}"
                
                # API 호출
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    logger.error(f"뉴스 API 응답 에러: {response.status_code}")
                    return json.dumps({
                        "error": f"API 응답 에러: {response.status_code}",
                        "results": []
                    }, ensure_ascii=False)
                
                # JSON 파싱
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"뉴스 JSON 파싱 에러: {e}")
                    return json.dumps({
                        "error": "JSON 파싱 에러",
                        "results": []
                    }, ensure_ascii=False)
                
                # API 에러 확인
                if "error" in data:
                    logger.error(f"Google News API 에러: {data['error']}")
                    return json.dumps({
                        "error": f"Google API 에러: {data['error']}",
                        "results": []
                    }, ensure_ascii=False)
                
                # 검색 결과 처리
                search_items = data.get("items")
                if search_items is None:
                    return json.dumps({
                        "query": query,
                        "results": [],
                        "total_results": 0,
                        "search_type": "news"
                    }, ensure_ascii=False)
                
                # 뉴스 결과 처리
                for search_item in search_items[:wanted_row]:
                    try:
                        result = {
                            "title": search_item.get("title", ""),
                            "link": search_item.get("link", ""),
                            "snippet": search_item.get("snippet", ""),
                            "source": search_item.get("displayLink", ""),
                            "published_date": search_item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time", "")
                        }
                        results.append(result)
                    except Exception as e:
                        logger.error(f"뉴스 결과 처리 에러: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"뉴스 검색 에러: {e}")
                return json.dumps({
                    "error": f"뉴스 검색 중 오류: {str(e)}",
                    "results": []
                }, ensure_ascii=False)
            
            return json.dumps({
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_type": "news"
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Google News Search 전체 에러: {str(e)}")
            return json.dumps({
                "error": f"뉴스 검색 중 오류가 발생했습니다: {str(e)}",
                "results": []
            }, ensure_ascii=False)

import os
import requests
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
    """Google Custom Search API를 사용한 웹 검색 도구 (글로벌 최적화)"""
    
    name: str = "google_web_search"
    description: str = (
        "Google Custom Search API를 사용한 글로벌 웹 검색 도구입니다. "
        "전 세계의 정보를 검색하며, 모든 언어와 국가의 결과를 포함합니다. "
        "일반적인 웹 정보, 연구 자료, 사실 확인 등에 사용하세요."
    )
    args_schema: type[BaseModel] = GoogleSearchInput
    
    def __init__(
        self,
        max_results: int = 3,
        search_type: str = "web",
        date_restrict: Optional[str] = None,
        site_search: Optional[str] = None,
        site_search_filter: str = "i",
        exclude_domains: List[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.max_results = min(max_results, 10)  # Google API 최대값 10
        self.search_type = search_type
        self.date_restrict = date_restrict
        self.site_search = site_search
        self.site_search_filter = site_search_filter
        self.exclude_domains = exclude_domains or []
        
        # 환경변수에서 API 키와 검색 엔진 ID 가져오기
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("GOOGLE_API_KEY와 GOOGLE_SEARCH_ENGINE_ID 환경변수가 필요합니다.")

    def _run(self, query: str) -> str:
        """검색 실행"""
        try:
            results = self._google_search(query)
            return json.dumps(results, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Google 검색 중 오류 발생: {e}")
            return json.dumps([{
                "title": "Error",
                "url": "",
                "content": f"검색 중 오류가 발생했습니다: {str(e)}",
                "score": 0.0,
                "source_type": "ERROR"
            }], ensure_ascii=False)

    def _google_search(self, query: str) -> List[Dict]:
        """Google Custom Search API 호출 (글로벌 최적화)"""
        
        # 기본 파라미터 설정 (글로벌 검색 최적화)
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": self.max_results,
            "hl": "en",  # 영어 인터페이스
            "safe": "off",  # 필터링 최소화
            # gl, lr, cr 파라미터는 설정하지 않아서 글로벌 결과 확보
        }
        
        # 검색 타입 설정
        if self.search_type == "image":
            params["searchType"] = "image"
        
        # 날짜 제한 설정
        if self.date_restrict:
            params["dateRestrict"] = self.date_restrict
        
        # 사이트 검색 설정
        if self.site_search:
            params["siteSearch"] = self.site_search
            params["siteSearchFilter"] = self.site_search_filter
        
        # 제외 도메인 처리 (쿼리에 추가)
        if self.exclude_domains:
            exclude_terms = " ".join([f"-site:{domain}" for domain in self.exclude_domains])
            params["q"] = f"{query} {exclude_terms}"
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            # 결과를 표준 형식으로 변환
            results = []
            for item in items:
                result = {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("snippet", ""),
                    "score": 0.8,  # 기본 신뢰도
                    "source_type": "WEB",
                    "search_engine": "Google Custom Search",
                    "global_search": True
                }
                results.append(result)
            
            logger.info(f"Google 검색 완료 - 쿼리: '{query}', 결과: {len(results)}개")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google API 요청 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"Google 검색 처리 중 오류: {e}")
            raise

class GoogleNewsSearch(GoogleCustomSearch):
    """Google Custom Search API를 사용한 뉴스 검색 도구 (글로벌 최적화)"""
    
    name: str = "google_news_search"
    description: str = (
        "Google Custom Search API를 사용한 글로벌 뉴스 검색 도구입니다. "
        "전 세계의 최신 뉴스, 시사, 현재 이슈를 검색합니다. "
        "모든 언어와 국가의 뉴스를 포함하며, 최신성을 우선시합니다."
    )
    
    def __init__(
        self, 
        max_results: int = 3, 
        date_restrict: str = "w1",  # 기본적으로 1주일 이내
        **kwargs
    ):
        super().__init__(
            max_results=max_results,
            search_type="web",  # 뉴스도 웹 검색
            date_restrict=date_restrict,
            **kwargs
        )

    def _google_search(self, query: str) -> List[Dict]:
        """뉴스 특화 Google Custom Search API 호출"""
        
        # 뉴스 특화 파라미터 설정
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": f"{query} news OR 뉴스 OR ニュース OR новости",  # 다국어 뉴스 키워드 추가
            "num": self.max_results,
            "hl": "en",  # 영어 인터페이스
            "safe": "off",  # 필터링 최소화
            "sort": "date",  # 날짜순 정렬
            # gl, lr, cr 파라미터는 설정하지 않아서 글로벌 뉴스 확보
        }
        
        # 날짜 제한 설정 (뉴스는 기본적으로 최신성 중요)
        if self.date_restrict:
            params["dateRestrict"] = self.date_restrict
        
        # 뉴스 사이트 우선 검색 (글로벌 뉴스 사이트)
        news_sites = [
            "site:news.google.com", "site:reuters.com", "site:bbc.com", 
            "site:cnn.com", "site:nytimes.com", "site:washingtonpost.com",
            "site:guardian.com", "site:ap.org", "site:bloomberg.com",
            "site:naver.com", "site:daum.net", "site:chosun.com",
            "site:joongang.co.kr", "site:donga.com"
        ]
        news_query = f"({' OR '.join(news_sites)}) {query}"
        params["q"] = news_query
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            # 뉴스 결과를 표준 형식으로 변환
            results = []
            for item in items:
                result = {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("snippet", ""),
                    "score": 0.9,  # 뉴스는 높은 신뢰도
                    "source_type": "NEWS",
                    "recency": "CURRENT",
                    "priority": "HIGH",
                    "search_engine": "Google Custom Search",
                    "global_search": True,
                    "date_restrict": self.date_restrict
                }
                results.append(result)
            
            logger.info(f"Google 뉴스 검색 완료 - 쿼리: '{query}', 결과: {len(results)}개")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google 뉴스 API 요청 실패: {e}")
            raise
        except Exception as e:
            logger.error(f"Google 뉴스 검색 처리 중 오류: {e}")
            raise


from typing import Any, List
from langchain_utils.tools.google_search import GoogleCustomSearch  # 변경된 import
from .base import BaseTool


class WebSearchTool(BaseTool[GoogleCustomSearch]):  # 타입 변경
    """Google Custom Search API를 사용한 글로벌 웹 검색 도구 클래스"""

    def __init__(
        self,
        topic: str = "general",
        days: int = 7,
        max_results: int = 3,
        include_answer: bool = False,  # 무시됨
        include_raw_content: bool = False,  # 무시됨
        include_images: bool = False,
        format_output: bool = False,  # 무시됨
        include_domains: List[str] = [],
        exclude_domains: List[str] = [],
        date_restrict: str = None,
        site_search: str = None,
    ):
        """WebSearchTool 초기화 메서드 (기존 파라미터 완전 호환)"""
        super().__init__()
        self.topic = topic
        self.days = days
        self.max_results = max_results
        self.include_answer = include_answer  # 호환성을 위해 유지
        self.include_raw_content = include_raw_content  # 호환성을 위해 유지
        self.include_images = include_images
        self.format_output = format_output  # 호환성을 위해 유지
        self.include_domains = include_domains
        self.exclude_domains = exclude_domains
        self.date_restrict = date_restrict
        self.site_search = site_search

    def _create_tool(self) -> GoogleCustomSearch:
        """GoogleCustomSearch 객체를 생성하고 설정하는 내부 메서드"""
        
        # include_domains를 siteSearch로 변환
        site_search_query = None
        site_search_filter = "i"
        
        if self.include_domains:
            # 여러 도메인을 OR로 연결
            site_search_query = " OR ".join([f"site:{domain}" for domain in self.include_domains])
        elif self.site_search:
            site_search_query = self.site_search
            
        # days를 dateRestrict로 변환
        date_restrict = None
        if self.topic == "news" or self.date_restrict:
            if self.date_restrict:
                date_restrict = self.date_restrict
            elif self.days:
                if self.days <= 1:
                    date_restrict = "d1"
                elif self.days <= 7:
                    date_restrict = "w1"
                elif self.days <= 30:
                    date_restrict = "m1"
                else:
                    date_restrict = "y1"
        
        # 검색 타입 결정
        search_type = "image" if self.include_images else "web"
            
        search = GoogleCustomSearch(
            max_results=self.max_results,
            search_type=search_type,
            date_restrict=date_restrict,
            site_search=site_search_query,
            site_search_filter=site_search_filter,
            exclude_domains=self.exclude_domains
        )
        
        search.name = "web_search"
        search.description = (
            "Search the web globally for general information, research, facts, and non-news content "
            "using Google Custom Search API. This tool searches worldwide across all languages and countries "
            "for comprehensive web searches when you need general information that is not specifically about recent news or current events."
        )
        return search

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """도구를 실행하는 메서드"""
        tool = self._create_tool()
        return tool(*args, **kwargs)



import json
import logging
from typing import Any, List, Optional
from langchain_core.tools import BaseTool as LangChainBaseTool
from langchain_utils.tools.google_search import GoogleNewsSearch  # 변경된 import
from .base import BaseTool

# 로거 설정
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


class EnhancedNewsSearchTool(BaseTool[LangChainBaseTool]):
    """Google Custom Search API를 사용한 글로벌 뉴스 검색 도구 클래스"""

    def __init__(
        self,
        max_results: int = 3,
        search_type: str = "keyword",  # "keyword" or "latest"
        use_morphological_analysis: bool = False,  # 호환성을 위해 유지 (무시됨)
        optimize_query: bool = False,  # 호환성을 위해 유지 (무시됨)
        date_restrict: str = "w1",  # 기본적으로 1주일 이내
        site_search: str = None,
    ):
        """EnhancedNewsSearchTool 초기화 메서드 (기존 파라미터 완전 호환)"""
        logger.info(f"EnhancedNewsSearchTool 초기화 - max_results: {max_results}, "
                   f"search_type: {search_type}, date_restrict: {date_restrict}")
        super().__init__()
        self.max_results = max_results
        self.search_type = search_type
        self.use_morphological_analysis = use_morphological_analysis  # 호환성을 위해 유지
        self.optimize_query = optimize_query  # 호환성을 위해 유지
        self.date_restrict = date_restrict
        self.site_search = site_search
        
        try:
            self.google_news_search = GoogleNewsSearch(
                max_results=max_results,
                date_restrict=date_restrict,
                site_search=site_search
            )
            logger.info("GoogleNewsSearch 인스턴스 생성 완료")
            
        except Exception as e:
            logger.error(f"GoogleNewsSearch 인스턴스 생성 실패: {e}")
            raise

    def _create_tool(self) -> LangChainBaseTool:
        """EnhancedNewsSearcher 도구를 생성하고 설정하는 내부 메서드"""
        logger.info("EnhancedNewsSearcher 도구 생성 시작")
        
        class EnhancedNewsSearcher(LangChainBaseTool):
            name: str = "news_search"
            description: str = """Search for recent news articles and current events globally using Google Custom Search API. 
            This tool is specifically designed for finding latest news, breaking news, current events, and recent updates 
            from around the world in all languages. It provides more accurate and up-to-date news content compared to general web search.
            Use this tool when users ask about news, current events, recent happenings, or when you need the most recent information."""
            
            max_results: int = 3
            search_type: str = "keyword"
            optimize_query: bool = False  # 호환성을 위해 유지
            google_news_search: GoogleNewsSearch = None
            date_restrict: str = "w1"

            def __init__(self, max_results: int, search_type: str, optimize_query: bool, 
                        google_news_search: GoogleNewsSearch, date_restrict: str):
                # 부모 클래스 초기화를 먼저 수행 (필드와 함께)
                super().__init__(
                    max_results=max_results,
                    search_type=search_type,
                    optimize_query=optimize_query,
                    google_news_search=google_news_search,
                    date_restrict=date_restrict
                )
                logger.info(f"EnhancedNewsSearcher 초기화 완료 - max_results: {max_results}, "
                           f"search_type: {search_type}, date_restrict: {date_restrict}")

            def _run(self, query: str = None) -> str:
                """Google Custom Search API를 사용한 글로벌 뉴스 검색 실행"""
                logger.info(f"Google 글로벌 뉴스 검색 실행 - query: '{query}', search_type: {self.search_type}")
                
                try:
                    if self.search_type == "latest":
                        logger.info("최신 뉴스 검색 실행 (글로벌)")
                        # 최신 뉴스의 경우 다국어 뉴스 키워드로 검색
                        search_query = "latest news OR breaking news OR 최신뉴스 OR 속보 OR ニュース OR новости"
                    else:
                        logger.info(f"키워드 뉴스 검색 실행 (글로벌) - keyword: '{query}'")
                        search_query = query if query else "news"
                    
                    # Google Custom Search API 호출
                    result = self.google_news_search._run(search_query)
                    
                    # 결과가 JSON 문자열인 경우 파싱
                    if isinstance(result, str):
                        try:
                            results = json.loads(result)
                        except json.JSONDecodeError:
                            logger.error("검색 결과 JSON 파싱 실패")
                            results = []
                    else:
                        results = result if isinstance(result, list) else []
                    
                    logger.info(f"검색 결과 수: {len(results) if results else 0}")
                    
                    if not results:
                        logger.warning("검색 결과가 없습니다")
                        return json.dumps([{
                            "title": "No news found", 
                            "url": "", 
                            "content": "No news articles found for the given query.", 
                            "score": 0.0,
                            "source_type": "NEWS",
                            "search_engine": "Google Custom Search",
                            "global_search": True
                        }], ensure_ascii=False, indent=2)
                    
                    # 결과를 표준 형식으로 변환 (기존 호환성 유지)
                    formatted_results = []
                    for i, result in enumerate(results):
                        logger.debug(f"결과 {i+1} 처리: {result.get('url', 'No URL')}")
                        
                        formatted_result = {
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "content": result.get("content", ""),
                            "score": result.get("score", 0.9),
                            "source_type": "NEWS",
                            "recency": "CURRENT",
                            "priority": "HIGH",
                            "search_engine": "Google Custom Search",
                            "global_search": True,
                            "date_restrict": self.date_restrict,
                            "analysis_used": False  # 호환성을 위해 추가
                        }
                        
                        # 첫 번째 결과에 검색 정보 추가 (기존 호환성)
                        if i == 0:
                            formatted_result["original_query"] = query
                            formatted_result["search_type"] = self.search_type
                            formatted_result["max_results"] = self.max_results
                            formatted_result["optimized_query"] = query  # 호환성을 위해 추가
                        
                        formatted_results.append(formatted_result)
                    
                    logger.info(f"Google 글로벌 뉴스 검색 완료 - {len(formatted_results)}개 결과 반환")
                    return json.dumps(formatted_results, ensure_ascii=False, indent=2)
                    
                except Exception as e:
                    logger.error(f"Google 뉴스 검색 중 오류 발생: {str(e)}", exc_info=True)
                    return json.dumps([{
                        "title": "Error", 
                        "url": "", 
                        "content": f"Error occurred during Google news search: {str(e)}", 
                        "score": 0.0,
                        "source_type": "NEWS",
                        "search_engine": "Google Custom Search",
                        "global_search": True
                    }], ensure_ascii=False, indent=2)

            async def _arun(self, query: str = None) -> str:
                """비동기 Google 뉴스 검색 실행"""
                logger.info(f"비동기 Google 글로벌 뉴스 검색 실행 - query: '{query}'")
                return self._run(query)

        try:
            enhanced_news_searcher = EnhancedNewsSearcher(
                max_results=self.max_results,
                search_type=self.search_type,
                optimize_query=self.optimize_query,
                google_news_search=self.google_news_search,
                date_restrict=self.date_restrict
            )
            enhanced_news_searcher.name = "news_search"
            logger.info("EnhancedNewsSearcher 인스턴스 생성 완료")
            return enhanced_news_searcher
        except Exception as e:
            logger.error(f"EnhancedNewsSearcher 생성 실패: {e}", exc_info=True)
            raise

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """도구를 실행하는 메서드"""
        logger.info(f"EnhancedNewsSearchTool 호출 - args: {args}, kwargs: {kwargs}")
        tool = self._create_tool()
        return tool(*args, **kwargs)


# 기존 NewsSearchTool과의 호환성을 위한 별칭 및 래퍼
class NewsSearchTool(EnhancedNewsSearchTool):
    """기존 NewsSearchTool과 완전 호환되는 래퍼 클래스"""
    
    def __init__(
        self,
        max_results: int = 3,
        search_type: str = "keyword",
        date_restrict: str = "w1",
    ):
        # Google Custom Search API 사용으로 형태소 분석 기능은 비활성화하지만 호환성 유지
        super().__init__(
            max_results=max_results,
            search_type=search_type,
            use_morphological_analysis=False,  # 호환성을 위해 유지
            optimize_query=False,  # 호환성을 위해 유지
            date_restrict=date_restrict
        )


# 사용 예제 및 테스트
if __name__ == "__main__":
    # Google Custom Search를 사용한 글로벌 뉴스 검색 도구 생성
    enhanced_tool = EnhancedNewsSearchTool(
        max_results=5,
        date_restrict="w1"  # 1주일 이내
    )
    
    # 도구 정보 출력
    print("=== Google Custom Search 글로벌 뉴스 도구 정보 ===")
    tool_info = enhanced_tool.get_tool_info()
    for key, value in tool_info.items():
        print(f"{key}: {value}")
    print()
    
    # LangChain 도구 생성
    news_tool = enhanced_tool.create()
    
    # 글로벌 검색 테스트
    print("=== Google Custom Search 글로벌 뉴스 검색 테스트 ===")
    test_queries = [
        "Tesla stock price",
        "Bitcoin cryptocurrency news",
        "삼성전자 주가",
        "Ukraine war latest"
    ]
    
    for query in test_queries:
        print(f"\n검색 쿼리: '{query}'")
        print("-" * 50)
        
        try:
            result = news_tool.invoke(query)
            
            # JSON 결과 파싱하여 보기 좋게 출력
            import json
            parsed_result = json.loads(result)
            
            for i, article in enumerate(parsed_result, 1):
                print(f"{i}. {article.get('title', 'No Title')}")
                print(f"   검색 엔진: {article.get('search_engine', 'Unknown')}")
                print(f"   글로벌 검색: {article.get('global_search', False)}")
                print(f"   날짜 제한: {article.get('date_restrict', 'None')}")
                print(f"   URL: {article.get('url', 'No URL')}")
                print()
                
        except Exception as e:
            print(f"검색 중 오류 발생: {e}")
    
    print("\n=== 호환성 테스트 ===")
    # 기존 방식과 동일한 인터페이스 테스트
    compatible_tool = NewsSearchTool(
        max_results=3,
        search_type="keyword"
    )
    
    compatible_news_tool = compatible_tool.create()
    query = "Apple iPhone news"
    
    print(f"테스트 쿼리: '{query}'")
    try:
        result = compatible_news_tool.invoke(query)
        parsed = json.loads(result)
        print(f"결과 수: {len(parsed)}")
        for i, article in enumerate(parsed, 1):
            print(f"{i}. {article.get('title', 'No Title')[:50]}...")
            print(f"   글로벌 검색: {article.get('global_search', False)}")
            print(f"   검색 엔진: {article.get('search_engine', 'Unknown')}")
    except Exception as e:
        print(f"오류: {e}")


import importlib
from typing import Any

_module_lookup = {
    "GoogleNews": "tools.news",
    "TavilySearch": "tools.tavily",
    "GoogleCustomSearch": "tools.google_search",  # 추가
    "GoogleNewsSearch": "tools.google_search",    # 추가
}

from .news import GoogleNews
from .tavily import TavilySearch
from .google_search import GoogleCustomSearch, GoogleNewsSearch  # 추가


def __getattr__(name: str) -> Any:
    if name in _module_lookup:
        module = importlib.import_module(_module_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "GoogleNews",
    "TavilySearch",
    "GoogleCustomSearch",  # 추가
    "GoogleNewsSearch",    # 추가
]

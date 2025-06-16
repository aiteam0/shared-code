from typing import Any, List
from langchain_utils.tools.google_search import GoogleCustomSearch
from .base import BaseTool


class WebSearchTool(BaseTool[GoogleCustomSearch]):
    """Google Custom Search API를 사용한 웹 검색 도구 클래스"""

    def __init__(
        self,
        topic: str = "general",
        days: int = 7,
        max_results: int = 3,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        format_output: bool = False,
        include_domains: List[str] = [],
        exclude_domains: List[str] = [],
        date_restrict: str = None,
        site_search: str = None,
    ):
        """WebSearchTool 초기화 메서드"""
        super().__init__()
        self.topic = topic
        self.days = days
        self.max_results = max_results
        self.include_answer = include_answer
        self.include_raw_content = include_raw_content
        self.include_images = include_images
        self.format_output = format_output
        self.include_domains = include_domains
        self.exclude_domains = exclude_domains
        self.date_restrict = date_restrict
        self.site_search = site_search

    def _create_tool(self) -> GoogleCustomSearch:
        """GoogleCustomSearch 객체를 생성하고 설정하는 내부 메서드"""
        
        # include_domains가 있으면 site_search로 변환
        site_search_query = None
        if self.include_domains:
            site_search_query = " OR ".join([f"site:{domain}" for domain in self.include_domains])
        elif self.site_search:
            site_search_query = self.site_search
            
        # 날짜 제한 설정 (topic이 news인 경우에만)
        date_restrict = None
        if self.topic == "news" and self.days:
            if self.days <= 1:
                date_restrict = "d1"
            elif self.days <= 7:
                date_restrict = "w1"
            elif self.days <= 30:
                date_restrict = "m1"
            else:
                date_restrict = "y1"
        elif self.date_restrict:
            date_restrict = self.date_restrict
            
        search = GoogleCustomSearch(
            max_results=self.max_results,
            search_type="web",
            date_restrict=date_restrict,
            site_search=site_search_query,
            exclude_domains=self.exclude_domains
        )
        search.name = "web_search"
        search.description = "Search the web for general information, research, facts, and non-news content using Google Custom Search API. Use this for comprehensive web searches when you need general information that is not specifically about recent news or current events."
        return search

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """도구를 실행하는 메서드"""
        tool = self._create_tool()
        return tool(*args, **kwargs)


import json
import logging
from typing import Any, List, Optional
from langchain_core.tools import BaseTool as LangChainBaseTool
from langchain_utils.tools.google_search import GoogleNewsSearch
from .base import BaseTool

# 로거 설정
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


class EnhancedNewsSearchTool(BaseTool[LangChainBaseTool]):
    """Google Custom Search API를 사용한 향상된 뉴스 검색 도구 클래스"""

    def __init__(
        self,
        max_results: int = 3,
        search_type: str = "keyword",  # "keyword" or "latest"
        use_morphological_analysis: bool = False,  # Google API에서는 사용하지 않음
        optimize_query: bool = False,  # Google API에서는 사용하지 않음
        date_restrict: str = "w1",  # 기본적으로 1주일 이내
        site_search: str = None,
    ):
        """EnhancedNewsSearchTool 초기화 메서드"""
        logger.info(f"EnhancedNewsSearchTool 초기화 - max_results: {max_results}, "
                   f"search_type: {search_type}, date_restrict: {date_restrict}")
        super().__init__()
        self.max_results = max_results
        self.search_type = search_type
        self.use_morphological_analysis = use_morphological_analysis
        self.optimize_query = optimize_query
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
            description: str = """Search for recent news articles and current events using Google Custom Search API. 
            This tool is specifically designed for finding latest news, breaking news, current events, and recent updates. 
            It provides more accurate and up-to-date news content compared to general web search.
            Use this tool when users ask about news, current events, recent happenings, or when you need the most recent information."""
            
            max_results: int = 3
            search_type: str = "keyword"
            optimize_query: bool = False
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
                """Google Custom Search API를 사용한 뉴스 검색 실행"""
                logger.info(f"Google 뉴스 검색 실행 - query: '{query}', search_type: {self.search_type}")
                
                try:
                    if self.search_type == "latest":
                        logger.info("최신 뉴스 검색 실행 (쿼리 없이)")
                        # 최신 뉴스의 경우 일반적인 뉴스 키워드로 검색
                        search_query = "뉴스 OR 최신 OR 속보"
                    else:
                        logger.info(f"키워드 뉴스 검색 실행 - keyword: '{query}'")
                        search_query = query if query else "뉴스"
                    
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
                            "search_engine": "Google Custom Search"
                        }], ensure_ascii=False, indent=2)
                    
                    # 결과를 표준 형식으로 변환
                    formatted_results = []
                    for i, result in enumerate(results):
                        logger.debug(f"결과 {i+1} 처리: {result.get('url', 'No URL')}")
                        
                        formatted_result = {
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "content": result.get("content", ""),
                            "score": result.get("score", 0.8),
                            "source_type": "NEWS",
                            "recency": "CURRENT",
                            "priority": "HIGH",
                            "search_engine": "Google Custom Search",
                            "date_restrict": self.date_restrict
                        }
                        
                        # 첫 번째 결과에 검색 정보 추가
                        if i == 0:
                            formatted_result["original_query"] = query
                            formatted_result["search_type"] = self.search_type
                            formatted_result["max_results"] = self.max_results
                        
                        formatted_results.append(formatted_result)
                    
                    logger.info(f"Google 뉴스 검색 완료 - {len(formatted_results)}개 결과 반환")
                    return json.dumps(formatted_results, ensure_ascii=False, indent=2)
                    
                except Exception as e:
                    logger.error(f"Google 뉴스 검색 중 오류 발생: {str(e)}", exc_info=True)
                    return json.dumps([{
                        "title": "Error", 
                        "url": "", 
                        "content": f"Error occurred during Google news search: {str(e)}", 
                        "score": 0.0,
                        "source_type": "NEWS",
                        "search_engine": "Google Custom Search"
                    }], ensure_ascii=False, indent=2)

            async def _arun(self, query: str = None) -> str:
                """비동기 Google 뉴스 검색 실행"""
                logger.info(f"비동기 Google 뉴스 검색 실행 - query: '{query}'")
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
    """기존 NewsSearchTool과 호환되는 래퍼 클래스"""
    
    def __init__(
        self,
        max_results: int = 3,
        search_type: str = "keyword",
        date_restrict: str = "w1",
    ):
        # Google Custom Search API 사용으로 형태소 분석 기능은 비활성화
        super().__init__(
            max_results=max_results,
            search_type=search_type,
            use_morphological_analysis=False,
            optimize_query=False,
            date_restrict=date_restrict
        )


# 사용 예제
if __name__ == "__main__":
    # Google Custom Search를 사용한 뉴스 검색 도구 생성
    enhanced_tool = EnhancedNewsSearchTool(
        max_results=5,
        date_restrict="w1"  # 1주일 이내
    )
    
    # 도구 정보 출력
    print("=== Google Custom Search 뉴스 도구 정보 ===")
    tool_info = enhanced_tool.get_tool_info()
    for key, value in tool_info.items():
        print(f"{key}: {value}")
    print()
    
    # LangChain 도구 생성
    news_tool = enhanced_tool.create()
    
    # 검색 테스트
    print("=== Google Custom Search 뉴스 검색 테스트 ===")
    test_queries = [
        "삼성전자 주가",
        "한국 부동산 정책"
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
    query = "비트코인 가격"
    
    print(f"테스트 쿼리: '{query}'")
    try:
        result = compatible_news_tool.invoke(query)
        parsed = json.loads(result)
        print(f"결과 수: {len(parsed)}")
        for i, article in enumerate(parsed, 1):
            print(f"{i}. {article.get('title', 'No Title')[:50]}...")
            print(f"   검색 엔진: {article.get('search_engine', 'Unknown')}")
    except Exception as e:
        print(f"오류: {e}")

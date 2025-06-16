from pydantic import BaseModel, Field

class GoogleCustomSearch(BaseTool):
    """Google Custom Search API를 사용한 웹 검색 도구 (글로벌 최적화)"""
    
    name: str = Field(default="google_web_search")
    description: str = Field(default=(
        "Google Custom Search API를 사용한 글로벌 웹 검색 도구입니다. "
        "전 세계의 정보를 검색하며, 모든 언어와 국가의 결과를 포함합니다. "
        "일반적인 웹 정보, 연구 자료, 사실 확인 등에 사용하세요."
    ))
    args_schema: type[BaseModel] = Field(default=GoogleSearchInput)
    
    # 추가 필드들을 Pydantic 필드로 정의
    max_results: int = Field(default=3)
    search_type: str = Field(default="web")
    date_restrict: Optional[str] = Field(default=None)
    site_search: Optional[str] = Field(default=None)
    site_search_filter: str = Field(default="i")
    exclude_domains: List[str] = Field(default_factory=list)
    api_key: Optional[str] = Field(default=None)
    search_engine_id: Optional[str] = Field(default=None)
    
    def __init__(self, **kwargs):
        # 환경변수에서 API 키 설정
        if 'api_key' not in kwargs:
            kwargs['api_key'] = os.getenv("GOOGLE_API_KEY")
        if 'search_engine_id' not in kwargs:
            kwargs['search_engine_id'] = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
            
        super().__init__(**kwargs)
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("GOOGLE_API_KEY와 GOOGLE_SEARCH_ENGINE_ID 환경변수가 필요합니다.")
        
        # max_results 제한
        if self.max_results > 10:
            self.max_results = 10


class GoogleNewsSearch(GoogleCustomSearch):
    """Google Custom Search API를 사용한 뉴스 검색 도구 (글로벌 최적화)"""
    
    name: str = Field(default="google_news_search")
    description: str = Field(default=(
        "Google Custom Search API를 사용한 글로벌 뉴스 검색 도구입니다. "
        "전 세계의 최신 뉴스, 시사, 현재 이슈를 검색합니다. "
        "모든 언어와 국가의 뉴스를 포함하며, 최신성을 우선시합니다."
    ))
    
    def __init__(self, date_restrict: str = "w1", **kwargs):
        kwargs['date_restrict'] = date_restrict
        kwargs['search_type'] = "web"
        super().__init__(**kwargs)

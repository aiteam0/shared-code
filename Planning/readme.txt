class GoogleCustomSearch(BaseTool):
    """Google Custom Search API를 사용한 웹 검색 도구 (글로벌 최적화)"""
    
    name: str = Field(default="google_web_search")
    description: str = Field(default="Google Custom Search API를 사용하여 글로벌 웹 검색을 수행합니다.")
    args_schema: type[BaseModel] = Field(default=GoogleSearchInput)
    
    # 모든 파라미터를 Pydantic 필드로 명시적 정의
    max_results: int = Field(default=3, description="검색 결과 개수 (1-10)")
    search_type: str = Field(default="web", description="검색 타입 (web/image)")
    topic: str = Field(default="general", description="검색 주제")
    days: int = Field(default=7, description="날짜 제한 (일)")
    include_domains: List[str] = Field(default_factory=list, description="포함할 도메인 리스트")
    exclude_domains: List[str] = Field(default_factory=list, description="제외할 도메인 리스트")
    include_answer: bool = Field(default=False, description="답변 포함 여부 (무시됨)")
    include_raw_content: bool = Field(default=False, description="원본 콘텐츠 포함 여부 (무시됨)")
    include_images: bool = Field(default=False, description="이미지 검색 여부")
    format_output: bool = Field(default=False, description="출력 형식화 여부")
    date_restrict: Optional[str] = Field(default=None, description="날짜 제한 파라미터")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class GoogleNewsSearch(BaseTool):
    """Google Custom Search API를 사용한 뉴스 검색 도구 (글로벌 최적화)"""
    
    name: str = Field(default="google_news_search")
    description: str = Field(default="Google Custom Search API를 사용하여 글로벌 뉴스를 검색합니다.")
    args_schema: type[BaseModel] = Field(default=GoogleNewsInput)
    
    # 모든 파라미터를 Pydantic 필드로 명시적 정의
    max_results: int = Field(default=3, description="검색 결과 개수 (1-10)")
    days: int = Field(default=7, description="날짜 제한 (일)")
    country: str = Field(default="", description="국가 코드")
    language: str = Field(default="", description="언어 코드")
    category: str = Field(default="", description="뉴스 카테고리")
    date_restrict: Optional[str] = Field(default=None, description="날짜 제한 파라미터")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

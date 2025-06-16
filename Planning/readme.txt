class GoogleCustomSearch(BaseTool):
    """Google Custom Search API를 사용한 웹 검색 도구"""
    
    name: str = Field(default="google_web_search")
    description: str = Field(default="Google Custom Search API를 사용하여 웹 검색을 수행합니다.")
    args_schema: type[BaseModel] = Field(default=GoogleSearchInput)
    
    # 환경변수를 __init__에서 로드하도록 수정
    api_key: Optional[str] = Field(default=None)
    search_engine_id: Optional[str] = Field(default=None)
    
    # 기타 필드들...
    max_results: int = Field(default=3)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 환경변수를 __init__에서 로드
        if self.api_key is None:
            self.api_key = os.getenv("GOOGLE_API_KEY")
        if self.search_engine_id is None:
            self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        # API 키 검증
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        if not self.search_engine_id:
            raise ValueError("GOOGLE_SEARCH_ENGINE_ID 환경변수가 설정되지 않았습니다.")
        
        # API 키 형식 검증
        if not self.api_key.startswith("AIza"):
            raise ValueError("GOOGLE_API_KEY 형식이 올바르지 않습니다. 'AIza'로 시작해야 합니다.")


def _run(self, query: str, run_manager=None) -> str:
    """검색 실행 메서드"""
    try:
        # 디버깅 로그 추가
        logger.info(f"API 키 확인: {self.api_key[:10]}..." if self.api_key else "API 키 없음")
        logger.info(f"검색 엔진 ID: {self.search_engine_id}")
        
        # API 키 확인
        if not self.api_key or not self.search_engine_id:
            error_msg = f"API 설정 오류 - API키: {'있음' if self.api_key else '없음'}, 검색엔진ID: {'있음' if self.search_engine_id else '없음'}"
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "results": []
            }, ensure_ascii=False)
        
        # URL 구성 및 로깅
        encoded_query = quote_plus(query)
        url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.search_engine_id}&q={encoded_query}&start=1"
        logger.info(f"요청 URL: {url[:100]}...")  # URL 일부만 로그
        
        # API 호출
        response = requests.get(url, timeout=10)
        logger.info(f"응답 상태 코드: {response.status_code}")
        
        # 응답 내용 로깅 (에러인 경우)
        if response.status_code != 200:
            logger.error(f"API 응답 에러: {response.text}")
            return json.dumps({
                "error": f"API 응답 에러: {response.status_code} - {response.text}",
                "results": []
            }, ensure_ascii=False)


class GoogleCustomSearch(BaseTool):
    """Google Custom Search API를 사용한 웹 검색 도구 (글로벌 최적화)"""
    
    # ... 기존 필드들 ...
    
    def _run(self, query: str, run_manager=None) -> str:
        """검색 실행 메서드"""
        try:
            # API 키 확인
            if not self.api_key or not self.search_engine_id:
                return json.dumps({
                    "error": "Google API 키 또는 검색 엔진 ID가 설정되지 않았습니다.",
                    "results": []
                })
            
            # 검색 파라미터 구성
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(self.max_results, 10),  # 최대 10개
                "searchType": "image" if self.include_images else "web"
            }
            
            # 글로벌 검색 최적화
            params["gl"] = "us"  # 글로벌 결과
            params["hl"] = "en"  # 영어 인터페이스
            
            # 날짜 제한 설정
            if self.days and self.days > 0:
                if self.days <= 7:
                    params["dateRestrict"] = f"d{self.days}"
                elif self.days <= 30:
                    params["dateRestrict"] = f"w{self.days//7}"
                else:
                    params["dateRestrict"] = f"m{self.days//30}"
            
            # 도메인 필터링
            if self.include_domains:
                params["siteSearch"] = " OR ".join(self.include_domains)
                params["siteSearchFilter"] = "i"
            elif self.exclude_domains:
                params["siteSearch"] = " OR ".join(self.exclude_domains)
                params["siteSearchFilter"] = "e"
            
            # API 호출
            url = "https://www.googleapis.com/customsearch/v1"
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            search_items = data.get("items", [])
            
            # 결과 포맷팅
            results = []
            for item in search_items:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "displayLink": item.get("displayLink", "")
                }
                results.append(result)
            
            return json.dumps({
                "query": query,
                "results": results,
                "total_results": len(results)
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Google Custom Search 에러: {str(e)}")
            return json.dumps({
                "error": f"검색 중 오류가 발생했습니다: {str(e)}",
                "results": []
            })


class GoogleNewsSearch(BaseTool):
    """Google Custom Search API를 사용한 뉴스 검색 도구 (글로벌 최적화)"""
    
    # ... 기존 필드들 ...
    
    def _run(self, query: str, run_manager=None) -> str:
        """뉴스 검색 실행 메서드"""
        try:
            # API 키 확인
            if not self.api_key or not self.search_engine_id:
                return json.dumps({
                    "error": "Google API 키 또는 검색 엔진 ID가 설정되지 않았습니다.",
                    "results": []
                })
            
            # 뉴스 검색 파라미터 구성
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(self.max_results, 10),
                "searchType": "web"
            }
            
            # 글로벌 뉴스 검색 최적화
            params["gl"] = "us"  # 글로벌 결과
            params["hl"] = "en"  # 영어 인터페이스
            
            # 뉴스 특화 설정
            if self.days and self.days > 0:
                if self.days <= 7:
                    params["dateRestrict"] = f"d{self.days}"
                elif self.days <= 30:
                    params["dateRestrict"] = f"w{self.days//7}"
                else:
                    params["dateRestrict"] = f"m{self.days//30}"
            
            # 뉴스 사이트 우선 검색
            news_sites = [
                "cnn.com", "bbc.com", "reuters.com", "ap.org", 
                "bloomberg.com", "wsj.com", "nytimes.com", "guardian.com"
            ]
            params["siteSearch"] = " OR ".join(news_sites)
            params["siteSearchFilter"] = "i"
            
            # 날짜순 정렬 (가능한 경우)
            params["sort"] = "date"
            
            # API 호출
            url = "https://www.googleapis.com/customsearch/v1"
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            search_items = data.get("items", [])
            
            # 뉴스 결과 포맷팅
            results = []
            for item in search_items:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("displayLink", ""),
                    "published_date": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time", "")
                }
                results.append(result)
            
            return json.dumps({
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_type": "news"
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Google News Search 에러: {str(e)}")
            return json.dumps({
                "error": f"뉴스 검색 중 오류가 발생했습니다: {str(e)}",
                "results": []
            })

import os
import requests
import json
import logging
from typing import List, Dict, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

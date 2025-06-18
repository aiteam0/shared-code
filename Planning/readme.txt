import os
import random
from typing import Optional, List
from threading import Lock

class EnvRotator:
    """환경변수 로테이션 관리 클래스 - 여러 환경변수를 순환하며 사용"""
    
    _counters = {}  # 각 prefix별 현재 인덱스 저장
    _lock = Lock()  # 쓰레드 안전성 보장
    
    @classmethod
    def get_rotated_env(cls, prefix: str, mode: str = "round_robin", default: Optional[str] = None) -> Optional[str]:
        """
        환경변수를 로테이션하며 가져오기
        
        Args:
            prefix: 환경변수 접두사 (예: "OLLAMA_BASE_URL", "TAVILY_API_KEY")
            mode: "round_robin" (순차적) 또는 "random" (랜덤)
            default: 환경변수가 없을 때 기본값
            
        Returns:
            선택된 환경변수 값 또는 None
        """
        # 1. prefix_1, prefix_2, ... 형태의 환경변수들 수집
        env_values = []
        counter = 1
        while True:
            env_key = f"{prefix}_{counter}"
            env_value = os.environ.get(env_key)
            if env_value:
                env_values.append(env_value)
                counter += 1
            else:
                break
        
        # 2. 환경변수가 없으면 기본 환경변수 확인
        if not env_values:
            base_value = os.environ.get(prefix)
            if base_value:
                return base_value
            return default
        
        # 3. 모드에 따라 선택
        if mode == "random":
            return random.choice(env_values)
        else:  # round_robin
            with cls._lock:
                if prefix not in cls._counters:
                    cls._counters[prefix] = 0
                
                selected_value = env_values[cls._counters[prefix]]
                cls._counters[prefix] = (cls._counters[prefix] + 1) % len(env_values)
                return selected_value

# 편의 함수들
def get_ollama_base_url(mode: str = "round_robin") -> str:
    """Ollama Base URL을 로테이션하며 가져오기"""
    return EnvRotator.get_rotated_env("OLLAMA_BASE_URL", mode, "http://localhost:11434")

def get_tavily_api_key(mode: str = "round_robin") -> Optional[str]:
    """Tavily API Key를 로테이션하며 가져오기"""
    return EnvRotator.get_rotated_env("TAVILY_API_KEY", mode)

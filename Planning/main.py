# PyTorch + Streamlit 호환성 패치
import os
try:
    import torch
    # Streamlit file watcher와 PyTorch 충돌 해결
    torch.classes.__path__ = []
    print("PyTorch-Streamlit 호환성 패치 적용 완료")
except ImportError:
    # torch가 설치되지 않은 경우
    pass
except Exception as e:
    print(f"PyTorch 패치 적용 중 오류 (무시 가능): {e}")

# 대안: Streamlit file watcher 비활성화 (필요시)
# os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

from attr import dataclass
import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_utils import logging as langsmith_logging
from langchain_utils.messages import random_uuid
from modules.agent import create_agent_executor
from dotenv import load_dotenv
from modules.handler import stream_handler, format_search_result
from modules.tools import WebSearchTool
from modules.news_tool import NewsSearchTool
from modules.deep_research_agent import DeepResearchAgent
from modules.deep_research_handler import (
    deep_research_stream_handler, 
    show_feedback_questions_ui
)
from modules.feedback import (
    generate_feedback_questions,
    combine_query_with_feedback
)
# RAG 관련 imports 추가
from modules.rag_handler import create_rag_handler, create_rag_tool
from modules.document_rag import create_document_rag
from modules.image_rag import create_image_rag

# 로깅 설정
from logging_config import setup_logging, get_logger, add_db_handler_to_logger

# DB 로깅 import
try:
    from db_logger import log_conversation, log_search, log_agent_action, get_session_summary
    DB_LOGGING_AVAILABLE = True
except ImportError:
    DB_LOGGING_AVAILABLE = False

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="H-Deepsearch 💬",
    page_icon="🔍"
)

# CSS 로드 함수 (개선된 버전)
def load_custom_css():
    """커스텀 CSS 스타일 로드 - Docker 환경 최적화"""
    try:
        with open('./assets/style.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
            # CSS에 추가적인 오버플로우 방지 코드 삽입
            additional_css = """
            /* Docker 환경 최적화 */
            .stApp {
                overflow-x: hidden !important;
                max-width: 100vw !important;
            }
            
            /* 채팅 메시지 강제 너비 제한 */
            .stChatMessage {
                max-width: 100% !important;
                word-wrap: break-word !important;
                overflow-wrap: break-word !important;
                box-sizing: border-box !important;
            }
            
            /* 모든 텍스트 요소 오버플로우 방지 */
            * {
                word-wrap: break-word;
                overflow-wrap: break-word;
                max-width: 100%;
                box-sizing: border-box;
            }
            """
            combined_css = css_content + additional_css
            st.html(f'<style>{combined_css}</style>')
            logger.info("커스텀 CSS 로드 완료 (Docker 최적화 포함)")
    except FileNotFoundError:
        logger.warning("CSS 파일을 찾을 수 없습니다: assets/style.css")
        # 기본 오버플로우 방지 CSS 적용
        fallback_css = """
        <style>
        .stApp { overflow-x: hidden !important; max-width: 100vw !important; }
        [data-testid="stChatMessage"] { 
            word-wrap: break-word !important; 
            overflow-wrap: break-word !important; 
            max-width: 100% !important; 
        }
        </style>
        """
        st.html(fallback_css)
        logger.info("기본 CSS 폴백 적용")
    except Exception as e:
        logger.error(f"CSS 로드 중 오류: {e}")

# 모던 헤더 생성 함수 (심플 버전)
def create_modern_header():
    """헤더 생성 - 심플 버전"""
    st.html("""
    <div style="
        background: linear-gradient(135deg, #002C5F 0%, #0066CC 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 15px 40px rgba(0, 44, 95, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">
            🔍 제조AI기술개발-Team Agent
        </h1>
        <p style="color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: 300;">
            AI-Powered Research & Search Platform
        </p>
        <div style="margin-top: 1.5rem;">
            <span style="
                background: white; 
                color: #002C5F; 
                padding: 0.5rem 1.2rem; 
                border-radius: 25px; 
                margin: 0 0.5rem; 
                font-size: 0.9rem; 
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            ">
                💬 일반채팅
            </span>
            <span style="
                background: white; 
                color: #002C5F; 
                padding: 0.5rem 1.2rem; 
                border-radius: 25px; 
                margin: 0 0.5rem; 
                font-size: 0.9rem; 
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            ">
                🔬 딥리서치
            </span>
            <span style="
                background: white; 
                color: #002C5F; 
                padding: 0.5rem 1.2rem; 
                border-radius: 25px; 
                margin: 0 0.5rem; 
                font-size: 0.9rem; 
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            ">
                📚 RAG
            </span>
        </div>
    </div>
    """)

# 사이드바 섹션 헤더 함수 (심플 버전)
def create_sidebar_section(title, icon, color="#0066CC"):
    """사이드바 섹션 헤더 생성 - 심플 버전"""
    st.html(f"""
    <div style="
        background: rgba(0, 102, 204, 0.1);
        color: #002C5F;
        padding: 0.8rem;
        border-radius: 10px;
        margin: 1.5rem 0 0.8rem 0;
        text-align: left;
        font-weight: 700;
        font-size: 0.95rem;
        border-left: 4px solid {color};
        border: 1px solid rgba(0, 102, 204, 0.15);
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1.1rem;">{icon}</span>
            <span>{title}</span>
        </div>
    </div>
    """)

def create_status_card(title, status, color, description=""):
    """상태 카드 생성"""
    if status == "완료":
        status_color = "#0066CC"
    elif status == "진행중":
        status_color = "#FF6B35"
    else:
        status_color = "#F44336"
        
    st.html(f"""
    <div style="
        background: rgba(255, 255, 255, 0.98);
        border-left: 4px solid {status_color};
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0, 44, 95, 0.08);
        border: 1px solid rgba(0, 102, 204, 0.1);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600; color: #002C5F;">{title}</span>
            <span style="
                background: {status_color}; 
                color: white; 
                padding: 0.3rem 1rem; 
                border-radius: 20px; 
                font-size: 0.85rem;
                font-weight: 600;
                box-shadow: 0 2px 8px rgba(0, 44, 95, 0.2);
            ">{status}</span>
        </div>
        {f'<p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem; line-height: 1.4;">{description}</p>' if description else ''}
    </div>
    """)

# 프로젝트 전체 로깅 설정
setup_logging(level="INFO", log_to_file=True)
logger = get_logger(__name__)

# API KEY 정보로드
load_dotenv()
logger.info("환경 변수 로드 완료")

# 프로젝트 이름
langsmith_logging.langsmith("H-Deepsearch")
logger.info("LangSmith 초기화 완료")

# 헬퍼 함수들 추가
def get_session_lock_status():
    """세션 잠금 상태 확인"""
    return (
        st.session_state.get("normal_chat_ready", False) or
        st.session_state.get("deep_research_ready", False) or  
        st.session_state.get("rag_data_ready", False)
    )

def get_active_mode_info():
    """현재 활성화된 모드 정보 반환"""
    if st.session_state.get("rag_data_ready"):
        return "RAG", "📚 RAG 모드"
    elif st.session_state.get("deep_research_ready"):
        return "DEEP_RESEARCH", "🔬 딥리서치 모드"
    elif st.session_state.get("normal_chat_ready"):
        return "NORMAL_CHAT", "💬 일반 채팅 모드"
    return None, None


def get_current_session_id() -> str:
    """현재 세션 ID 반환"""
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = random_uuid()
    return st.session_state["thread_id"]


def log_user_message(content: str, metadata: dict = None):
    """사용자 메시지를 DB에 로깅"""
    if not DB_LOGGING_AVAILABLE:
        return
    
    session_id = get_current_session_id()
    mode_type, _ = get_active_mode_info()
    mode = mode_type if mode_type else "UNKNOWN"
    
    log_conversation(
        session_id=session_id,
        role="user",
        content=content,
        mode=mode,
        metadata=metadata
    )


def log_assistant_message(content: str, metadata: dict = None):
    """어시스턴트 메시지를 DB에 로깅"""
    if not DB_LOGGING_AVAILABLE:
        return
    
    session_id = get_current_session_id()
    mode_type, _ = get_active_mode_info()
    mode = mode_type if mode_type else "UNKNOWN"
    
    log_conversation(
        session_id=session_id,
        role="assistant",
        content=content,
        mode=mode,
        metadata=metadata
    )


def log_search_action(search_type: str, query: str, results: dict = None, metadata: dict = None):
    """검색 행동을 DB에 로깅"""
    if not DB_LOGGING_AVAILABLE:
        return
    
    session_id = get_current_session_id()
    
    log_search(
        session_id=session_id,
        search_type=search_type,
        query=query,
        results=results,
        metadata=metadata
    )


def log_tool_usage(tool_name: str, input_data: dict = None, output_data: dict = None, duration: float = None):
    """도구 사용을 DB에 로깅"""
    if not DB_LOGGING_AVAILABLE:
        return
    
    session_id = get_current_session_id()
    
    log_agent_action(
        session_id=session_id,
        action_type="tool_use",
        tool_name=tool_name,
        input_data=input_data,
        output_data=output_data,
        duration=duration
    )

# def show_active_mode_banner():
#     """활성 모드 배너 표시"""
#     mode_type, mode_name = get_active_mode_info()
    
#     if mode_type == "RAG":
#         st.success(f"🔒 **{mode_name} 활성화됨**")
#         st.info("📌 설정이 잠겨있습니다.\n'대화 초기화' 버튼으로 해제할 수 있습니다.")
        
#         # RAG 상태 요약 표시
#         rag_handler = st.session_state.get("rag_handler")
#         if rag_handler:
#             st.write("**📂 업로드된 파일:**")
#             doc_count = getattr(rag_handler, '_document_count', 0)
#             if doc_count > 0:
#                 st.write(f"• 📄 문서: {doc_count}개")
            
#             img_count = getattr(rag_handler, '_image_count', 0)
#             if img_count > 0:
#                 st.write(f"• 🖼️ 이미지: {img_count}개")
            
#             if rag_handler.has_documents:
#                 st.write("• ✅ 문서 벡터DB 준비됨")
#             if rag_handler.has_images:
#                 st.write("• ✅ 이미지 분석 완료")
                
#     elif mode_type == "NORMAL_CHAT":
#         st.success(f"🔒 **{mode_name} 활성화됨**")
#         st.info("📌 설정이 잠겨있습니다.\n'대화 초기화' 버튼으로 해제할 수 있습니다.")
        
#         # 일반 채팅 설정 요약 표시
#         st.write("**⚙️ 현재 설정:**")
#         st.write(f"• 🤖 모델: {st.session_state.get('selected_model', 'N/A')}")
        
#         search_result_count = st.session_state.get("search_result_count", 3)
#         st.write(f"• 🔍 검색 결과: {search_result_count}개")
        
#         search_topic = st.session_state.get("search_topic", "general")
#         st.write(f"• 📋 검색 주제: {search_topic}")
        
#         domains_count = len(st.session_state.get("include_domains", []))
#         if domains_count > 0:
#             st.write(f"• 🌐 등록된 도메인: {domains_count}개")
        
#         st.write("• ✅ 에이전트 준비 완료")
        
#     elif mode_type == "DEEP_RESEARCH":
#         st.success(f"🔒 **{mode_name} 활성화됨**")
#         st.info("📌 설정이 잠겨있습니다.\n'대화 초기화' 버튼으로 해제할 수 있습니다.")
        
#         # 딥리서치 설정 요약 표시
#         st.write("**⚙️ 현재 설정:**")
#         st.write(f"• 🤖 모델: {st.session_state.get('selected_model', 'N/A')}")
        
#         breadth = st.session_state.get("deep_research_breadth", 2)
#         depth = st.session_state.get("deep_research_depth", 2)
#         st.write(f"• 📊 연구 설정: 폭 {breadth}, 깊이 {depth}")
        
#         # 활성화된 검색 도구 표시
#         tools = []
#         if st.session_state.get("use_web_search", True):
#             web_count = st.session_state.get("web_search_count", 3)
#             tools.append(f"웹검색({web_count})")
#         if st.session_state.get("use_news_search", True):
#             news_count = st.session_state.get("news_search_count", 3)
#             tools.append(f"뉴스검색({news_count})")
        
#         st.write(f"• 🔧 검색 도구: {', '.join(tools) if tools else '없음'}")
#         st.write("• ✅ 딥리서치 에이전트 준비 완료")
    
#     if mode_type:
#         st.divider()

def show_active_mode_banner():
    """활성 모드 배너 표시"""
    mode_type, mode_name = get_active_mode_info()
    
    if mode_type == "RAG":
        st.html("""
        <div style="
            background: linear-gradient(135deg, #0066CC, #4A90E2);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 8px 25px rgba(0, 102, 204, 0.3);
            text-align: center;
        ">
            <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem;">
                📚 RAG 모드 활성화
            </div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                🔒 설정이 잠겨있습니다
            </div>
        </div>
        """)
        
        # RAG 상태 요약을 카드 형태로 표시
        rag_handler = st.session_state.get("rag_handler")
        if rag_handler:
            doc_count = getattr(rag_handler, '_document_count', 0)
            img_count = getattr(rag_handler, '_image_count', 0)
            
            st.html(f"""
            <div style="
                background: rgba(255, 255, 255, 0.98);
                padding: 1rem;
                border-radius: 10px;
                margin: 0.5rem 0;
                border-left: 4px solid #0066CC;
                box-shadow: 0 2px 10px rgba(0, 102, 204, 0.1);
            ">
                <div style="font-weight: 600; color: #002C5F; margin-bottom: 0.5rem;">📂 업로드된 파일</div>
                <div style="color: #666; line-height: 1.4;">
                    📄 문서: {doc_count}개 | 🖼️ 이미지: {img_count}개
                </div>
                <div style="margin-top: 0.5rem; color: #0066CC; font-size: 0.9rem;">
                    {'✅ 문서 벡터DB 준비됨' if rag_handler.has_documents else ''}
                    {'<br>✅ 이미지 분석 완료' if rag_handler.has_images else ''}
                </div>
            </div>
            """)
                
    elif mode_type == "NORMAL_CHAT":
        st.html("""
        <div style="
            background: linear-gradient(135deg, #002C5F, #0066CC);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 8px 25px rgba(0, 44, 95, 0.3);
            text-align: center;
        ">
            <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem;">
                💬 일반 채팅 모드 활성화
            </div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                🔒 설정이 잠겨있습니다
            </div>
        </div>
        """)
        
        # 설정 요약을 카드로 표시
        model = st.session_state.get('selected_model', 'N/A')
        search_count = st.session_state.get("search_result_count", 3)
        search_topic = st.session_state.get("search_topic", "general")
        domains_count = len(st.session_state.get("include_domains", []))
        
        st.html(f"""
        <div style="
            background: rgba(255, 255, 255, 0.98);
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            border-left: 4px solid #002C5F;
            box-shadow: 0 2px 10px rgba(0, 44, 95, 0.1);
        ">
            <div style="font-weight: 600; color: #002C5F; margin-bottom: 0.5rem;">⚙️ 현재 설정</div>
            <div style="color: #666; line-height: 1.5; font-size: 0.9rem;">
                🤖 모델: {model}<br>
                🔍 검색 결과: {search_count}개<br>
                📋 검색 주제: {search_topic}<br>
                🌐 등록 도메인: {domains_count}개<br>
                <span style="color: #0066CC;">✅ 에이전트 준비 완료</span>
            </div>
        </div>
        """)
        
    elif mode_type == "DEEP_RESEARCH":
        st.html("""
        <div style="
            background: linear-gradient(135deg, #FF6B35, #F7931E);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 8px 25px rgba(255, 107, 53, 0.3);
            text-align: center;
        ">
            <div style="font-size: 1.2rem; font-weight: 700; margin-bottom: 0.5rem;">
                🔬 딥리서치 모드 활성화
            </div>
            <div style="font-size: 0.9rem; opacity: 0.9;">
                🔒 설정이 잠겨있습니다
            </div>
        </div>
        """)
        
        # 딥리서치 설정 요약
        model = st.session_state.get('selected_model', 'N/A')
        breadth = st.session_state.get("deep_research_breadth", 2)
        depth = st.session_state.get("deep_research_depth", 2)
        
        tools = []
        if st.session_state.get("use_web_search", True):
            web_count = st.session_state.get("web_search_count", 3)
            tools.append(f"웹검색({web_count})")
        if st.session_state.get("use_news_search", True):
            news_count = st.session_state.get("news_search_count", 3)
            tools.append(f"뉴스검색({news_count})")
        
        st.html(f"""
        <div style="
            background: rgba(255, 255, 255, 0.98);
            padding: 1rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            border-left: 4px solid #FF6B35;
            box-shadow: 0 2px 10px rgba(255, 107, 53, 0.1);
        ">
            <div style="font-weight: 600; color: #002C5F; margin-bottom: 0.5rem;">⚙️ 연구 설정</div>
            <div style="color: #666; line-height: 1.5; font-size: 0.9rem;">
                🤖 모델: {model}<br>
                📊 연구 설정: 폭 {breadth}, 깊이 {depth}<br>
                🔧 검색 도구: {', '.join(tools) if tools else '없음'}<br>
                <span style="color: #FF6B35;">✅ 딥리서치 에이전트 준비 완료</span>
            </div>
        </div>
        """)
    
    if mode_type:
        st.html("<hr style='margin: 1rem 0; border: 1px solid rgba(0, 102, 204, 0.1);'>")

# 개선된 메시지 함수들 (현대자동차 테마)
def show_success_message(message, icon="✅"):
    """개선된 성공 메시지"""
    st.html(f"""
    <div style="
        background: linear-gradient(135deg, #0066CC, #4A90E2);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 102, 204, 0.2);
        animation: fadeIn 0.6s ease-out;
    ">
        <div style="font-weight: 600;">
            {icon} {message}
        </div>
    </div>
    """)

def show_info_message(message, icon="💡"):
    """개선된 정보 메시지"""
    st.html(f"""
    <div style="
        background: linear-gradient(135deg, #4A90E2, #74B9FF);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.2);
        animation: fadeIn 0.6s ease-out;
    ">
        <div style="font-weight: 600;">
            {icon} {message}
        </div>
    </div>
    """)

def show_warning_message(message, icon="⚠️"):
    """개선된 경고 메시지"""
    st.html(f"""
    <div style="
        background: linear-gradient(135deg, #FF6B35, #F7931E);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.2);
        animation: fadeIn 0.6s ease-out;
    ">
        <div style="font-weight: 600;">
            {icon} {message}
        </div>
    </div>
    """)

def reset_all_mode_states():
    """모든 모드 상태 초기화"""
    st.session_state["normal_chat_ready"] = False
    st.session_state["deep_research_ready"] = False
    st.session_state["rag_data_ready"] = False
    st.session_state["active_mode"] = None  # 활성 모드도 함께 초기화

# 기존 import들 다음에 추가
load_custom_css()  # CSS 먼저 로드

# st.title("H-Deepsearch 💬")
# st.markdown("LLM에 **웹검색 기능** 을 추가한 H-Deepsearch 입니다. _멀티턴_ 대화를 지원합니다.")

create_modern_header()

# 대화기록을 저장하기 위한 용도로 생성
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    logger.info("대화 기록 초기화")

# ReAct Agent 초기화
if "react_agent" not in st.session_state:
    st.session_state["react_agent"] = None
    logger.info("ReAct Agent 상태 초기화")

# include_domains 초기화
if "include_domains" not in st.session_state:
    st.session_state["include_domains"] = []
    logger.info("검색 도메인 목록 초기화")

# RAG 핸들러 초기화
if "rag_handler" not in st.session_state:
    st.session_state["rag_handler"] = None
    logger.info("RAG 핸들러 상태 초기화")

# RAG 상태 초기화
if "rag_enabled" not in st.session_state:
    st.session_state["rag_enabled"] = False
    logger.info("RAG 기능 상태 초기화")

# RAG 데이터 준비 상태 초기화
if "rag_data_ready" not in st.session_state:
    st.session_state["rag_data_ready"] = False
    logger.info("RAG 데이터 준비 상태 초기화")

# 일반 채팅 준비 상태 초기화
if "normal_chat_ready" not in st.session_state:
    st.session_state["normal_chat_ready"] = False
    logger.info("일반 채팅 준비 상태 초기화")

# 딥리서치 준비 상태 초기화
if "deep_research_ready" not in st.session_state:
    st.session_state["deep_research_ready"] = False
    logger.info("딥리서치 준비 상태 초기화")

# 활성 모드 상태 초기화 (설정 완료 시 고정되는 모드)
if "active_mode" not in st.session_state:
    st.session_state["active_mode"] = None
    logger.info("활성 모드 상태 초기화")

# 사이드바 생성
with st.sidebar:
    # 활성 모드 배너 표시 (가장 상단에 표시)
    show_active_mode_banner()
    
    # 통합 잠금 상태 결정
    is_locked = get_session_lock_status()
    
    # 모드 선택
    if is_locked:
        # 잠금 상태일 때는 활성 모드를 유지하고 비활성화
        current_active_mode = st.session_state.get("active_mode")
        if current_active_mode:
            mode_options = ["💬 일반 채팅", "🔬 딥리서치"]
            current_index = mode_options.index(current_active_mode) if current_active_mode in mode_options else 0
        else:
            current_index = 0
            
        mode = st.selectbox(
            "모드 선택", 
            ["💬 일반 채팅", "🔬 딥리서치"], 
            index=current_index,
            disabled=True,
            help=f"{get_active_mode_info()[1]} 활성화 중입니다. 변경하려면 '대화 초기화'를 눌러주세요."
        )
        # 잠금 상태에서는 활성 모드를 사용
        if current_active_mode:
            mode = current_active_mode
    else:
        # 비잠금 상태일 때는 정상적으로 선택 가능
        mode = st.selectbox(
            "모드 선택", 
            ["💬 일반 채팅", "🔬 딥리서치"], 
            index=0,
            disabled=False,
            help=None
        )
    logger.info(f"선택된 모드: {mode}")
    
    # 초기화 버튼 생성 (항상 활성화, 시각적 강조)
    if is_locked:
        mode_type, mode_name = get_active_mode_info()
        clear_btn = st.button("🔄 대화 초기화", type="primary", help=f"{mode_name} 설정을 해제하고 모든 데이터를 초기화합니다")
    else:
        clear_btn = st.button("대화 초기화")

    # 모델 선택 메뉴 - LLM Factory에서 가져오기
    try:
        from langchain_utils.llm_factory import LLMFactory
        factory = LLMFactory()
        available_models = factory.get_model_names()
        # display_name을 실제 model name으로 매핑하는 딕셔너리 생성
        display_to_name = {config.display_name: config.name for config in factory.get_available_models()}
    except Exception as e:
        logger.warning(f"LLM Factory 로드 실패, 기본 모델 사용: {e}")
        available_models = ["gpt-4o-mini", "gpt-4o"]
        display_to_name = {"gpt-4o-mini": "gpt-4o-mini", "gpt-4o": "gpt-4o"}
    
    # 잠금 상태일 때 현재 모델에 해당하는 인덱스 계산
    if is_locked:
        current_model = st.session_state.get("selected_model", "gpt-4o-mini")
        # 실제 모델명을 display name으로 변환
        name_to_display = {v: k for k, v in display_to_name.items()}
        current_display_name = name_to_display.get(current_model)
        
        # display name이 available_models에 있는지 확인하고 인덱스 찾기
        if current_display_name and current_display_name in available_models:
            current_index = available_models.index(current_display_name)
        else:
            current_index = 0
            
        selected_display_name = st.selectbox(
            "LLM 선택", 
            available_models, 
            index=current_index,
            disabled=True,
            help=f"{get_active_mode_info()[1]}에서는 변경할 수 없습니다"
        )
        selected_model = current_model  # 세션 상태 값 사용
    else:
        selected_display_name = st.selectbox(
            "LLM 선택", 
            available_models, 
            index=0,
            disabled=False
        )
        selected_model = display_to_name.get(selected_display_name, selected_display_name)
        st.session_state["selected_model"] = selected_model
    
    logger.info(f"선택된 모델: {selected_model}")
    
    # 모델 정보 표시 (선택사항)
    if st.checkbox("모델 정보 보기", key="show_model_info"):
        try:
            factory = LLMFactory()
            model_info = factory.get_model_info(selected_model)
            if model_info:
                #st.info(f"**{model_info['display_name']}** ({model_info['provider']})")
                show_info_message(f"**{model_info['display_name']}** ({model_info['provider']})")
                st.caption(model_info['description'])
                
                # Capabilities 표시
                capabilities = model_info['capabilities']
                caps_text = []
                if capabilities['multimodal']:
                    caps_text.append("🖼️ 멀티모달")
                if capabilities['tool_calling']:
                    caps_text.append("🔧 툴 콜링")
                if capabilities['reasoning']:
                    caps_text.append("🧠 추론")
                
                if caps_text:
                    #st.success(f"지원 기능: {' | '.join(caps_text)}")
                    show_success_message(f"지원 기능: {' | '.join(caps_text)}")
                
                # 환경변수 확인
                if model_info['env_vars_missing']:
                    #st.warning(f"누락된 환경변수: {', '.join(model_info['env_vars_missing'])}")
                    show_warning_message(f"누락된 환경변수: {', '.join(model_info['env_vars_missing'])}")
                elif model_info['env_vars_required']:
                    #st.success("✅ 모든 필수 환경변수가 설정되었습니다")
                    show_success_message(f"모든 필수 환경변수가 설정되었습니다")
        except Exception as e:
            st.error(f"모델 정보를 가져올 수 없습니다: {e}")

    if mode == "💬 일반 채팅":
        create_sidebar_section("🔧 일반 채팅 설정", "")
        # 검색 결과 개수 설정
        # 현재 세션 상태 값 또는 기본값 사용
        current_search_count = st.session_state.get("search_result_count", 3)

        search_result_count = st.slider(
            "검색 결과", 
            min_value=1, 
            max_value=10, 
            value=current_search_count,
            disabled=is_locked,
            help=f"{get_active_mode_info()[1]}에서는 변경할 수 없습니다" if is_locked else None
        )
        # 잠금되지 않았을 때만 세션 상태 업데이트
        if not is_locked:
            st.session_state["search_result_count"] = search_result_count

        # include_domains 설정
        st.subheader("검색 도메인 설정")
        # 현재 세션 상태 값 확인
        current_topic = st.session_state.get("search_topic", "general")
        topic_options = ["news", "general"]

        # 현재 값에 해당하는 인덱스 찾기
        if current_topic in topic_options:
            current_topic_index = topic_options.index(current_topic)
        else:
            current_topic_index = 1  # "general"의 인덱스

        search_topic = st.selectbox(
            "검색 주제", 
            topic_options, 
            index=current_topic_index, 
            help="news는 최신뉴스, general은 일반 웹검색" if not is_locked else f"{get_active_mode_info()[1]}에서는 변경할 수 없습니다",
            disabled=is_locked
        )
        # 잠금되지 않았을 때만 세션 상태 업데이트
        if not is_locked:
            st.session_state["search_topic"] = search_topic
        
        # 검색 주제가 'news'가 아닐 때만 도메인 설정 표시
        if search_topic != 'news':
            new_domain = st.text_input(
                "추가할 도메인 입력",
                disabled=is_locked,
                help="(예) naver.com" if not is_locked else f"{get_active_mode_info()[1]}에서는 추가할 수 없습니다"
            )
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(
                    "도메인 추가", 
                    key="add_domain", 
                    help="(예) naver.com" if not is_locked else f"{get_active_mode_info()[1]}에서는 추가할 수 없습니다",
                    disabled=is_locked
                ):
                    if new_domain and new_domain not in st.session_state["include_domains"]:
                        st.session_state["include_domains"].append(new_domain)
                        logger.info(f"도메인 추가: {new_domain}")

            # 현재 등록된 도메인 목록 표시
            st.write("등록된 도메인 목록:")
            for idx, domain in enumerate(st.session_state["include_domains"]):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(domain)
                with col2:
                    if st.button(
                        "삭제", 
                        key=f"del_{idx}",
                        disabled=is_locked,
                        help=f"{get_active_mode_info()[1]}에서는 삭제할 수 없습니다" if is_locked else None
                    ):
                        removed_domain = st.session_state["include_domains"].pop(idx)
                        logger.info(f"도메인 삭제: {removed_domain}")
                        st.rerun()
        else:
            # 뉴스 검색일 때는 도메인 설정이 필요 없다는 안내 메시지
            st.info("📰 뉴스 검색 모드에서는 별도의 도메인 설정이 필요하지 않습니다.")

        st.divider()  # 구분선 추가
        
        # RAG 기능 설정 (일반 채팅 모드에서만 표시)
        #st.subheader("📚 RAG 기능 (문서/이미지)")
        create_sidebar_section("📚 RAG 기능", "", "#4CAF50")
        
        # RAG 활성화 상태를 callback으로 관리
        def toggle_rag():
            st.session_state["rag_enabled"] = st.session_state["use_rag_checkbox"]
        
        # 현재 모드가 일반 채팅이 아닌 경우 RAG 섹션 숨김
        current_mode_type, _ = get_active_mode_info()
        
        # 잠금 상태이고 RAG 모드가 아닌 경우의 안내 메시지
        if is_locked and current_mode_type != "RAG":
            #st.info("🔒 현재 모드가 활성화되어 있습니다.\n설정을 변경하려면 '대화 초기화'를 눌러주세요.")
            show_info_message("현재 모드가 활성화되어 있습니다.\n설정을 변경하려면 '대화 초기화'를 눌러주세요.")
        # RAG가 이미 준비된 상태라면 설정 변경 불가
        elif is_locked and current_mode_type == "RAG":
            #st.info("✅ RAG 기능이 활성화되어 있습니다.\n변경하려면 '대화 초기화'를 눌러주세요.")
            show_info_message("RAG 기능이 활성화되어 있습니다.\n변경하려면 '대화 초기화'를 눌러주세요.")
            # 현재 설정 표시만
            st.checkbox("RAG 기능 사용", value=True, disabled=True)
            
            # 현재 RAG 설정 정보 표시
            if st.session_state.get("disable_web_search_checkbox"):
                st.checkbox("웹검색 비활성화 (RAG만 사용)", value=True, disabled=True)
        else:
            # RAG 활성화 체크박스 (callback으로 즉시 상태 동기화)
            use_rag = st.checkbox(
                "RAG 기능 사용", 
                value=st.session_state.get("rag_enabled", False),
                key="use_rag_checkbox",
                on_change=toggle_rag
            )
        
        # 안정적인 컨테이너 생성 (항상 렌더링, 내용만 조건부 표시)
        rag_container = st.container()
        
        with rag_container:
            # RAG가 잠겨있지 않고 활성화된 경우에만 설정 UI 표시
            if not is_locked and st.session_state.get("rag_enabled", False):
                # 웹검색 비활성화 옵션
                disable_web_search = st.checkbox(
                    "웹검색 비활성화 (RAG만 사용)", 
                    value=True,
                    key="disable_web_search_checkbox",
                    help="체크하면 업로드된 문서/이미지만 사용하고 웹검색을 하지 않습니다"
                )
                
                # 문서 업로드 (안정적인 상태 관리)
                st.write("**📄 문서 업로드**")
                document_files = st.file_uploader(
                    "문서 파일을 업로드하세요",
                    type=['pdf', 'docx', 'txt', 'md', 'pptx', 'xlsx'],
                    accept_multiple_files=True,
                    key="doc_files_uploader",
                    help="PDF, DOCX, TXT, MD, PPTX, XLSX 파일을 지원합니다"
                )
                
                
                # 이미지 업로드 (단순화)
                st.write("**🖼️ 이미지 업로드**")
                image_files = st.file_uploader(
                    "이미지 파일을 업로드하세요",
                    type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
                    accept_multiple_files=True,
                    key="img_files_uploader",
                    help="PNG, JPG, JPEG, GIF, BMP, WEBP 파일을 지원합니다"
                )
                
                # 이미지 분석 질문
                image_query = ""
                if image_files:
                    image_query = st.text_input(
                        "이미지 분석 질문 (선택사항)",
                        key="image_query_input",
                        placeholder="예: 이 이미지에서 중요한 정보를 찾아주세요",
                        help="특정 질문이 있다면 입력하세요 (빈 칸이면 일반 분석)"
                    )
                
                # 간단한 업로드 상태 표시
                if document_files or image_files:
                    #st.success(f"✅ 파일 업로드 완료: 문서 {len(document_files) if document_files else 0}개, 이미지 {len(image_files) if image_files else 0}개")
                    show_success_message(f"파일 업로드 완료: 문서 {len(document_files) if document_files else 0}개, 이미지 {len(image_files) if image_files else 0}개")
                    #st.info("💡 '설정 완료' 버튼을 눌러 벡터DB를 생성하고 채팅을 시작하세요!")
                    show_info_message("'설정 완료' 버튼을 눌러 벡터DB를 생성하고 채팅을 시작하세요!")
                
                # RAG 데이터 준비 완료 상태만 간단히 표시
                if st.session_state.get("rag_data_ready"):
                    #st.success("✅ 벡터DB 생성 완료 - 이제 채팅에서 업로드한 파일들을 활용할 수 있습니다!")
                    show_success_message("벡터DB 생성 완료 - 이제 채팅에서 업로드한 파일들을 활용할 수 있습니다!")
            elif not is_locked:
                # RAG를 사용하지 않는 경우 기본값 설정
                disable_web_search = False
                document_files = None
                image_files = None
                image_query = ""
            else:
                # RAG가 잠긴 상태에서의 기본값
                disable_web_search = st.session_state.get("disable_web_search_checkbox", False)
                document_files = None
                image_files = None 
                image_query = ""

        # 설정 버튼 (세션이 잠겨있으면 비활성화)
        # apply_btn = st.button(
        #     "설정 완료", 
        #     type="primary",
        #     disabled=is_locked,
        #     help=f"{get_active_mode_info()[1]}에서는 설정을 변경할 수 없습니다" if is_locked else None
        # )
        st.html("<div style='margin: 1rem 0;'></div>")
        apply_btn = st.button(
            "✅ 설정 완료", 
            type="primary",
            disabled=is_locked,
            help=f"{get_active_mode_info()[1]}에서는 설정을 변경할 수 없습니다" if is_locked else "설정을 완료하고 채팅을 시작합니다"
        )
    
    else:  # 딥리서치 모드
        #st.subheader("딥리서치 설정")
        create_sidebar_section("🔬 딥리서치 설정", "")
        
        # 연구 파라미터 설정
        # 현재 세션 상태 값 또는 기본값 사용
        current_breadth = st.session_state.get("deep_research_breadth", 2)
        current_depth = st.session_state.get("deep_research_depth", 2)

        breadth = st.slider(
            "연구 폭 (Breadth)", 
            min_value=1, 
            max_value=5, 
            value=current_breadth, 
            help="각 단계에서 생성할 검색 쿼리 수" if not is_locked else f"{get_active_mode_info()[1]}에서는 변경할 수 없습니다",
            disabled=is_locked
        )
        depth = st.slider(
            "연구 깊이 (Depth)", 
            min_value=1, 
            max_value=3, 
            value=current_depth,
            help="재귀적 연구 깊이" if not is_locked else f"{get_active_mode_info()[1]}에서는 변경할 수 없습니다",
            disabled=is_locked
        )
        # 잠금되지 않았을 때만 세션 상태 업데이트
        if not is_locked:
            st.session_state["deep_research_breadth"] = breadth
            st.session_state["deep_research_depth"] = depth
        
        # 검색 도구 선택
        st.subheader("검색 도구 선택")
        # 현재 세션 상태 값 또는 기본값 사용
        current_use_web = st.session_state.get("use_web_search", True)
        current_use_news = st.session_state.get("use_news_search", True)

        use_web_search = st.checkbox(
            "웹 검색", 
            value=current_use_web,
            disabled=is_locked,
            help=f"{get_active_mode_info()[1]}에서는 변경할 수 없습니다" if is_locked else None
        )
        use_news_search = st.checkbox(
            "뉴스 검색", 
            value=current_use_news,
            disabled=is_locked,
            help=f"{get_active_mode_info()[1]}에서는 변경할 수 없습니다" if is_locked else None
        )
        # 잠금되지 않았을 때만 세션 상태 업데이트
        if not is_locked:
            st.session_state["use_web_search"] = use_web_search
            st.session_state["use_news_search"] = use_news_search
        
        if use_web_search:
            current_web_count = st.session_state.get("web_search_count", 3)
            web_search_count = st.slider(
                "웹 검색 결과 수", 
                min_value=1, 
                max_value=10, 
                value=current_web_count,
                disabled=is_locked,
                help=f"{get_active_mode_info()[1]}에서는 변경할 수 없습니다" if is_locked else None
            )
            # 잠금되지 않았을 때만 세션 상태 업데이트
            if not is_locked:
                st.session_state["web_search_count"] = web_search_count
        
        if use_news_search:
            current_news_count = st.session_state.get("news_search_count", 3)
            news_search_count = st.slider(
                "뉴스 검색 결과 수", 
                min_value=1, 
                max_value=10, 
                value=current_news_count,
                disabled=is_locked,
                help=f"{get_active_mode_info()[1]}에서는 변경할 수 없습니다" if is_locked else None
            )
            # 잠금되지 않았을 때만 세션 상태 업데이트
            if not is_locked:
                st.session_state["news_search_count"] = news_search_count
        
        # 딥리서치 에이전트 설정 버튼
        # setup_deep_research_btn = st.button(
        #     "딥리서치 설정 완료", 
        #     type="primary",
        #     disabled=is_locked,
        #     help=f"{get_active_mode_info()[1]}에서는 설정을 변경할 수 없습니다" if is_locked else None
        # )
        st.html("<div style='margin: 1rem 0;'></div>")
        setup_deep_research_btn = st.button(
            "🚀 딥리서치 설정 완료", 
            type="primary",
            disabled=is_locked,
            help=f"{get_active_mode_info()[1]}에서는 설정을 변경할 수 없습니다" if is_locked else "딥리서치 설정을 완료합니다"
        )
    

    st.divider()  # 구분선 추가
    st.markdown("### 👨‍💻 Contact")
    st.markdown("""
    **개발**: Clark  
    **버그 제보**: [y.lim@h.com](mailto:y.lim@h.com)
    """)


@dataclass
class ChatMessageWithType:
    chat_message: ChatMessage
    msg_type: str
    tool_name: str


# 이전 대화를 출력
def print_messages():
    for message in st.session_state["messages"]:
        if message.msg_type == "text":
            # 커스텀 아바타 설정
            avatar = "./assets/user.png" if message.chat_message.role == "user" else "./assets/ai.png"
            st.chat_message(message.chat_message.role, avatar=avatar).write(
                message.chat_message.content
            )
        elif message.msg_type == "tool_result":
            with st.expander(f"✅ {message.tool_name}"):
                st.markdown(message.chat_message.content)


# 새로운 메시지를 추가
def add_message(role, message, msg_type="text", tool_name=""):
    if msg_type == "text":
        st.session_state["messages"].append(
            ChatMessageWithType(
                chat_message=ChatMessage(role=role, content=message),
                msg_type="text",
                tool_name=tool_name,
            )
        )
        logger.debug(f"텍스트 메시지 추가: {role} - {message[:50]}...")
        
        # DB 로깅 추가
        metadata = {"msg_type": msg_type, "tool_name": tool_name}
        if role == "user":
            log_user_message(message, metadata)
        elif role == "assistant":
            log_assistant_message(message, metadata)
            
    elif msg_type == "tool_result":
        formatted_message = format_search_result(message)
        st.session_state["messages"].append(
            ChatMessageWithType(
                chat_message=ChatMessage(
                    role="assistant", content=formatted_message
                ),
                msg_type="tool_result",
                tool_name=tool_name,
            )
        )
        logger.debug(f"도구 결과 메시지 추가: {tool_name}")
        
        # DB 로깅 추가 (도구 결과)
        metadata = {"msg_type": msg_type, "tool_name": tool_name}
        log_assistant_message(formatted_message, metadata)
        
        # 도구 사용 로깅
        log_tool_usage(tool_name, input_data={"query": "검색 쿼리"}, output_data={"result": message})


# 딥리서치 상태 초기화 함수
def _reset_deep_research_state():
    """딥리서치 상태 초기화"""
    st.session_state["deep_research_step"] = "initial"
    st.session_state["initial_query"] = ""
    st.session_state["feedback_questions"] = []
    st.session_state["feedback_answers"] = []
    logger.info("딥리서치 상태 초기화 완료")


# 딥리서치 직접 실행 함수
def _execute_deep_research_directly(query: str, agent):
    """피드백 단계 없이 바로 딥리서치 실행"""
    try:
        st.session_state["deep_research_step"] = "research"
        breadth = st.session_state.get("deep_research_breadth", 2)
        depth = st.session_state.get("deep_research_depth", 2)
        
        st.write(f"### 🔬 딥리서치: {query}")
        
        # 딥리서치 실행 중 spinner 표시
        with st.spinner("🚀 딥리서치를 실행하고 있습니다... 잠시만 기다려 주세요."):
            final_report, full_result = deep_research_stream_handler(
                streamlit_container=st.container(),
                agent=agent,
                query=query,
                breadth=breadth,
                depth=depth
            )
        
        # 결과 표시
        if final_report:
            #st.success("✅ 딥리서치가 완료되었습니다!")
            show_success_message("딥리서치가 완료되었습니다!")
            st.write("#### 📋 최종 보고서")
            st.markdown(final_report)
            
            # 보고서 다운로드 버튼
            st.download_button(
                label="📄 보고서 다운로드 (Markdown)",
                data=final_report,
                file_name=f"deep_research_report_{query[:20]}.md",
                mime="text/markdown"
            )
        else:
            #st.warning("⚠️ 딥리서치가 완료되었지만 보고서가 생성되지 않았습니다.")
            show_warning_message("딥리서치가 완료되었지만 보고서가 생성되지 않았습니다.")
        
        # 연구 완료 후 상태 초기화
        _reset_deep_research_state()
        
    except Exception as e:
        logger.error(f"직접 딥리서치 실행 중 오류: {e}")
        st.error(f"딥리서치 실행 중 오류가 발생했습니다: {e}")
        _reset_deep_research_state()


# 딥리서치 에이전트 초기화
if "deep_research_agent" not in st.session_state:
    st.session_state["deep_research_agent"] = None
    logger.info("딥리서치 에이전트 상태 초기화")

# 딥리서치 워크플로우 상태 초기화
if "deep_research_step" not in st.session_state:
    st.session_state["deep_research_step"] = "initial"  # initial, feedback, research
    logger.info("딥리서치 워크플로우 상태 초기화")

if "initial_query" not in st.session_state:
    st.session_state["initial_query"] = ""
    logger.info("초기 질문 상태 초기화")

if "feedback_questions" not in st.session_state:
    st.session_state["feedback_questions"] = []
    logger.info("피드백 질문 상태 초기화")

if "feedback_answers" not in st.session_state:
    st.session_state["feedback_answers"] = []
    logger.info("피드백 답변 상태 초기화")

# 초기화 버튼이 눌리면...
if clear_btn:
    st.session_state["messages"] = []
    st.session_state["thread_id"] = random_uuid()
    logger.info("대화 기록 초기화 및 새 스레드 ID 생성")
    
    # RAG 핸들러 정리
    try:
        if st.session_state.get("rag_handler"):
            st.session_state["rag_handler"].clear_all()
            logger.info("RAG 데이터 초기화 완료")
    except Exception as e:
        logger.warning(f"RAG 데이터 초기화 중 오류 (무시됨): {e}")
    
    # 모든 세션 상태 완전 초기화
    keys_to_preserve = ["messages", "thread_id"]  # 보존할 키들
    keys_to_clear = []
    
    # 현재 세션 상태에서 보존하지 않을 키들을 찾음
    for key in list(st.session_state.keys()):
        if key not in keys_to_preserve:
            keys_to_clear.append(key)
    
    # 키들 초기화
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            logger.debug(f"세션 키 초기화: {key}")
    
    # 기본 상태들 재설정
    st.session_state["react_agent"] = None
    st.session_state["include_domains"] = []
    st.session_state["rag_handler"] = None
    st.session_state["rag_enabled"] = False
    
    # 모든 모드의 준비 상태 초기화
    reset_all_mode_states()
    
    if mode == "🔬 딥리서치":
        st.session_state["deep_research_agent"] = None
        st.session_state["deep_research_step"] = "initial"
        st.session_state["initial_query"] = ""
        st.session_state["feedback_questions"] = []
        st.session_state["feedback_answers"] = []
        logger.info("딥리서치 관련 상태 모두 초기화")
    
    logger.info("모든 세션 상태 초기화 완료")
    #st.success("🔄 모든 데이터가 초기화되었습니다!")
    show_success_message("모든 데이터가 초기화되었습니다!")
    
    # 강제로 페이지 새로고침을 위해 rerun 호출
    st.rerun()

# 이전 대화 기록 출력 (일반 채팅 모드에서만)
if mode == "💬 일반 채팅":
    print_messages()

# 딥리서치 모드에서 현재 진행 상황 표시
if mode == "🔬 딥리서치":
    current_step = st.session_state.get("deep_research_step", "initial")
    if current_step == "feedback":
        #st.info("🔄 **딥리서치 진행 중**: 피드백 질문에 답변해 주세요.")
        show_info_message("**딥리서치 진행 중**: 피드백 질문에 답변해 주세요.")
        logger.debug("딥리서치 피드백 단계 진행 중")
    elif current_step == "research":
        #st.info("🔄 **딥리서치 진행 중**: 연구를 수행하고 있습니다.")
        show_info_message("**딥리서치 진행 중**: 연구를 수행하고 있습니다.")
        logger.debug("딥리서치 연구 단계 진행 중")
    else:
        #st.info("🚀 **딥리서치 준비**: 연구하고 싶은 주제를 입력해 주세요.")
        show_info_message("**딥리서치 준비**: 연구하고 싶은 주제를 입력해 주세요.")
        logger.debug("딥리서치 초기 상태")

# 사용자의 입력
user_input = st.chat_input("궁금한 내용을 물어보세요!")

# 경고 메시지를 띄우기 위한 빈 영역
warning_msg = st.empty()

# 설정 버튼이 눌리면...
if mode == "💬 일반 채팅" and apply_btn:
    logger.info("일반 채팅 모드 설정 시작")
    try:
        # RAG 처리 실패 추적 변수 추가
        rag_processing_failed = False
        
        # 간단한 상태 확인 (복잡한 컨테이너 관리 제거)
        logger.info(f"RAG 사용 여부: {use_rag}")
        if use_rag:
            logger.info("RAG 기능이 활성화됨")
        
        tools = []
        
        # RAG 기능 처리
        if use_rag:
            # RAG 핸들러 초기화
            if not st.session_state.get("rag_handler"):
                st.session_state["rag_handler"] = create_rag_handler(model_name=selected_model)
                logger.info("RAG 핸들러 생성 완료")
            
            rag_handler = st.session_state["rag_handler"]
            
            # RAG 데이터가 이미 준비되어 있다면 파일 처리 건너뛰기
            if st.session_state.get("rag_data_ready", False):
                logger.info("RAG 데이터가 이미 준비되어 있음, 파일 처리 건너뛰기")
            else:
                # 업로드된 파일들 벡터DB에 저장 (단순화된 처리)
                if document_files or image_files:
                    with st.spinner("📚 벡터DB 생성 중입니다..."):
                        try:
                            processed_files = 0
                            
                            # 문서 파일 처리
                            if document_files:
                                # 첫 번째 RAG 설정인 경우에만 기존 데이터 초기화
                                reset_existing = not st.session_state.get("rag_data_ready", False)
                                chunk_count = rag_handler.process_documents(document_files, reset_existing=reset_existing)
                                
                                # 실제 처리 성공 여부에 따라 처리
                                if chunk_count > 0:
                                    processed_files += len(document_files)  # 성공한 경우만 파일 수 추가
                                    logger.info(f"문서 처리 완료: {len(document_files)}개 파일, {chunk_count}개 청크")
                                else:
                                    logger.warning(f"문서 처리 실패: {len(document_files)}개 파일, {chunk_count}개 청크")
                                    rag_processing_failed = True  # 실패 플래그 설정
                            
                            # 이미지 파일 처리 (분석 결과 표시 없이 벡터DB에만 저장)
                            if image_files:
                                query_for_images = image_query if image_query.strip() else None
                                image_results = rag_handler.process_images(image_files, query_for_images)
                                
                                # 실제 처리 성공 여부 확인 (에러가 포함된 결과 제외)
                                successful_images = 0
                                for result in image_results:
                                    if "오류 발생" not in result.get("analysis", ""):
                                        successful_images += 1
                                
                                if successful_images > 0:
                                    processed_files += successful_images  # 성공한 이미지만 카운트
                                    logger.info(f"이미지 처리 완료: {successful_images}/{len(image_files)}개 파일")
                                else:
                                    logger.warning(f"이미지 처리 실패: 0/{len(image_files)}개 파일")
                                    rag_processing_failed = True  # 실패 플래그 설정
                            
                            # 처리 완료 상태만 저장 (실제 성공한 파일이 있는 경우에만)
                            if processed_files > 0:
                                # RAG 핸들러에서도 실제 데이터가 있는지 확인
                                if rag_handler.has_documents or rag_handler.has_images:
                                    st.session_state["rag_data_ready"] = True
                                    st.session_state["active_mode"] = "📚 RAG 모드"  # 활성 모드 저장
                                    logger.info(f"RAG 데이터 처리 완료: 총 {processed_files}개 파일")
                                else:
                                    logger.warning("파일 처리는 완료되었지만 실제 사용 가능한 데이터가 없음")
                                    rag_processing_failed = True
                            else:
                                logger.warning("처리된 파일이 없음")
                                rag_processing_failed = True
                            
                        except Exception as e:
                            st.error(f"파일 처리 중 오류: {str(e)}")
                            logger.error(f"파일 처리 중 오류: {e}", exc_info=True)
                            rag_processing_failed = True  # 실패 플래그 설정
                else:
                    # RAG 사용하지만 파일이 없는 경우
                    if use_rag:
                        logger.warning("RAG 기능을 사용하려 하지만 업로드된 파일이 없음")
                        rag_processing_failed = True
            
            # RAG 도구 추가 (처리 성공 시에만)
            if not rag_processing_failed and st.session_state.get("rag_data_ready", False):
                rag_tool = create_rag_tool(rag_handler)
                tools.append(rag_tool)
                logger.info("RAG 검색 도구 추가 완료")
            else:
                logger.warning("RAG 파일 처리 실패 또는 데이터 미준비로 인해 RAG 도구를 추가하지 않음")
        
        # 웹 검색 도구 추가 (RAG 사용 시 선택적)
        if not use_rag or (use_rag and not disable_web_search):
            web_tool = WebSearchTool().create()
            web_tool.max_results = search_result_count
            web_tool.include_domains = st.session_state["include_domains"]
            web_tool.topic = search_topic
            tools.append(web_tool)
            logger.info(f"웹 검색 도구 설정 완료 - 결과 수: {search_result_count}, 주제: {search_topic}")
            
            # 검색 주제가 'news'일 때 NewsSearchTool 추가
            if search_topic == 'news':
                logger.info("뉴스 검색 도구 생성 시작 (일반 채팅 모드)")
                news_tool = NewsSearchTool(max_results=search_result_count).create()
                tools.append(news_tool)
                logger.info(f"뉴스 검색 도구 추가 완료 - 결과 수: {search_result_count}")
        
        # 도구가 없는 경우 기본 웹 검색 도구 추가
        if not tools:
            web_tool = WebSearchTool().create()
            web_tool.max_results = search_result_count
            web_tool.include_domains = st.session_state["include_domains"]
            web_tool.topic = search_topic
            tools.append(web_tool)
            logger.info("기본 웹 검색 도구 추가")
            
            # 기본 도구 추가 시에도 뉴스 주제면 NewsSearchTool 추가
            if search_topic == 'news':
                logger.info("뉴스 검색 도구 생성 시작 (기본 도구)")
                news_tool = NewsSearchTool(max_results=search_result_count).create()
                tools.append(news_tool)
                logger.info(f"뉴스 검색 도구 추가 완료 - 결과 수: {search_result_count}")
        
        # RAG 상태 저장
        st.session_state["rag_enabled"] = use_rag
        
        # 에이전트가 없거나 새로 생성해야 하는 경우에만 생성
        need_new_agent = (
            st.session_state.get("react_agent") is None or
            st.session_state.get("selected_model") != selected_model
        )
        
        # RAG 실패 시 에이전트 생성하지 않음
        if use_rag and rag_processing_failed:
            logger.warning("RAG 파일 처리 실패로 인해 에이전트를 생성하지 않음")
            # 실패한 경우 기존 에이전트도 제거
            st.session_state["react_agent"] = None
        elif need_new_agent:
            st.session_state["react_agent"] = create_agent_executor(
                model_name=selected_model,
                tools=tools,
            )
            logger.info(f"새로운 ReAct 에이전트 생성 완료 - 도구 수: {len(tools)}")
        else:
            logger.info("기존 ReAct 에이전트 재사용")
        
        # thread_id가 없는 경우에만 새로 생성
        if "thread_id" not in st.session_state or not st.session_state["thread_id"]:
            st.session_state["thread_id"] = random_uuid()
            logger.info("새 스레드 ID 생성")
        else:
            logger.info(f"기존 스레드 ID 유지: {st.session_state['thread_id']}")
        
        # 일반 채팅 준비 상태 설정 (RAG 실패 시 제외)
        if not (use_rag and rag_processing_failed):
            st.session_state["normal_chat_ready"] = True
            st.session_state["active_mode"] = "💬 일반 채팅"  # 활성 모드 저장
            logger.info("일반 채팅 모드 준비 완료 상태로 설정")
        else:
            logger.warning("RAG 파일 처리 실패로 인해 채팅 모드를 활성화하지 않음")
            # 실패 시 준비 상태 해제
            st.session_state["normal_chat_ready"] = False
            st.session_state["active_mode"] = None
        
        # 조건부 메시지 표시
        if use_rag and rag_processing_failed:
            # RAG 실패 시 경고 메시지
            show_warning_message("파일 처리에 실패했습니다. 파일을 다시 업로드하고 설정을 완료해주세요.")
            show_info_message("💡 지원되는 파일 형식을 확인하고 파일 크기나 내용을 점검해보세요.")
            show_info_message("📋 지원 형식: PDF, DOCX, TXT, MD, PPTX, XLSX (문서) / PNG, JPG, JPEG, GIF, BMP, WEBP (이미지)")
        else:
            # 성공 시 기존 메시지
            if use_rag and st.session_state.get("rag_data_ready"):
                show_success_message("설정 완료! 벡터DB가 생성되었습니다. 이제 채팅에서 업로드한 파일들을 활용할 수 있습니다.")
            else:
                show_success_message("일반 채팅 설정이 완료되었습니다!")
            
            show_info_message("이제 아래에서 질문을 입력하여 채팅을 시작하세요!\n설정을 변경하려면 '대화 초기화' 버튼을 눌러주세요.")
        
    except Exception as e:
        logger.error(f"일반 채팅 모드 설정 실패: {e}", exc_info=True)
        st.error(f"설정 중 오류가 발생했습니다: {e}")

# 딥리서치 설정 버튼이 눌리면...
elif mode == "🔬 딥리서치" and setup_deep_research_btn:
    logger.info("딥리서치 모드 설정 시작")
    try:
        tools = []
        
        # 웹 검색 도구 추가
        if use_web_search:
            logger.info("웹 검색 도구 생성 시작")
            web_tool = WebSearchTool().create()
            web_tool.max_results = web_search_count
            tools.append(web_tool)
            logger.info(f"웹 검색 도구 추가 완료 - 결과 수: {web_search_count}")
        
        # 뉴스 검색 도구 추가
        if use_news_search:
            logger.info("뉴스 검색 도구 생성 시작")
            news_tool = NewsSearchTool(max_results=news_search_count).create()
            tools.append(news_tool)
            logger.info(f"뉴스 검색 도구 추가 완료 - 결과 수: {news_search_count}")
        
        if not tools:
            logger.warning("선택된 검색 도구가 없습니다")
            #st.warning("최소 하나의 검색 도구를 선택해주세요.")
            show_warning_message("최소 하나의 검색 도구를 선택해주세요.")
            st.stop()
        
        # 딥리서치 에이전트 생성 (모든 도구를 전달)
        logger.info(f"딥리서치 에이전트 생성 시작 - 도구 수: {len(tools)}")
        st.session_state["deep_research_agent"] = DeepResearchAgent(
            model_name=selected_model,
            tools=tools
        )
        
        # 딥리서치 파라미터 저장
        st.session_state["deep_research_breadth"] = breadth
        st.session_state["deep_research_depth"] = depth
        
        # 딥리서치 준비 상태 설정
        st.session_state["deep_research_ready"] = True
        st.session_state["active_mode"] = "🔬 딥리서치"  # 활성 모드 저장
        logger.info("딥리서치 모드 준비 완료 상태로 설정")
        
        logger.info(f"딥리서치 설정 완료 - breadth: {breadth}, depth: {depth}")
        logger.info(f"딥리서치 도구 설정 - 웹검색: {use_web_search}, 뉴스검색: {use_news_search}")
        logger.info(f"딥리서치 에이전트 생성 완료 - 모델: {selected_model}")
        #st.success("✅ 딥리서치 설정이 완료되었습니다!")
        show_success_message("딥리서치 설정이 완료되었습니다!")
        #st.info("🔬 이제 아래에서 연구하고 싶은 주제를 입력하여 딥리서치를 시작하세요!\n🔒 설정을 변경하려면 '대화 초기화' 버튼을 눌러주세요.")
        show_info_message("이제 아래에서 연구하고 싶은 주제를 입력하여 딥리서치를 시작하세요!\n설정을 변경하려면 '대화 초기화' 버튼을 눌러주세요.")
        
    except Exception as e:
        logger.error(f"딥리서치 모드 설정 실패: {e}", exc_info=True)
        st.error(f"딥리서치 설정 중 오류가 발생했습니다: {e}")

# 만약에 사용자 입력이 들어오면...
if user_input:
    logger.info(f"사용자 입력 수신 - 모드: {mode}, 입력: {user_input[:100]}...")
    logger.info(f"현재 세션 상태 - 딥리서치 단계: {st.session_state.get('deep_research_step', 'N/A')}")
    
    if mode == "💬 일반 채팅":
        agent = st.session_state["react_agent"]
        
        if agent is not None:
            logger.info(f"일반 채팅 모드 실행 시작 - 모델: {st.session_state.get('selected_model', 'Unknown')}")
            logger.info(f"스레드 ID: {st.session_state.get('thread_id', 'N/A')}")
            config = {"configurable": {"thread_id": st.session_state["thread_id"]}}
            
            # 채팅 메시지 컨테이너로 감싸기 (오버플로우 방지)
            with st.container():
                # 사용자의 입력
                st.chat_message("user", avatar="./assets/user.png").write(user_input)
                logger.info("사용자 메시지 화면 출력 완료")

                with st.chat_message("assistant", avatar="./assets/ai.png"):
                    # 빈 공간(컨테이너)을 만들어서, 여기에 토큰을 스트리밍 출력한다.
                    container = st.empty()

                try:
                    ai_answer = ""
                    # AI 답변 준비 중 spinner 표시
                    with st.spinner("🤖 AI가 답변을 준비하고 있습니다... 잠시만 기다려 주세요."):
                        container_messages, tool_args, agent_answer = stream_handler(
                            container,
                            agent,
                            {
                                "messages": [
                                    ("human", user_input),
                                ]
                            },
                            config,
                        )

                    # 대화기록을 저장한다.
                    add_message("user", user_input)
                    for tool_arg in tool_args:
                        add_message(
                            "assistant",
                            tool_arg["tool_result"],
                            "tool_result",
                            tool_arg["tool_name"],
                        )
                    add_message("assistant", agent_answer)
                    logger.info(f"일반 채팅 모드 실행 완료 - 응답 길이: {len(agent_answer)} 문자")
                    logger.info(f"도구 사용 횟수: {len(tool_args)}")
                except Exception as e:
                    logger.error(f"일반 채팅 모드 실행 중 오류: {e}", exc_info=True)
                    logger.error(f"오류 발생 시점 - 사용자 입력: {user_input[:50]}...")
                    st.error(f"대화 처리 중 오류가 발생했습니다: {e}")
        else:
            warning_msg.warning("사이드바에서 설정을 완료해주세요.")
            logger.warning("일반 채팅 에이전트가 설정되지 않음")
    
    else:  # 딥리서치 모드
        deep_research_agent = st.session_state["deep_research_agent"]
        
        if deep_research_agent is not None:
            current_step = st.session_state["deep_research_step"]
            logger.info(f"딥리서치 모드 실행 시작 - 현재 단계: {current_step}")
            
            if current_step == "initial":
                # 1단계: 초기 질문 입력 및 피드백 질문 생성
                logger.info("딥리서치 1단계: 피드백 질문 생성")
                st.session_state["initial_query"] = user_input
                
                with st.spinner("🤔 더 정확한 연구를 위한 맞춤형 질문을 생성하고 있습니다..."):
                    try:
                        selected_model = st.session_state.get("selected_model", "gpt-4o-mini")
                        feedback_questions = generate_feedback_questions(
                            query=user_input,
                            model_name=selected_model,
                            max_feedbacks=3
                        )
                        
                        # 피드백 질문 유효성 검증
                        if feedback_questions and isinstance(feedback_questions, list):
                            valid_questions = [q for q in feedback_questions if q and q.strip()]
                            if valid_questions:
                                st.session_state["feedback_questions"] = valid_questions
                                st.session_state["feedback_answers"] = []  # 초기화
                                logger.info(f"피드백 질문 {len(valid_questions)}개 생성 완료")
                                
                                st.session_state["deep_research_step"] = "feedback"
                                st.write(f"### 🔬 딥리서치: {user_input}")
                                st.write("#### 🤔 추가 질문에 답변해 주세요")
                                st.write("더 정확한 리서치를 위해 다음 질문에 답변해 주세요:")
                                
                                # 첫 번째 질문만 표시
                                first_question = valid_questions[0]
                                st.write(f"**질문 1:** {first_question}")
                                
                                #st.info("위 질문에 대한 답변을 입력해 주세요.")
                                show_info_message("위 질문에 대한 답변을 입력해 주세요.")
                                logger.info(f"첫 번째 피드백 질문 표시: {first_question}")
                            else:
                                logger.info("유효한 피드백 질문이 없어 바로 연구 단계로 진행")
                                _execute_deep_research_directly(user_input, deep_research_agent)
                        else:
                            # 피드백 질문이 없으면 바로 연구 진행
                            logger.info("피드백 질문이 없어 바로 연구 단계로 진행")
                            _execute_deep_research_directly(user_input, deep_research_agent)
                            
                    except Exception as e:
                        logger.error(f"피드백 질문 생성 중 오류: {e}", exc_info=True)
                        st.error(f"피드백 질문 생성 중 오류가 발생했습니다: {e}")
                        # 오류 발생 시 바로 연구 진행
                        logger.info("오류로 인해 피드백 단계를 건너뛰고 바로 연구 진행")
                        try:
                            _execute_deep_research_directly(user_input, deep_research_agent)
                        except Exception as direct_error:
                            logger.error(f"직접 연구 실행도 실패: {direct_error}")
                            st.error(f"딥리서치 실행에 실패했습니다: {direct_error}")
                            st.session_state["deep_research_step"] = "initial"
                        
            elif current_step == "feedback":
                # 2단계: 피드백 답변 수집
                current_answer_index = len(st.session_state.get("feedback_answers", []))
                total_questions = len(st.session_state.get("feedback_questions", []))
                
                # 상태 유효성 검증
                if current_answer_index >= total_questions:
                    logger.warning("피드백 답변 수가 질문 수를 초과함, 상태 초기화")
                    st.session_state["deep_research_step"] = "initial"
                    st.rerun()
                
                logger.info(f"피드백 답변 수집 중 - {current_answer_index + 1}/{total_questions}")
                
                # 현재 질문에 대한 답변 저장
                if "feedback_answers" not in st.session_state:
                    st.session_state["feedback_answers"] = []
                    
                st.session_state["feedback_answers"].append(user_input)
                logger.info(f"질문 {current_answer_index + 1} 답변 저장: {user_input[:50]}...")
                
                # 현재까지의 진행상황 표시
                st.write(f"### 🔬 딥리서치: {st.session_state.get('initial_query', '')}")
                st.write("#### 📝 답변 진행상황")
                
                for i, (question, answer) in enumerate(zip(
                    st.session_state["feedback_questions"][:current_answer_index + 1],
                    st.session_state["feedback_answers"]
                ), 1):
                    st.write(f"**질문 {i}:** {question}")
                    st.write(f"**답변:** {answer}")
                    st.write("")
                
                # 다음 질문이 있는지 확인
                if current_answer_index + 1 < total_questions:
                    next_question = st.session_state["feedback_questions"][current_answer_index + 1]
                    st.write(f"**질문 {current_answer_index + 2}:** {next_question}")
                    #st.info("위 질문에 대한 답변을 입력해 주세요.")
                    show_info_message("위 질문에 대한 답변을 입력해 주세요.")
                    logger.info(f"다음 질문 표시: {next_question}")
                else:
                    # 모든 답변 완료, 딥리서치 실행
                    logger.info("모든 피드백 답변 완료, 딥리서치 실행 시작")
                    
                    try:
                        # 결합된 쿼리 생성
                        combined_query = combine_query_with_feedback(
                            st.session_state.get("initial_query", ""),
                            st.session_state.get("feedback_questions", []),
                            st.session_state.get("feedback_answers", [])
                        )
                        logger.info(f"결합된 쿼리 생성 완료: {combined_query[:100]}...")
                        
                        # 딥리서치 실행
                        breadth = st.session_state.get("deep_research_breadth", 2)
                        depth = st.session_state.get("deep_research_depth", 2)
                        
                        st.write("#### 🚀 딥리서치 시작")
                        
                        # 상태를 연구 중으로 변경하여 중복 실행 방지
                        st.session_state["deep_research_step"] = "research"
                        
                        # 딥리서치 실행 중 spinner 표시
                        with st.spinner("🔍 피드백을 반영하여 심층 연구를 진행하고 있습니다... 잠시만 기다려 주세요."):
                            final_report, full_result = deep_research_stream_handler(
                                streamlit_container=st.container(),
                                agent=deep_research_agent,
                                query=combined_query,
                                breadth=breadth,
                                depth=depth,
                                feedback_answers=st.session_state["feedback_answers"]
                            )
                        logger.info("딥리서치 실행 완료")
                        
                        # 결과 표시
                        if final_report:
                            #st.success("🎉 피드백 기반 딥리서치가 완료되었습니다!")
                            show_success_message("피드백 기반 딥리서치가 완료되었습니다!")
                            st.write("#### 📋 최종 보고서")
                            st.markdown(final_report)
                            
                            # 보고서 다운로드 버튼
                            st.download_button(
                                label="📄 보고서 다운로드 (Markdown)",
                                data=final_report,
                                file_name=f"deep_research_report_{st.session_state.get('initial_query', 'research')[:20]}.md",
                                mime="text/markdown"
                            )
                        else:
                            #st.warning("⚠️ 딥리서치가 완료되었지만 보고서가 생성되지 않았습니다.")
                            show_warning_message("딥리서치가 완료되었지만 보고서가 생성되지 않았습니다.")
                        
                        # 연구 완료 후 상태 초기화
                        _reset_deep_research_state()
                        logger.info("딥리서치 워크플로우 완료, 상태 초기화")
                        
                    except Exception as e:
                        logger.error(f"딥리서치 실행 중 오류: {e}", exc_info=True)
                        st.error(f"딥리서치 실행 중 오류가 발생했습니다: {e}")
                        _reset_deep_research_state()
                        
            elif current_step == "research":
                # 이미 연구가 진행 중인 경우 - 중복 실행 방지
                logger.info("딥리서치가 이미 진행 중입니다.")
                #st.info("🔍 딥리서치가 이미 진행 중입니다. 잠시만 기다려 주세요...")
                show_info_message("딥리서치가 이미 진행 중입니다. 잠시만 기다려 주세요...")
                st.write("💡 **현재 진행 중인 작업:**")
                st.write("- 🔎 웹에서 관련 정보 수집")
                st.write("- 🧠 정보 분석 및 학습")
                st.write("- 📝 최종 보고서 생성")
                st.write("---")
                st.write("⏳ 딥리서치는 보통 1-3분 정도 소요됩니다.")
                
        else:
            warning_msg.warning("사이드바에서 딥리서치 설정을 완료해주세요.")
            logger.warning("딥리서치 에이전트가 설정되지 않음")





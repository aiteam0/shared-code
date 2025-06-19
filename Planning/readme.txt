
**User**

@main.py 
어플리케이션은 streamlit으로 구현되어 있어. 처음 접속했을 때 팝업창을 띄워서 공지사항을 제공하고 싶어. context7을 통해 관련한 streamlit의 적절한 기능을 찾아줘.
공지사항에는 업데이트 된 내용과 5개 항목에 대해서 각 항목별로 내가 설정한 날짜와 시간을 기준으로 +7일을 기준으로 얼마나 남았는지 공지해주는 내용을 넣고 싶어. 코드를 수정하지 말고 어떻게 어느부분을 수정해야 할지 전체적인 코드를 제공해줘. 최소한의 변경개발을 하고 싶어.
using sequential thinking, context7

---

**Cursor**

조사 결과와 분석을 바탕으로 Streamlit에서 공지사항 팝업을 구현하는 최적의 방법을 제시하겠습니다.

## 🔍 Streamlit 팝업 구현 방법

**조사 결과:**
- **`st.dialog`** (Streamlit 1.34.0+): 가장 최신이고 공식적인 모달 다이얼로그 기능 ✅ **추천**
- `streamlit-modal` 라이브러리: 서드파티 라이브러리
- `st.popover`: 작은 팝업 형태 (공지사항에는 부적합)
- JavaScript alert: 제한적이고 스타일링 어려움

## 📋 구현 방안

최소한의 변경으로 다음과 같이 수정하시면 됩니다:

### 1. **추가할 import** (파일 상단에)

```python
from datetime import datetime, timedelta
```

### 2. **공지사항 설정 추가** (import 섹션 후에)

```python
# =============================================================================
# 공지사항 설정
# =============================================================================

# 업데이트 내용
UPDATE_NEWS = """
### 🚀 최신 업데이트 내용

**v2.1.0 업데이트 (2024.01.15)**
- 🔬 딥리서치 성능 30% 향상
- 📚 RAG 기능에 이미지 분석 추가
- 🎨 UI/UX 개선 및 현대자동차 테마 적용
- 🔧 안정성 개선 및 버그 수정

**v2.0.5 업데이트 (2024.01.10)**
- 💬 채팅 응답 속도 개선
- 🔍 검색 결과 정확도 향상
"""

# 5개 중요 일정 항목 (날짜와 시간을 원하는 대로 설정하세요)
NOTIFICATION_ITEMS = [
    {
        "name": "🎯 프로젝트 마일스톤 1차 점검",
        "target_date": "2024-02-15 14:00",
        "description": "1차 개발 완료 및 테스트 시작"
    },
    {
        "name": "🔧 시스템 정기 점검",
        "target_date": "2024-02-20 09:00", 
        "description": "서버 및 데이터베이스 점검"
    },
    {
        "name": "📋 월간 보고서 제출",
        "target_date": "2024-02-25 17:00",
        "description": "프로젝트 진행 상황 보고"
    },
    {
        "name": "👥 팀 워크샵 및 교육",
        "target_date": "2024-03-01 10:00",
        "description": "새로운 기술 스택 교육"
    },
    {
        "name": "🚀 베타 버전 배포",
        "target_date": "2024-03-05 16:00",
        "description": "사용자 테스트용 베타 배포"
    }
]

def calculate_days_remaining(target_date_str):
    """목표 날짜 + 7일까지의 남은 일수 계산"""
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d %H:%M")
        deadline = target_date + timedelta(days=7)  # +7일 추가
        now = datetime.now()
        remaining = deadline - now
        
        if remaining.days < 0:
            return 0, "기한 만료"
        elif remaining.days == 0:
            hours = remaining.seconds // 3600
            return 0, f"{hours}시간 남음"
        else:
            return remaining.days, f"{remaining.days}일 남음"
    except:
        return 0, "날짜 오류"

@st.dialog("📢 중요 공지사항", width="large")
def show_notification_dialog():
    """공지사항 팝업 다이얼로그"""
    
    # 업데이트 내용 표시
    st.markdown(UPDATE_NEWS)
    
    st.divider()
    
    # 중요 일정 표시
    st.markdown("### ⏰ 중요 일정 알림")
    st.markdown("*기준일로부터 +7일까지의 남은 시간을 표시합니다*")
    
    for i, item in enumerate(NOTIFICATION_ITEMS, 1):
        days_left, status_text = calculate_days_remaining(item["target_date"])
        
        # 상태에 따른 색상 결정
        if days_left == 0:
            status_color = "🔴"
        elif days_left <= 3:
            status_color = "🟡"
        else:
            status_color = "🟢"
        
        # 목표 날짜 포맷팅
        try:
            target_dt = datetime.strptime(item["target_date"], "%Y-%m-%d %H:%M")
            formatted_date = target_dt.strftime("%m월 %d일 %H:%M")
        except:
            formatted_date = item["target_date"]
        
        # 항목 표시
        st.markdown(f"""
        **{i}. {item['name']}**  
        📅 **기준일:** {formatted_date}  
        📝 **내용:** {item['description']}  
        {status_color} **상태:** {status_text}
        """)
        
        if i < len(NOTIFICATION_ITEMS):
            st.markdown("---")
    
    st.divider()
    
    # 닫기 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✅ 확인했습니다", type="primary", use_container_width=True):
            st.session_state["notification_shown"] = True
            st.rerun()
```

### 3. **세션 상태 초기화 추가** (기존 세션 상태 초기화 섹션에)

```python
# 공지사항 표시 여부 초기화 (기존 세션 상태 초기화들과 함께 추가)
if "notification_shown" not in st.session_state:
    st.session_state["notification_shown"] = False
    logger.info("공지사항 표시 상태 초기화")
```

### 4. **팝업 호출 로직 추가** (활성 모드 상태 초기화 후, 사이드바 설정 전에)

```python
# =============================================================================
# 공지사항 팝업 표시 (처음 접속 시에만)
# =============================================================================

# 처음 접속한 사용자에게만 공지사항 팝업 표시
if not st.session_state.get("notification_shown", False):
    show_notification_dialog()
```

## 📍 구체적인 삽입 위치

**main.py**에서 다음 위치들에 코드를 삽입하세요:

### 위치 1: Import 섹션 (라인 1-20 근처)
```python
from datetime import datetime, timedelta  # 추가
```

### 위치 2: 공지사항 설정 (라인 50-100 근처, 함수 정의 섹션)
전체 공지사항 설정 코드 블록을 추가

### 위치 3: 세션 상태 초기화 (라인 280-300 근처)
```python
# 기존 세션 상태 초기화들과 함께
if "notification_shown" not in st.session_state:
    st.session_state["notification_shown"] = False
    logger.info("공지사항 표시 상태 초기화")
```

### 위치 4: 팝업 호출 (라인 320-350 근처, 사이드바 설정 전)
```python
# 처음 접속한 사용자에게만 공지사항 팝업 표시
if not st.session_state.get("notification_shown", False):
    show_notification_dialog()
```

## 🎯 주요 특징

1. **처음 접속 시에만 표시**: 세션 상태로 관리
2. **날짜 계산 자동화**: +7일 기준으로 남은 일수 표시
3. **시각적 구분**: 색상으로 긴급도 표시 (🔴🟡🟢)
4. **사용자 정의 가능**: 5개 항목의 날짜와 내용 쉽게 변경
5. **최소한의 변경**: 기존 코드 구조 유지

## 🔧 설정 방법

1. `NOTIFICATION_ITEMS` 리스트에서 날짜와 내용을 원하는 대로 수정
2. `UPDATE_NEWS`에서 업데이트 내용 수정
3. 필요에 따라 색상이나 스타일 조정

이렇게 구현하면 사용자가 처음 접속할 때만 팝업이 표시되고, 확인 버튼을 누르면 해당 세션에서는 더 이상 표시되지 않습니다.

```python
from datetime import datetime, timedelta
```

```python
# =============================================================================
# 공지사항 설정
# =============================================================================

# 업데이트 내용
UPDATE_NEWS = """
### 🚀 최신 업데이트 내용

**v2.1.0 업데이트 (2024.01.15)**
- 🔬 딥리서치 성능 30% 향상
- 📚 RAG 기능에 이미지 분석 추가
- 🎨 UI/UX 개선 및 현대자동차 테마 적용
- 🔧 안정성 개선 및 버그 수정

**v2.0.5 업데이트 (2024.01.10)**
- 💬 채팅 응답 속도 개선
- 🔍 검색 결과 정확도 향상
"""

# 5개 중요 일정 항목 (날짜와 시간을 원하는 대로 설정하세요)
NOTIFICATION_ITEMS = [
    {
        "name": "🎯 프로젝트 마일스톤 1차 점검",
        "target_date": "2024-02-15 14:00",
        "description": "1차 개발 완료 및 테스트 시작"
    },
    {
        "name": "🔧 시스템 정기 점검",
        "target_date": "2024-02-20 09:00", 
        "description": "서버 및 데이터베이스 점검"
    },
    {
        "name": "📋 월간 보고서 제출",
        "target_date": "2024-02-25 17:00",
        "description": "프로젝트 진행 상황 보고"
    },
    {
        "name": "👥 팀 워크샵 및 교육",
        "target_date": "2024-03-01 10:00",
        "description": "새로운 기술 스택 교육"
    },
    {
        "name": "🚀 베타 버전 배포",
        "target_date": "2024-03-05 16:00",
        "description": "사용자 테스트용 베타 배포"
    }
]

def calculate_days_remaining(target_date_str):
    """목표 날짜 + 7일까지의 남은 일수 계산"""
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d %H:%M")
        deadline = target_date + timedelta(days=7)  # +7일 추가
        now = datetime.now()
        remaining = deadline - now
        
        if remaining.days < 0:
            return 0, "기한 만료"
        elif remaining.days == 0:
            hours = remaining.seconds // 3600
            return 0, f"{hours}시간 남음"
        else:
            return remaining.days, f"{remaining.days}일 남음"
    except:
        return 0, "날짜 오류"

@st.dialog("📢 중요 공지사항", width="large")
def show_notification_dialog():
    """공지사항 팝업 다이얼로그"""
    
    # 업데이트 내용 표시
    st.markdown(UPDATE_NEWS)
    
    st.divider()
    
    # 중요 일정 표시
    st.markdown("### ⏰ 중요 일정 알림")
    st.markdown("*기준일로부터 +7일까지의 남은 시간을 표시합니다*")
    
    for i, item in enumerate(NOTIFICATION_ITEMS, 1):
        days_left, status_text = calculate_days_remaining(item["target_date"])
        
        # 상태에 따른 색상 결정
        if days_left == 0:
            status_color = "🔴"
        elif days_left <= 3:
            status_color = "🟡"
        else:
            status_color = "🟢"
        
        # 목표 날짜 포맷팅
        try:
            target_dt = datetime.strptime(item["target_date"], "%Y-%m-%d %H:%M")
            formatted_date = target_dt.strftime("%m월 %d일 %H:%M")
        except:
            formatted_date = item["target_date"]
        
        # 항목 표시
        st.markdown(f"""
        **{i}. {item['name']}**  
        📅 **기준일:** {formatted_date}  
        📝 **내용:** {item['description']}  
        {status_color} **상태:** {status_text}
        """)
        
        if i < len(NOTIFICATION_ITEMS):
            st.markdown("---")
    
    st.divider()
    
    # 닫기 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✅ 확인했습니다", type="primary", use_container_width=True):
            st.session_state["notification_shown"] = True
            st.rerun()
```

```python
# 공지사항 표시 여부 초기화 (기존 세션 상태 초기화들과 함께 추가)
if "notification_shown" not in st.session_state:
    st.session_state["notification_shown"] = False
    logger.info("공지사항 표시 상태 초기화")
```

```python
# =============================================================================
# 공지사항 팝업 표시 (처음 접속 시에만)
# =============================================================================

# 처음 접속한 사용자에게만 공지사항 팝업 표시
if not st.session_state.get("notification_shown", False):
    show_notification_dialog()
```

```python
from datetime import datetime, timedelta  # 추가
```

```python
# 기존 세션 상태 초기화들과 함께
if "notification_shown" not in st.session_state:
    st.session_state["notification_shown"] = False
    logger.info("공지사항 표시 상태 초기화")
```

```python
# 처음 접속한 사용자에게만 공지사항 팝업 표시
if not st.session_state.get("notification_shown", False):
    show_notification_dialog()
```


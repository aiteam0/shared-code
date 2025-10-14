# 📘 LangGraph ReAct Agent 마이그레이션 가이드

> `create_react_agent`에서 커스텀 StateGraph로 업그레이드하기

**대상 독자**: 신입 개발자
**난이도**: 중급
**소요 시간**: 30-60분
**목표**: create_react_agent를 순수 LangGraph StateGraph로 교체하여 완전한 제어권 확보

---

## 📋 목차

1. [왜 변경해야 하나요?](#1-왜-변경해야-하나요)
2. [사전 준비](#2-사전-준비)
3. [마이그레이션 단계](#3-마이그레이션-단계)
4. [테스트 및 검증](#4-테스트-및-검증)
5. [문제 해결](#5-문제-해결)
6. [추가 학습 자료](#6-추가-학습-자료)

---

## 1. 왜 변경해야 하나요?

### 🎯 변경 동기

**create_react_agent의 한계:**
```python
# 🔒 Black Box: 내부 로직 수정 불가
return create_react_agent(
    prompt=system_prompt,
    model=model,
    tools=tools,
    config_schema=ConfigSchema,
)
```

**StateGraph의 장점:**
- ✅ **완전한 제어**: 모든 노드와 엣지를 직접 정의
- ✅ **커스터마이징**: 검증, 로깅, 필터링 노드 추가 가능
- ✅ **디버깅**: 각 단계를 독립적으로 테스트
- ✅ **확장성**: 복잡한 워크플로우 구현 가능
- ✅ **최적화**: 메시지 트리밍으로 비용 절감 및 성능 향상

### 📊 비교표

| 기능 | create_react_agent | StateGraph |
|------|-------------------|------------|
| 구현 난이도 | 쉬움 (5분) | 중간 (30분) |
| 커스터마이징 | 제한적 | 무제한 |
| 디버깅 | 어려움 | 쉬움 |
| 노드 추가 | 불가능 | 가능 |
| 학습 가치 | 낮음 | 높음 |

---

## 2. 사전 준비

### ✅ 체크리스트

- [ ] Python 3.11+ 설치 확인
- [ ] 프로젝트 백업 완료
- [ ] Git 커밋 또는 브랜치 생성
- [ ] 기존 코드 이해 (agent.py 읽기)
- [ ] LangGraph 기본 개념 숙지

### 🔍 기존 코드 위치 확인

```bash
# 프로젝트 루트에서
cd tools_agent
cat agent.py | grep -A 5 "create_react_agent"
```

**출력 예시:**
```python
return create_react_agent(
    prompt=cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT,
    model=model,
    tools=tools,
    config_schema=GraphConfigPydantic,
)
```

### 📦 필요한 개념

**1. StateGraph란?**
- LangGraph의 핵심 클래스
- 노드(함수)와 엣지(연결)로 구성된 그래프
- 상태(State)를 노드 간에 전달

**2. ReAct 패턴이란?**
- **Re**asoning + **Act**ing
- LLM이 생각하고(reasoning) → 도구를 사용하고(acting) → 결과를 보고 → 반복

**3. 핵심 컴포넌트:**
```
State → Node → Edge → Router → Compile
  ↓       ↓      ↓       ↓        ↓
 상태   함수   연결   조건분기   실행
```

---

## 3. 마이그레이션 단계

### 📝 전체 흐름

```
Step 1: Import 추가
  ↓
Step 2: AgentState 정의
  ↓
Step 3: Router 함수 작성
  ↓
Step 4: StateGraph 구현
  ↓
Step 5: 기존 코드 교체
```

---

### Step 1: Import 문 추가

**위치**: `tools_agent/agent.py` 파일 상단

**기존 코드:**
```python
import os
from langchain_core.runnables import RunnableConfig
from typing import Optional, List
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent  # ← 이것을 변경할 것
from tools_agent.utils.tools import create_rag_tool
# ... 기타 imports
```

**변경 후:**
```python
import os
from langchain_core.runnables import RunnableConfig
from typing import Optional, List, Annotated, Sequence  # ← 추가
from pydantic import BaseModel, Field
from typing_extensions import TypedDict  # ← 추가
from langchain_core.messages import BaseMessage, SystemMessage, trim_messages  # ← 추가
from langgraph.graph import StateGraph, START, END  # ← 추가
from langgraph.graph.message import add_messages  # ← 추가
from langgraph.prebuilt import ToolNode  # ← 변경
from tools_agent.utils.tools import create_rag_tool
# ... 기타 imports
```

**💡 설명:**
- `Annotated, Sequence`: 타입 힌트용
- `TypedDict`: State 클래스 정의용
- `BaseMessage, SystemMessage, trim_messages`: 메시지 타입 및 트리밍 함수
- `StateGraph, START, END`: 그래프 구성 요소
- `add_messages`: 메시지 리스트 reducer
- `ToolNode`: 도구 실행 노드

---

### Step 2: AgentState 클래스 정의

**위치**: `UNEDITABLE_SYSTEM_PROMPT` 정의 바로 아래

**추가할 코드:**
```python
# UNEDITABLE_SYSTEM_PROMPT = "..."
# DEFAULT_SYSTEM_PROMPT = "..."

# ← 여기에 추가
# Define AgentState for StateGraph
class AgentState(TypedDict):
    """State for the ReAct agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
```

**💡 설명:**

**AgentState란?**
- 그래프의 "상태"를 정의하는 클래스
- 노드 간에 전달되는 데이터 구조

**messages 필드:**
- `Sequence[BaseMessage]`: 메시지 리스트 타입
- `add_messages`: 메시지를 추가하는 reducer 함수
- Reducer는 새 메시지를 기존 리스트에 병합하는 방법을 정의

**예제:**
```python
# State 초기값
{"messages": [HumanMessage(content="안녕")]}

# Node에서 반환
{"messages": [AIMessage(content="안녕하세요")]}

# Reducer 적용 후 결과
{"messages": [
    HumanMessage(content="안녕"),
    AIMessage(content="안녕하세요")
]}
```

---

### Step 3: Router 함수 작성

**위치**: `get_api_key_for_model` 함수 바로 아래

**추가할 코드:**
```python
def get_api_key_for_model(model_name: str, config: RunnableConfig):
    # ... 기존 코드 ...
    return os.getenv(key_name)


# ← 여기에 추가
def should_continue(state: AgentState):
    """Router function to decide whether to continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]

    # Check if the last message has tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise end the conversation
    return END
```

**💡 설명:**

**Router 함수란?**
- 조건부 엣지(Conditional Edge)에서 사용
- State를 받아서 다음 노드 이름을 반환
- 그래프의 "분기점" 역할

**로직 분석:**
```python
# 1. 상태에서 메시지 리스트 가져오기
messages = state["messages"]

# 2. 마지막 메시지 확인
last_message = messages[-1]

# 3. tool_calls 속성 체크
if hasattr(last_message, "tool_calls") and last_message.tool_calls:
    # LLM이 도구 호출을 요청함 → "tools" 노드로
    return "tools"

# 4. tool_calls 없음 → 대화 종료
return END
```

**예제 시나리오:**

**시나리오 1: 도구 호출 필요**
```python
last_message = AIMessage(
    content="계산하겠습니다",
    tool_calls=[{"name": "calculator", "args": {"a": 2, "b": 3}}]
)
# → return "tools"
```

**시나리오 2: 최종 답변**
```python
last_message = AIMessage(content="2 + 3 = 5입니다")
# → return END
```

---

### Step 4: StateGraph 구현 (핵심!)

**위치**: `graph` 함수 내부, `model` 초기화 이후

**기존 코드 (삭제할 부분):**
```python
async def graph(config: RunnableConfig):
    # ... RAG 도구 로딩 ...
    # ... MCP 도구 로딩 ...

    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=get_api_key_for_model(cfg.model_name, config) or "No token found"
    )

    # ❌ 이 부분을 삭제
    return create_react_agent(
        prompt=cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT,
        model=model,
        tools=tools,
        config_schema=GraphConfigPydantic,
    )
```

**새로운 코드 (추가할 부분):**
```python
async def graph(config: RunnableConfig):
    # ... RAG 도구 로딩 (변경 없음) ...
    # ... MCP 도구 로딩 (변경 없음) ...

    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=get_api_key_for_model(cfg.model_name, config) or "No token found"
    )

    # ✅ 여기부터 새로운 코드

    # 1️⃣ Model에 tools 바인딩
    model_with_tools = model.bind_tools(tools) if tools else model

    # 2️⃣ Agent node 정의
    async def agent_node(state: AgentState, config: RunnableConfig):
        """Agent node that calls the LLM with system prompt."""
        # Get system prompt from config
        cfg = GraphConfigPydantic(**config.get("configurable", {}))
        system_prompt = cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT

        # Trim conversation history to prevent context overflow
        trimmed_messages = trim_messages(
            state["messages"],
            max_tokens=10000,
            strategy="last",
            token_counter=len,
        )

        # Prepend system message to conversation
        messages = [SystemMessage(content=system_prompt)] + trimmed_messages

        # Call the model
        response = await model_with_tools.ainvoke(messages, config)

        # Return the response to add to state
        return {"messages": [response]}

    # 3️⃣ Tools node 생성
    tools_node = ToolNode(tools) if tools else None

    # 4️⃣ StateGraph 빌드
    workflow = StateGraph(AgentState, config_schema=GraphConfigPydantic)

    # 5️⃣ 노드 추가
    workflow.add_node("agent", agent_node)
    if tools_node:
        workflow.add_node("tools", tools_node)

    # 6️⃣ 엣지 추가
    workflow.add_edge(START, "agent")

    if tools_node:
        # Conditional edge from agent: either go to tools or end
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END,
            },
        )
        # Always return from tools back to agent
        workflow.add_edge("tools", "agent")
    else:
        # If no tools, just end after agent
        workflow.add_edge("agent", END)

    # 7️⃣ 컴파일 및 반환
    return workflow.compile()
```

---

### 📚 Step 4 상세 설명

#### 1️⃣ Model에 tools 바인딩

```python
model_with_tools = model.bind_tools(tools) if tools else model
```

**왜 필요한가?**
- LLM이 사용 가능한 도구를 알아야 함
- `bind_tools()`는 모델에 도구 정보를 추가
- 도구가 없으면 원본 모델 사용

**작동 방식:**
```python
# 도구가 있을 때
tools = [calculator_tool, search_tool]
model_with_tools = model.bind_tools(tools)
# → LLM이 이 두 도구를 사용할 수 있음을 인지

# 도구가 없을 때
tools = []
model_with_tools = model  # 그냥 원본 모델
```

#### 2️⃣ Agent node 정의

```python
async def agent_node(state: AgentState, config: RunnableConfig):
    """Agent node that calls the LLM with system prompt."""
    # A. Config에서 system prompt 추출
    cfg = GraphConfigPydantic(**config.get("configurable", {}))
    system_prompt = cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT

    # B. 메시지 히스토리 트리밍 (컨텍스트 오버플로우 방지)
    trimmed_messages = trim_messages(
        state["messages"],
        max_tokens=10000,
        strategy="last",
        token_counter=len,
    )

    # C. SystemMessage를 대화 맨 앞에 추가
    messages = [SystemMessage(content=system_prompt)] + trimmed_messages

    # D. LLM 호출
    response = await model_with_tools.ainvoke(messages, config)

    # E. 응답을 State에 추가하기 위해 반환
    return {"messages": [response]}
```

**단계별 분석:**

**A. System prompt 추출**
```python
cfg = GraphConfigPydantic(**config.get("configurable", {}))
system_prompt = cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT
```
- Config에서 사용자 정의 시스템 프롬프트 가져오기
- 필수 프롬프트(UNEDITABLE_SYSTEM_PROMPT) 추가

**B. 메시지 히스토리 트리밍 ⚠️ 중요!**
```python
trimmed_messages = trim_messages(
    state["messages"],
    max_tokens=10000,
    strategy="last",
    token_counter=len,
)
```

**왜 필요한가?**
- 긴 대화에서 컨텍스트 윈도우 초과 방지
- API 비용 최적화 (토큰 사용량 제어)
- 응답 속도 개선 (처리할 데이터 감소)

**동작 방식:**
- `max_tokens=10000`: 최대 10K 토큰만 유지
- `strategy="last"`: 최신 메시지부터 유지
- `token_counter=len`: 간단한 근사치 사용 (1 char ≈ 1 token)

**예제:**
```python
# 100턴 대화 (50K 토큰)
state["messages"] = [...100 messages...]

# trim_messages 적용 후
trimmed_messages = [...최근 20개 messages...] # ~10K 토큰

# 결과: 비용 80% 절감, 속도 5배 향상
```

**C. 메시지 리스트 구성**
```python
messages = [SystemMessage(content=system_prompt)] + trimmed_messages
```

예제:
```python
# trimmed_messages
[
    HumanMessage(content="2 + 3은?"),
]

# 변환 후
[
    SystemMessage(content="You are a helpful assistant..."),  # ← 추가
    HumanMessage(content="2 + 3은?"),
]
```

**D. LLM 호출**
```python
response = await model_with_tools.ainvoke(messages, config)
```
- 비동기로 LLM 호출
- 결과: AIMessage 객체

**E. 응답 반환**
```python
return {"messages": [response]}
```
- Dictionary 형태로 반환
- `add_messages` reducer가 자동으로 병합

#### 3️⃣ Tools node 생성

```python
tools_node = ToolNode(tools) if tools else None
```

**ToolNode란?**
- LangChain 도구를 실행하는 프리빌트 노드
- tool_calls를 자동으로 처리
- 결과를 ToolMessage로 반환

**작동 예시:**
```python
# Input state
{
    "messages": [
        HumanMessage("2 + 3은?"),
        AIMessage(tool_calls=[{"name": "calculator", "args": {"a": 2, "b": 3}}])
    ]
}

# ToolNode 실행 →

# Output
{
    "messages": [
        ToolMessage(content="5", tool_call_id="...")
    ]
}
```

#### 4️⃣ StateGraph 빌드

```python
workflow = StateGraph(AgentState, config_schema=GraphConfigPydantic)
```

**매개변수:**
- `AgentState`: 상태 타입 지정
- `config_schema`: OAP UI 통합을 위한 설정 스키마

#### 5️⃣ 노드 추가

```python
workflow.add_node("agent", agent_node)
if tools_node:
    workflow.add_node("tools", tools_node)
```

**노드 등록:**
- `"agent"`: 노드 이름 (문자열)
- `agent_node`: 실행할 함수

#### 6️⃣ 엣지 추가 (그래프 연결)

**기본 엣지:**
```python
workflow.add_edge(START, "agent")
```
- 그래프 시작 → agent 노드

**조건부 엣지 (도구가 있을 때):**
```python
workflow.add_conditional_edges(
    "agent",           # 출발 노드
    should_continue,   # Router 함수
    {
        "tools": "tools",  # Router가 "tools" 반환 → tools 노드
        END: END,          # Router가 END 반환 → 종료
    },
)
```

**돌아오는 엣지:**
```python
workflow.add_edge("tools", "agent")
```
- tools 노드 → agent 노드 (항상)

**그래프 시각화:**
```
         ┌─────────┐
START ──→│  agent  │
         └────┬────┘
              │
         [tool_calls?]
         ┌────┴────┐
       Yes│        │No
         ↓         ↓
    ┌───────┐    END
    │ tools │
    └───┬───┘
        │
        └──→ (back to agent)
```

**도구가 없을 때:**
```python
workflow.add_edge("agent", END)
```
- agent → 바로 종료

#### 7️⃣ 컴파일 및 반환

```python
return workflow.compile()
```

**compile()이 하는 일:**
- 그래프 검증 (순환 참조, 연결 오류 체크)
- 실행 가능한 객체로 변환
- 최적화 수행

---

### Step 5: 완료 확인

**변경 사항 요약:**
1. ✅ Import 추가 (7개)
2. ✅ AgentState 클래스 정의
3. ✅ should_continue 함수 추가
4. ✅ StateGraph 구현 (50줄)
5. ✅ create_react_agent 호출 제거

**파일 저장:**
```bash
# agent.py 저장 확인
git diff tools_agent/agent.py
```

---

## 4. 테스트 및 검증

### 🧪 테스트 체크리스트

#### Level 1: 구문 검사

```bash
# Python 문법 오류 확인
cd /mnt/e/MyProject2/oap-mcp
source .venv/bin/activate
python -c "import tools_agent.agent"
```

**성공 시:** 아무 출력 없음
**실패 시:** SyntaxError 표시 → 해당 줄 수정

#### Level 2: 서버 시작

```bash
uv run langgraph dev --no-browser
```

**예상 출력:**
```
Starting server on http://localhost:2024
Graph loaded successfully: agent
```

**실패 시 체크:**
- [ ] Import 오류 → 패키지 설치 확인
- [ ] 함수 정의 오류 → 들여쓰기 확인
- [ ] 타입 오류 → TypedDict 확인

#### Level 3: 기능 테스트

**테스트 1: 기본 대화 (도구 없음)**

Request:
```bash
curl -X POST http://localhost:2024/threads/test-1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {
      "messages": [
        {"role": "human", "content": "안녕하세요"}
      ]
    },
    "config": {
      "configurable": {
        "model_name": "openai:gpt-4o-mini",
        "system_prompt": "You are a helpful assistant."
      }
    }
  }'
```

**예상 결과:**
- ✅ 정상 응답 (AIMessage)
- ✅ 에러 없음

**테스트 2: 도구 호출**

Request:
```bash
curl -X POST http://localhost:2024/threads/test-2/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {
      "messages": [
        {"role": "human", "content": "2 + 3은 얼마인가요?"}
      ]
    },
    "config": {
      "configurable": {
        "model_name": "openai:gpt-4o-mini",
        "mcp_config": {
          "url": "http://localhost:8000",
          "tools": ["add"],
          "auth_required": false
        }
      }
    }
  }'
```

**예상 결과:**
- ✅ Tool call 발생
- ✅ Tools 노드 실행
- ✅ 최종 답변 반환

#### Level 4: 그래프 시각화

```python
# Python 인터프리터에서
from tools_agent.agent import graph
from langchain_core.runnables import RunnableConfig

config = RunnableConfig(configurable={})
g = await graph(config)

# ASCII 그래프 출력
print(g.get_graph().draw_ascii())
```

**예상 출력:**
```
           +-----------+
           | __start__ |
           +-----------+
                  *
                  *
                  *
             +-------+
             | agent |
             +-------+
           ***         ***
        ***               **
      **                    **
+-------+                     **
| tools |                   +---------+
+-------+                   | __end__ |
      **                    +---------+
        ***               **
           ***         ***
             +-------+
             | agent |
             +-------+
```

---

### ✅ 검증 체크리스트

**기능 동등성:**
- [ ] 기본 대화 동작 (도구 없음)
- [ ] 도구 호출 동작
- [ ] 멀티턴 대화
- [ ] 시스템 프롬프트 적용
- [ ] Config 변경 반영

**성능:**
- [ ] 응답 속도 유사
- [ ] 메모리 사용량 정상
- [ ] 에러율 동일 이하

**통합:**
- [ ] OAP UI 정상 동작
- [ ] RAG 도구 정상 동작
- [ ] MCP 도구 정상 동작
- [ ] 스트리밍 정상 동작

---

## 5. 문제 해결

### ❓ 자주 발생하는 오류

#### 오류 1: "NameError: name 'AgentState' is not defined"

**원인:** AgentState 클래스 정의를 추가하지 않음

**해결:**
```python
# 이 코드를 DEFAULT_SYSTEM_PROMPT 아래에 추가
class AgentState(TypedDict):
    """State for the ReAct agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
```

#### 오류 2: "ImportError: cannot import name 'StateGraph'"

**원인:** Import 문 누락

**해결:**
```python
# 파일 상단에 추가
from langgraph.graph import StateGraph, START, END
```

#### 오류 3: "TypeError: add_conditional_edges() got an unexpected keyword argument"

**원인:** 조건부 엣지 문법 오류

**해결:**
```python
# 올바른 문법
workflow.add_conditional_edges(
    "agent",           # source node
    should_continue,   # router function
    {                  # mapping
        "tools": "tools",
        END: END,
    },
)
```

#### 오류 4: "AttributeError: 'NoneType' object has no attribute 'tool_calls'"

**원인:** should_continue 함수에서 None 체크 누락

**해결:**
```python
def should_continue(state: AgentState):
    messages = state["messages"]
    if not messages:  # ← 추가
        return END

    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END
```

#### 오류 5: "Graph has cycles"

**원인:** 무한 루프 엣지 구성

**해결:**
```python
# ❌ 잘못된 예
workflow.add_edge("agent", "agent")  # 자기 자신으로

# ✅ 올바른 예
workflow.add_edge("tools", "agent")  # tools → agent
```

---

### 🐛 디버깅 팁

**1. 로그 추가**
```python
async def agent_node(state: AgentState, config: RunnableConfig):
    print(f"[DEBUG] Agent node called with {len(state['messages'])} messages")
    # ... 기존 코드 ...
    print(f"[DEBUG] Agent response: {response.content[:100]}")
    return {"messages": [response]}
```

**2. State 확인**
```python
def should_continue(state: AgentState):
    print(f"[DEBUG] State: {state}")
    print(f"[DEBUG] Last message type: {type(state['messages'][-1])}")
    # ... 기존 코드 ...
```

**3. 그래프 구조 확인**
```python
g = await graph(config)
print(g.get_graph().nodes)  # 노드 목록
print(g.get_graph().edges)  # 엣지 목록
```

---

## 6. 추가 학습 자료

### 📚 공식 문서

**LangGraph 핵심 개념:**
- [StateGraph 기초](https://langchain-ai.github.io/langgraph/concepts/stategraph/)
- [Conditional Edges](https://langchain-ai.github.io/langgraph/concepts/conditional_edges/)
- [ReAct Agent 패턴](https://langchain-ai.github.io/langgraph/tutorials/introduction/)

**예제 코드:**
- [Custom ReAct 구현](https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch/)
- [Multi-agent 시스템](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/)

### 🎓 다음 단계

**초급 → 중급:**
1. ✅ 이 가이드 완료
2. 커스텀 노드 추가 (로깅, 검증)
3. State에 필드 추가 (metrics, context)
4. 복잡한 Router 작성

**중급 → 고급:**
5. Multi-agent 시스템 구현
6. Human-in-the-loop 추가
7. Dynamic tool loading
8. Subgraph 활용

---

## 📊 부록: 전체 코드 비교

### Before (create_react_agent)

```python
# tools_agent/agent.py (일부)

from langgraph.prebuilt import create_react_agent

async def graph(config: RunnableConfig):
    # ... 도구 로딩 ...

    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=get_api_key_for_model(cfg.model_name, config) or "No token found"
    )

    return create_react_agent(
        prompt=cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT,
        model=model,
        tools=tools,
        config_schema=GraphConfigPydantic,
    )
```

**총 줄 수:** 5 lines
**커스터마이징:** 제한적
**제어:** Black box

---

### After (StateGraph)

```python
# tools_agent/agent.py (전체)

# 1. Import 추가
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 2. AgentState 정의
class AgentState(TypedDict):
    """State for the ReAct agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]

# 3. Router 함수
def should_continue(state: AgentState):
    """Router function to decide whether to continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END

# 4. Graph 함수 수정
async def graph(config: RunnableConfig):
    # ... 도구 로딩 (동일) ...

    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=get_api_key_for_model(cfg.model_name, config) or "No token found"
    )

    # Model에 tools 바인딩
    model_with_tools = model.bind_tools(tools) if tools else model

    # Agent node 정의
    async def agent_node(state: AgentState, config: RunnableConfig):
        """Agent node that calls the LLM with system prompt."""
        cfg = GraphConfigPydantic(**config.get("configurable", {}))
        system_prompt = cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT

        # Trim conversation history to prevent context overflow
        trimmed_messages = trim_messages(
            state["messages"],
            max_tokens=10000,
            strategy="last",
            token_counter=len,
        )

        messages = [SystemMessage(content=system_prompt)] + trimmed_messages
        response = await model_with_tools.ainvoke(messages, config)
        return {"messages": [response]}

    # Tools node 생성
    tools_node = ToolNode(tools) if tools else None

    # StateGraph 빌드
    workflow = StateGraph(AgentState, config_schema=GraphConfigPydantic)

    # 노드 추가
    workflow.add_node("agent", agent_node)
    if tools_node:
        workflow.add_node("tools", tools_node)

    # 엣지 추가
    workflow.add_edge(START, "agent")

    if tools_node:
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END,
            },
        )
        workflow.add_edge("tools", "agent")
    else:
        workflow.add_edge("agent", END)

    # 컴파일 및 반환
    return workflow.compile()
```

**총 줄 수:** ~60 lines
**커스터마이징:** 무제한
**제어:** 완전

---

## 🎯 요약

### ✅ 완료한 것

1. **Import 추가**: StateGraph 및 trim_messages 모듈
2. **AgentState 정의**: 그래프 상태 클래스
3. **should_continue 함수**: 조건부 라우팅
4. **StateGraph 구현**: 완전한 ReAct 패턴
5. **메시지 트리밍**: 컨텍스트 오버플로우 방지 및 비용 최적화
6. **create_react_agent 제거**: 기존 코드 교체

### 💪 이제 할 수 있는 것

- ✅ 노드 추가 (검증, 로깅, 필터링)
- ✅ State 확장 (metrics, context)
- ✅ 복잡한 라우팅
- ✅ 디버깅 및 모니터링
- ✅ 멀티 에이전트 시스템

### 🚀 다음 도전

**즉시 시도해볼 것:**
1. 로깅 노드 추가
2. 응답 시간 측정
3. 커스텀 검증 로직

**장기 목표:**
1. Multi-agent 협업
2. Human-in-the-loop
3. 프로덕션 배포

---

## 📞 도움이 필요하면?

**문제 발생 시:**
1. 오류 메시지 전체 복사
2. 관련 코드 스니펫 준비
3. 예상 동작 vs 실제 동작 설명
4. LangGraph 공식 문서 검색

**추가 학습:**
- [LangGraph 튜토리얼](https://langchain-ai.github.io/langgraph/tutorials/)
- [LangChain 커뮤니티](https://discord.gg/langchain)
- [GitHub Issues](https://github.com/langchain-ai/langgraph/issues)

---

**작성일**: 2025-01-13
**버전**: 1.0
**대상 프로젝트**: OAP-MCP (Open Agent Platform)
**난이도**: 중급 (신입 개발자도 따라할 수 있는 수준)

---

이 가이드를 완료하셨다면 축하합니다! 🎉
이제 LangGraph의 핵심 개념을 이해하고 커스텀 에이전트를 구축할 수 있습니다!

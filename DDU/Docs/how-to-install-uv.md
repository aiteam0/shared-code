# uv 사용 워크플로우 요약 (대화 기반 정리)

이 문서는 `uv`를 처음 사용하여 파이썬 프로젝트 환경을 설정하고 관리하는 과정을 단계별로 요약합니다. 특히, 프로젝트 폴더 외부 가상환경 사용 시 주의사항과 해결 방법을 포함합니다.

## 1. uv 설치

-   **설치 확인:**
    ```bash
    uv --version
    ```
-   **설치 (운영체제에 맞게 선택):**
    -   macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
    -   Windows PowerShell: `irm https://astral.sh/uv/install.ps1 | iex`
    -   pip: `pip install uv`

## 2. 핵심 개념: `pyproject.toml` vs 가상환경

-   **`pyproject.toml`의 `[project].name`:**
    -   파이썬 **패키지(배포판)**의 공식 이름입니다. (예: `langgraph-mcp-agents`)
    -   패키지 빌드, 배포, 다른 프로젝트에서의 의존성 명시에 사용됩니다.
-   **가상환경 이름 (예: `.venv`, `langgraph-mcp-agents`):**
    -   격리된 파이썬 실행 환경을 담는 **폴더(디렉토리)**의 이름입니다.
    -   프로젝트 개발/실행을 위한 작업 공간이며, 패키지 이름과 직접적인 관련은 없습니다.

## 3. 가상환경 관리

### 3.1. 가상환경 생성 (`uv venv`)

-   **표준 방식 (권장):** 프로젝트 루트 폴더에서 실행하여 `.venv` 생성
    ```bash
    cd /path/to/your/project
    uv venv
    ```
    (결과: `/path/to/your/project/.venv` 생성)

-   **특정 경로/이름 지정:**
    ```bash
    # 예: 특정 폴더 내부에 생성 (사용자가 사용한 방식)

    ** labtop
    uv venv "C:\Users\Clark\envs\virtualenvs\langgraph-mcp-agents"
    (결과: `C:\Users\Clark\envs\virtualenvs\langgraph-mcp-agents` 생성)

    ** Desktop
    uv venv "D:\cursor\virtualenvs\langgraph-mcp-agents"
    ```
    

-   **주의:** `uv venv <경로>` 실행 시 `<경로>`가 이미 존재하고 가상환경이 아니면 오류 발생. (예: `uv venv "C:\Users\Clark\envs\virtualenvs"` 실행 시 오류) -> 이 경우, 그 *안에* 새 이름을 지정하여 생성해야 함 (`...\virtualenvs\my_env`).

### 3.2. 가상환경 활성화

-   **명령어 (가상환경 경로와 터미널에 맞게 사용):**
    -   macOS/Linux (bash/zsh): `source <venv_path>/bin/activate`
    -   Win Cmd: `<venv_path>\Scripts\activate.bat`
    -   Win PowerShell: `<venv_path>\Scripts\Activate.ps1`
        (예: `. C:\Users\Clark\envs\virtualenvs\langgraph-mcp-agents\Scripts\Activate.ps1` - PowerShell의 점(`.`)은 `source`와 유사)
        (예: `. D:\cursor\virtualenvs\langgraph-mcp-agents\Scripts\Activate.ps1` - PowerShell의 점(`.`)은 `source`와 유사)

-   **활성화 간편화 (PowerShell 예시):** PowerShell 프로필(`$PROFILE`)에 함수 또는 별칭 추가
    **프로파일 생성
    New-Item -Path $PROFILE -ItemType File -Force
    
    **열기
    notepad $PROFILE

    ```powershell
    # 프로필 파일($PROFILE)에 추가할 함수 예시
    function activate-langgraph-agents {
        . D:\cursor\virtualenvs\langgraph-mcp-agents\Scripts\activate.ps1
    }
    # 사용:activate-langgraph-agents
    ```
    
    ** 재시작 또는 수정한 뒤 PROFILE 실행 : 
    . $PROFILE

### 3.3. 활성화 상태 확인

-   **`VIRTUAL_ENV` 환경 변수 확인 (가장 확실):**
    -   macOS/Linux: `echo $VIRTUAL_ENV`
    -   Win Cmd: `echo %VIRTUAL_ENV%`
    -   Win PowerShell: `echo $env:VIRTUAL_ENV`
-   **`python` 실행 파일 경로 확인:**
    -   `which python` / `which python3` (macOS/Linux)
    -   `where python` (Windows)
-   **터미널 프롬프트 확인:** `(가상환경이름)` 표시 확인

### 3.4. 가상환경 비활성화

```bash
deactivate
```

## 4. 의존성 관리

### 4.1. `uv sync` vs `uv pip install -r requirements.txt`

-   **`uv sync`:**
    -   **기준:** `pyproject.toml` (및 `uv.lock` 우선)
    -   **동작:** 명시된 의존성 설치/업데이트 + **명시되지 않은 의존성 제거** (환경을 명세와 정확히 일치시킴)
    -   **락파일:** `uv.lock` 파일이 있으면 우선적으로 사용하여 재현성 보장.
-   **`uv pip install -r requirements.txt`:**
    -   **기준:** 지정된 `requirements.txt` 파일
    -   **동작:** 명시된 의존성 설치/업데이트 (기존 환경에 추가/변경, 제거 없음)
    -   **락파일:** 별도 `uv.lock` 참조 안 함. 재현성은 `requirements.txt`의 잠금 수준에 따라 다름.

### 4.2. 의존성 설치 (`uv sync` 사용)

-   **표준 방식 (가상환경이 프로젝트 내 `.venv`일 경우):**
    1.  `.venv` 활성화
    2.  프로젝트 폴더에서 실행:
        ```bash
        uv sync
        ```

-   **외부 가상환경 사용 시 (사용자의 경우):**
    1.  **외부 가상환경 활성화** (예: `Activate-LangGraphEnv`)
    2.  프로젝트 폴더로 이동 (`pyproject.toml` 있는 곳)
    3.  **`--active` 플래그 사용:**
        ```bash
        uv sync --active
        ```
        *이유: `--active` 플래그는 `uv`에게 기본값(`.venv`) 대신 현재 활성화된 환경(`VIRTUAL_ENV`)을 사용하도록 지시.*

-   ** requiterments로 uv 환경에 패키지 추가하기 **
    uv add -r requirements.txt

## 5. 코드 및 애플리케이션 실행

### 5.1. `uv run` 명령어

-   **기능:**
    1.  프로젝트 가상환경(`.venv` 기본) 찾기
    2.  의존성 자동 동기화 (필요시 `uv sync` 실행)
    3.  동기화된 환경에서 지정된 명령어 실행
-   **`poetry shell` 유사 기능:** 하위 셸에서 환경 활성화
    ```bash
    # .venv 환경이 프로젝트 내에 있을 때 사용 가능
    uv run bash         # Linux/macOS
    uv run powershell   # Windows PowerShell
    ```
    (주의: 현재 셸이 아닌 *새로운 하위 셸*에서 활성화됨)

-   **FastAPI 개발 서버 실행 예시:**
    ```bash
    # .venv 환경이 프로젝트 내에 있을 때 사용 가능
    uv run fastapi dev main.py
    ```
    (의미: uv 환경 준비 후, `main.py`를 개발 모드로 실행)

### 5.2. 외부 가상환경 사용 시 코드 실행 방법

-   **`uv run` 사용 불가:** `uv run`은 기본적으로 프로젝트 내 `.venv`를 찾으므로 외부 가상환경에서는 직접 사용하기 어려움.
-   **권장 방식:**
    1.  **먼저 외부 가상환경 활성화** (예: `Activate-LangGraphEnv`)
    2.  활성화된 셸에서 **직접 명령어 실행:**
        ```powershell
        # 예시: FastAPI 개발 서버 직접 실행
        (langgraph-mcp-agents) PS C:\path\to\project> fastapi dev main.py
        # 또는 uvicorn 직접 사용
        (langgraph-mcp-agents) PS C:\path\to\project> uvicorn main:app --reload
        ```
        (이 방식이 `poetry shell`로 들어간 후 명령어를 실행하는 것과 가장 유사함)

## 6. 권장 워크플로우 (요약)

-   **가장 원활한 `uv` 경험:**
    1.  가상환경은 프로젝트 루트 폴더 내에 `.venv`로 생성 (`uv venv`).
    2.  `.venv`를 활성화 (`source .venv/bin/activate` 등).
    3.  의존성 설치/동기화는 `uv sync` 사용.
    4.  간단한 명령어 실행은 `uv run <command>` 사용 (예: `uv run python script.py`).
    5.  활성화된 셸이 필요하면 `uv run <shell>` 사용 (예: `uv run bash`).
-   **외부 가상환경을 사용해야 하는 경우:**
    1.  외부 가상환경 생성 (`uv venv <external_path>`).
    2.  해당 환경 활성화 (전체 경로 또는 프로필 함수/별칭 사용).
    3.  의존성 설치/동기화 시 **`uv sync --active` 사용 필수**.
    4.  코드/애플리케이션 실행은 활성화된 셸에서 **직접 명령어 실행** (예: `python main.py`, `fastapi dev main.py`). `uv run`은 셸 활성화 용도로 부적합.

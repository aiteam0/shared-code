### 신입 개발자를 위한 Parser & Assembly 아웃풋 스키마 가이드 (JSON 구조 중심)

안녕하세요! 이 문서는 우리 시스템의 3가지 핵심 데이터(DocYOLO, Docling, Assembly)의 JSON 구조와 각 속성의 의미를 설명합니다. 이 구조를 이해하면 데이터를 효과적으로 활용하고 디버깅하는 데 큰 도움이 될 것입니다.

---

### 1. DocYOLO 스키마: The Architect's Blueprint

DocYOLO는 문서의 시각적 레이아웃을 분석하여, 각 요소의 위치와 시각적 유형을 정의합니다.

```json
{
  "api": "2.0",
  "model": "converted-from-content-list-v2",
  "usage": {
    "pages": 10
  },
  "content": {
    "html": "<h1 id='0'>...</h1><p id='1'>...</p>...",
    "markdown": "# ...\n\n...",
    "text": "..."
  },
  "elements": [
    {
      "id": 0,
      "page": 1,
      "category": "heading1",
      "content": {
        "text": "디지털 정부혁신 추진계획"
      },
      "coordinates": [ /* 4개의 [x, y] 좌표 배열 */ ],
      "base64_encoding": null
    },
    {
      "id": 1,
      "page": 1,
      "category": "table",
      "content": {
        "html": "<table id='62'>...</table>"
      },
      "coordinates": [ /* ... */ ],
      "base64_encoding": "iVBORw0KGgoAAA..."
    },
    {
      "id": 2,
      "page": 1,
      "category": "figure",
      "content": {
        "html": "<figure id='54'><img src=.../></figure>"
      },
      "coordinates": [ /* ... */ ],
      "base64_encoding": "iVBORw0KGgoAAA..."
    }
    // ... 추가 요소들
  ]
}
```

#### **주요 키(Key) 설명**
-   `model`: `"converted-from-content-list-v2"` (고정값)
-   `content`: 각 요소의 `content`를 단순히 합친 결과로, 논리적 순서나 완전성을 보장하지 않을 수 있습니다.
-   `elements[n].category`: 시각적 특징에 따라 결정됩니다.
    -   **케이스**: `"heading1"`, `"heading2"`, `"paragraph"`, `"table"`, `"figure"`, `"list"`, `"footer"` 등.
    -   **강점**: `table`과 `figure` 분류에 매우 강합니다.
-   `elements[n].coordinates`: 페이지 내 요소의 절대 위치 좌표. DocYOLO의 가장 신뢰도 높은 결과물입니다.
-   `elements[n].base64_encoding`: `category`가 `table` 또는 `figure`일 때, 해당 영역의 이미지를 인코딩한 문자열이 포함될 수 있습니다. 그 외에는 `null`일 수 있습니다.

---

### 2. Docling 스키마: The Editor's Manuscript

Docling은 텍스트의 논리적 흐름과 문맥을 분석하여, 의미 단위로 텍스트 덩어리(Segment)를 생성합니다.

```json
{
  "api": "2.0",
  "model": "docling-segments-combined-v1.3",
  "usage": {
    "pages": 10
  },
  "content": {
    "html": "<h1>...</h1><p>...</p>...",
    "markdown": "# ...\n\n...",
    "text": "..."
  },
  "elements": [
    {
      "category": "heading1",
      "content": {
        "text": "1. 엔진 오일 교체 절차"
      }
      // id, page, coordinates 등 다른 메타데이터 포함
    },
    {
      "category": "list",
      "content": {
        "text": "- 주입구 캡(A)을 엽니다.\n- 드레인 플러그(B)를 풀어 오일을 배출합니다."
      }
    },
    {
      "category": "footer",
      "content": {
        "text": "- 8 -"
      }
    }
    // ... 추가 요소들
  ]
}
```

#### **주요 키(Key) 설명**
-   `model`: `"docling-segments-combined-v1.3"` (고정값)
-   `content`: Docling이 분석한 텍스트 세그먼트들을 순서대로 합친 결과입니다.
-   `elements[n].category`: 텍스트의 스타일과 문맥(들여쓰기, 글머리 기호 등)에 따라 결정됩니다.
    -   **케이스**: `"heading1"`, `"paragraph"`, `"list"`, `"footer"`, `"header"` 등.
    -   **강점**: `list`와 같이 논리적 구조를 가진 텍스트 분류에 매우 강합니다.
-   `elements[n].content.text`: 논리적으로 의미가 통하는 텍스트 덩어리입니다. 시각적 구조물(예: 표)은 여러 개의 `paragraph`로 분해되어 나타날 수 있습니다.

---

### 3. Assembly 스키마: The General Contractor's Final Plan

Assembly는 DocYOLO와 Docling의 결과를 종합하여, 각 요소에 가장 적합한 분석을 채택하고 완전한 문서를 재구성합니다. **우리가 최종적으로 사용하는 데이터입니다.**

```json
{
  "api": "2.0",
  "model": "assembled-v1.0",
  "usage": {
    "pages": 10
  },
  "content": {
    "text": "전체 문서의 순수 텍스트...",
    "markdown": "전체 문서의 마크다운...",
    "html": "전체 문서의 HTML..."
  },
  "elements": [
    {
      "id": 0,
      "page": 1,
      "category": "heading1",
      "source_parser": "docling",
      "content": { /* ... */ },
      "coordinates": [ /* ... */ ]
    },
    {
      "id": 1,
      "page": 1,
      "category": "list",
      "source_parser": "docling",
      "content": { /* ... */ }
    },
    {
      "id": 2,
      "page": 1,
      "category": "table",
      "source_parser": "docyolo",
      "content": { /* ... */ }
    },
    {
      "id": 3,
      "page": 1,
      "category": "figure",
      "caption": "그림 1. 엔진 구조도",
      "has_caption": true,
      "source_parser": "docyolo",
      "content": { /* ... */ }
    }
  ]
}
```

#### **주요 키(Key) 설명**
-   `model`: `"assembled-v1.0"` (고정값)
-   `content`: **[가장 중요한 최상위 객체]** 최종 확정된 `elements`를 모두 조합하여 생성된, 문서 전체의 완전한 내용입니다. 이 객체 덕분에 전체 문서를 즉시 렌더링할 수 있습니다.
-   `elements[n].category`: 두 파서의 결과 중 더 신뢰도 높은 값으로 확정된 분류입니다.
-   `elements[n].source_parser`: **[매우 중요한 감사용 키]** 이 요소가 어떤 파서의 결과로부터 선택되었는지를 나타냅니다.
    -   **케이스**: `"docyolo"`, `"docling"`
    -   **활용**: `table` 요소가 깨져 보일 때, `source_parser`가 `docling`으로 잘못 설정되었는지 확인하는 등 디버깅에 필수적입니다.
-   `elements[n].caption`, `has_caption`: `category`가 `figure`일 때, Assembly 로직이 주변 텍스트에서 찾아낸 캡션 정보가 포함될 수 있습니다. 캡션이 없으면 `has_caption`은 `false`가 됩니다.






# 프로젝트 워크플로우 및 스키마 파악
_Exported on 7/6/2025 at 22:05:44 GMT+9 from Cursor (1.2.1)_

---

**User**

@complete_workflow.py @/assembly 
프로젝트를 설명하는 PRD를 작성하고 싶어. 
1. 전체적인 프로젝트의 워크플로우를 파악해봐. 
2. 인풋 스키마와 중간 산출물들의 스키마, 그리고 최종 아웃풋 스키마도 파악해봐.
3.document parser의 경우 복잡한 로직들이 통합되어 있으니 노드 단위까지 세부적으로 파악해.
너가 프로젝트의 구조화 프로세스를 파악하면 내가 다음 요청사항을 전달할께
using sequential thinking

---

**Cursor**

이 프로젝트의 전체 구조를 체계적으로 파악하기 위해 sequential thinking을 사용하겠습니다.

프로젝트 구조를 체계적으로 분석 완료했습니다. 다음은 **H-DDU-WIN** 프로젝트에 대한 상세한 분석입니다:

## 📋 프로젝트 전체 워크플로우 분석

### 🎯 **시스템 목적**
복잡한 PDF 문서를 고품질의 구조화된 데이터로 변환하는 **멀티 파서 기반 문서 처리 시스템**

### 🔄 **전체 워크플로우 구조**

```mermaid
graph TD
    A[PDF 입력] --> B[Document Parser]
    B --> C[Save Image Node]
    C --> D[Refine Content Node]
    D --> E[Add Translation]
    E --> F[Contextualize Text]
    F --> G[Create Elements Node]
    G --> H[Page Elements Extractor]
    
    H --> I[Image Entity Extractor]
    H --> J[Table Entity Extractor]
    
    I --> K[Merge Entity Node]
    J --> K
    
    K --> L[Reconstruct Elements Node]
    
    L --> M[Generate Comprehensive Markdown]
    L --> N[LangChain Document Node]
    
    M --> O[Save Final State]
    N --> O
    
    O --> P[최종 출력물들]
```

### 🏗️ **5단계 처리 구조**

1. **📄 단계 1: 문서 파싱 및 전처리**
   - PDF 파싱 → 이미지 저장 → 텍스트 정제

2. **🌐 단계 2: 언어 처리** 
   - 번역 → 문맥화 → 요소 생성

3. **🔍 단계 3: 엔티티 추출 (병렬)**
   - 페이지별 추출 → (이미지 엔티티 + 테이블 엔티티) 병렬 처리

4. **⚡ 단계 4: 최종 처리 (병렬)**
   - 엔티티 병합 → 요소 재구성 → (마크다운 생성 + 문서 생성) 병렬 처리

5. **💾 단계 5: 저장**
   - 최종 상태 저장

## 📊 **데이터 스키마 분석**

### 📥 **입력 스키마**
```json
{
  "pdf_file": "*.pdf",
  "parsers": {
    "docling": "구조화 파싱 강점",
    "docyolo": "텍스트 추출 강점"
  }
}
```

### 🔄 **중간 산출물 스키마**
```typescript
Element = {
  page: number,
  category: 'paragraph' | 'heading1' | 'table' | 'figure' | 'caption',
  content: {
    text: string,
    html?: string,
    markdown?: string,
    caption?: string
  },
  coordinates: Coordinate[],
  base64_encoding?: string,
  processing_status?: 'enhanced' | 'failed' | 'fallback',
  source_parser?: 'docling' | 'docyolo' | 'enhanced',
  extracted_caption?: string,
  has_caption?: boolean
}
```

### 📤 **최종 출력 스키마**
```json
{
  "api": "2.0",
  "model": "assembled-v1.0",
  "usage": {"pages": number},
  "elements": [Element],
  "content": {
    "text": "전체 문서 텍스트",
    "markdown": "전체 문서 마크다운", 
    "html": "전체 문서 HTML"
  }
}
```

**출력 파일들:**
- `*_final.json`: 최종 어셈블리 결과
- `*_documents.pkl`: LangChain 문서 객체들
- `*_final_state.json`: 전체 상태 정보
- `*.md`: 통합 마크다운 파일

## 🔧 **Document Parser 세부 노드 분석**

### 📋 **14개 노드 상세 구조**

| 노드 이름 | 역할 | 입력 | 출력 |
|-----------|------|------|------|
| `document_parser` | Upstage 파서 그래프 | PDF 파일 | ParseState |
| `save_image_node` | 이미지 저장 | ParseState | 이미지 경로 추가 |
| `refine_content_node` | 텍스트 정제 | ParseState | 정제된 텍스트 |
| `add_translation` | 번역 처리 | ParseState | 번역 결과 추가 |
| `contextualize_text` | 문맥화 | ParseState | 문맥화된 텍스트 |
| `create_elements_node` | 요소 생성 | ParseState | 구조화된 요소들 |
| `page_elements_extractor` | 페이지별 추출 | ParseState | 페이지별 요소 분류 |
| `image_entity_extractor` | 이미지 엔티티 추출 | ParseState | 향상된 이미지 요소 |
| `table_entity_extractor` | 테이블 엔티티 추출 | ParseState | 향상된 테이블 요소 |
| `merge_entity_node` | 엔티티 병합 | ParseState | 병합된 엔티티 |
| `reconstruct_elements_node` | 요소 재구성 | ParseState | 재구성된 요소 |
| `generate_comprehensive_markdown` | 마크다운 생성 | ParseState | 마크다운 파일 |
| `langchain_document_node` | LangChain 문서 생성 | ParseState | LangChain 문서 |
| `save_final_state` | 최종 상태 저장 | ParseState | 최종 결과 파일 |

## 🚀 **핵심 기술적 특징**

### 1. **🎯 Assembly 시스템 (핵심 혁신)**
- **멀티 파서 접근법**: Docling + DocYOLO 조합
- **정보 보존율**: 70% 손실 → **100% 보존**
- **LLM 기반 품질 향상**: GPT-4o-mini 최적화
- **Caption 처리 시스템**: 파서별 caption 구조 통합

### 2. **⚡ 성능 최적화**
- **병렬 처리**: 이미지/테이블 추출, 마크다운/문서 생성
- **Rate Limiting**: API 호출 최적화
- **배치 처리**: 대량 요소 효율적 처리

### 3. **🔧 확장성**
- **다중 모델 지원**: Azure OpenAI, OpenAI, Ollama
- **모듈화 구조**: 독립적 노드 설계
- **설정 기반**: 환경변수를 통한 유연한 제어

### 4. **🎨 품질 향상**
- **개별 요소 처리**: 매칭 실패 방지
- **다단계 검증**: 테이블 HTML 검증 + Fallback
- **중복 제거**: 지능적 중복 요소 처리

## 📈 **성능 지표**

| 항목 | 기존 | 개선 후 |
|------|------|---------|
| 이미지 보존율 | 4/14 (28%) | 14/14 (100%) |
| Caption 처리 | 부분적 손실 | 완전 보존 |
| 테이블 품질 | rowspan 누락 | 완전한 구조 |
| 처리 속도 | 순차 처리 | 병렬 처리 |
| 정보 손실 | 30% 손실 | 5% 미만 |

---

**✅ 프로젝트 구조 분석 완료!** 

이제 이 분석을 바탕으로 PRD의 다음 단계를 요청해주세요. 구체적으로 어떤 관점의 PRD를 원하시는지 알려주시면 더 세밀하게 작성할 수 있습니다.

```plaintext
graph TD
    A[PDF 입력] --> B[Document Parser]
    B --> C[Save Image Node]
    C --> D[Refine Content Node]
    D --> E[Add Translation]
    E --> F[Contextualize Text]
    F --> G[Create Elements Node]
    G --> H[Page Elements Extractor]
    
    H --> I[Image Entity Extractor]
    H --> J[Table Entity Extractor]
    
    I --> K[Merge Entity Node]
    J --> K
    
    K --> L[Reconstruct Elements Node]
    
    L --> M[Generate Comprehensive Markdown]
    L --> N[LangChain Document Node]
    
    M --> O[Save Final State]
    N --> O
    
    O --> P[최종 출력물들]
```

```json
{
  "pdf_file": "*.pdf",
  "parsers": {
    "docling": "구조화 파싱 강점",
    "docyolo": "텍스트 추출 강점"
  }
}
```

```typescript
Element = {
  page: number,
  category: 'paragraph' | 'heading1' | 'table' | 'figure' | 'caption',
  content: {
    text: string,
    html?: string,
    markdown?: string,
    caption?: string
  },
  coordinates: Coordinate[],
  base64_encoding?: string,
  processing_status?: 'enhanced' | 'failed' | 'fallback',
  source_parser?: 'docling' | 'docyolo' | 'enhanced',
  extracted_caption?: string,
  has_caption?: boolean
}
```

```json
{
  "api": "2.0",
  "model": "assembled-v1.0",
  "usage": {"pages": number},
  "elements": [Element],
  "content": {
    "text": "전체 문서 텍스트",
    "markdown": "전체 문서 마크다운", 
    "html": "전체 문서 HTML"
  }
}
```

---

**User**

document_parser는 전체워크플로우의 하나의 노드지만, 하위 워크플로우를 갖고 있어. 현재 분석한 워크플로우를 high level 아키텍쳐라고 한다면, document_parser의 하위 워크플로우까지 풀어낸 detailed아키첵처로 deep dive해서 분석해줘. using sequential thinking

---

**Cursor**

```python
document_parser_graph = create_parser_graph(
    batch_size=batch_size, test_page=test_page, verbose=verbose
)
```

document_parser의 하위 워크플로우를 detailed architecture로 분석하겠습니다.

완전한 **H-DDU-WIN** 프로젝트의 **Detailed Architecture** 분석을 완료했습니다!

## 🏗️ **Complete Detailed Architecture**

### 📊 **High Level vs Detailed Level 비교**

| Level | 설명 | 노드 수 | 복잡도 |
|-------|------|---------|---------|
| **High Level** | 외부에서 보는 메인 워크플로우 | 14개 노드 | 단순 |
| **Detailed Level** | 내부 하위 워크플로우 포함 | 50+ 개 노드 | 복잡 |

---

## 🔍 **Level 0: System Overview**

```mermaid
graph LR
    A[PDF 입력] --> B[H-DDU-WIN 처리 파이프라인]
    B --> C[Multi-Format 출력]
    
    C --> D[JSON 구조화 데이터]
    C --> E[Markdown 문서]
    C --> F[HTML 웹 문서]
    C --> G[LangChain Documents]
    C --> H[Pickle 객체]
```

---

## 🏗️ **Level 1: High Level Architecture (14 Nodes)**

### 🔄 **메인 워크플로우**
```
PDF → document_parser → save_image_node → refine_content_node → add_translation → contextualize_text → create_elements_node → page_elements_extractor → [image_entity_extractor + table_entity_extractor] → merge_entity_node → reconstruct_elements_node → [generate_comprehensive_markdown + langchain_document_node] → save_final_state → 출력물들
```

### 📋 **각 노드 상세 분석**

| 노드 | 입력 | 출력 | 핵심 기능 | 처리 방식 |
|------|------|------|----------|-----------|
| **document_parser** | PDF 파일 | elements_from_parser | DocYOLO+Docling+Assembly | **복잡 하위 워크플로우** |
| **save_image_node** | elements_from_parser | image_paths | base64→파일 저장 | 순차 처리 |
| **refine_content_node** | elements+image_paths | 정제된 elements | LLM 텍스트 정제 | 배치 처리 |
| **add_translation** | elements | 번역된 elements | 양방향 번역 | 자동 언어감지 |
| **contextualize_text** | elements | 문맥화된 elements | 이미지 기반 문맥화 | 배치 처리 |
| **create_elements_node** | elements | 구조화된 elements | 메타데이터 추가 | 구조화 |
| **page_elements_extractor** | elements | 페이지별 분류 | 텍스트/이미지/테이블 분류 | 페이지별 |
| **image_entity_extractor** | images_by_page | 향상된 image entities | LLM 이미지 분석 | **병렬 처리** |
| **table_entity_extractor** | tables_by_page | 향상된 table entities | LLM 테이블 분석 | **병렬 처리** |
| **merge_entity_node** | 추출된 entities | 병합된 entities | 엔티티 통합 | 병합 |
| **reconstruct_elements_node** | merged entities | 재구성된 elements | 요소 재구성 | 재구성 |
| **generate_comprehensive_markdown** | elements | markdown 파일 | 마크다운 생성 | **병렬 처리** |
| **langchain_document_node** | elements | LangChain docs | RAG용 문서 생성 | **병렬 처리** |
| **save_final_state** | 모든 데이터 | 최종 파일들 | 상태 저장 | 직렬화 |

---

## 🔧 **Level 2: Document Parser Detailed (5 Nodes)**

### 🔄 **Parser 워크플로우**
```mermaid
graph TD
    A[SplitPDFFilesNode] --> B[WorkingQueueNode]
    B -->|continue_parse=True| C[DocumentParseNode]
    B -->|continue_parse=False| D[PostDocumentParseNode]
    C --> B
    D --> E[SaveStateNode]
```

### 📋 **Parser 노드 분석**

| 노드 | 역할 | 입력 | 출력 |
|------|------|------|------|
| **SplitPDFFilesNode** | PDF 분할 | PDF 파일 | 분할된 파일 목록 |
| **WorkingQueueNode** | 작업 큐 관리 | 파일 목록 | 현재 작업 파일 |
| **DocumentParseNode** | **메인 파싱** | PDF 파일 | 파싱 결과 |
| **PostDocumentParseNode** | 후처리 | 파싱 결과 | ID 재할당, 메타데이터 |
| **SaveStateNode** | 상태 저장 | 전체 상태 | JSON 파일 |

---

## ⚡ **Level 3: DocumentParseNode Internal (3 Phases)**

### 🔄 **3단계 파싱 프로세스**

```mermaid
graph TD
    A[PDF 입력] --> B[Phase 1: DocYOLO 분석]
    A --> C[Phase 2: Docling 분석]
    B --> D[*_docyolo.json]
    C --> E[*_docling.json]
    D --> F[Phase 3: Assembly 시스템]
    E --> F
    F --> G[*_assembled.json]
```

### 📊 **각 Phase 상세**

#### **Phase 1: DocYOLO 분석**
- **엔진**: magic_pdf 라이브러리
- **강점**: 텍스트 추출
- **프로세스**: PDF Bytes → PymuDocDataset → doc_analyze → content_list → JSON

#### **Phase 2: Docling 분석**
- **엔진**: docling 라이브러리  
- **강점**: 구조화 파싱
- **프로세스**: PDF → DocumentConverter → 페이지 이미지 → 요소 추출 → JSON

#### **Phase 3: Assembly 시스템** ⭐
- **엔진**: DocumentAssembler (LLM 기반)
- **강점**: 두 파서 결과 통합
- **프로세스**: 5단계 통합 워크플로우

---

## 🎯 **Level 4: Assembly System Detailed (5 Steps)**

### 🔄 **Assembly 워크플로우**
```mermaid
graph LR
    A[Prepare] --> B[Classify]
    B --> C[Match]
    C --> D[Merge]
    D --> E[Individual Enhancement]
    E --> F[Post Process]
```

### 📋 **Assembly 단계별 분석**

| 단계 | 기능 | 핵심 기술 | 성과 |
|------|------|----------|------|
| **Prepare** | 데이터 로딩 및 그룹화 | 페이지별 분류 | 정리된 데이터 |
| **Classify** | 요소 분류 | 텍스트/테이블/이미지 분류 | 카테고리별 요소 |
| **Match** | 요소 매칭 | 임베딩 기반 유사도 | 매칭된 요소 쌍 |
| **Merge** | LLM 병합 | GPT-4o-mini 최적화 | 고품질 병합 |
| **Individual Enhancement** | 개별 요소 향상 | 모든 요소 개별 LLM 처리 | **100% 보존율** |
| **Post Process** | 최종 정리 | 중복 제거, 검증 | 완성된 결과 |

---

## 🚀 **핵심 기술적 혁신**

### 1. **🎯 Multi-Parser Strategy**
```
DocYOLO (텍스트 강함) + Docling (구조 강함) = 완벽한 조합
```

### 2. **⚡ Performance Optimization**
- **2개 병렬 구간**: 추출 단계, 생성 단계
- **배치 처리**: LLM 호출 최적화
- **Rate Limiting**: API 제한 관리

### 3. **🧠 LLM Enhancement**
- **Vision Models**: 이미지/테이블 분석
- **Text Models**: 번역, 문맥화, 정제
- **Structured Output**: Pydantic 기반

### 4. **📊 Information Preservation**
| 항목 | 기존 | **개선 후** |
|------|------|-------------|
| 이미지 보존율 | 28% (4/14) | **100% (14/14)** |
| Caption 처리 | 부분 손실 | **완전 보존** |
| 테이블 품질 | rowspan 누락 | **완전 구조** |
| 처리 방식 | 순차 처리 | **병렬 처리** |

---

## 📤 **Output Schema & File Types**

### 🗂️ **최종 출력 파일들**
```
intermediate/
├── *_docyolo.json          # DocYOLO 원시 결과
├── *_docling.json          # Docling 원시 결과  
├── *_assembled.json        # Assembly 통합 결과
├── *_final.json           # 최종 완성 결과
├── *_documents.pkl        # LangChain 문서들
├── *_final_state.json     # 전체 상태 정보
└── *.md                   # 통합 마크다운
```

### 📊 **최종 JSON 스키마**
```json
{
  "api": "2.0",
  "model": "assembled-v1.0", 
  "usage": {"pages": number},
  "elements": [
    {
      "id": number,
      "page": number,
      "category": "paragraph|heading1|table|figure",
      "content": {
        "text": "원문 텍스트",
        "markdown": "마크다운 형식", 
        "html": "HTML 형식"
      },
      "coordinates": [...],
      "base64_encoding": "이미지 데이터",
      "processing_status": "enhanced|failed|fallback",
      "source_parser": "docling|docyolo|enhanced",
      "extracted_caption": "캡션 텍스트",
      "has_caption": boolean,
      "unique_id": "고유 식별자"
    }
  ],
  "content": {
    "text": "전체 문서 텍스트",
    "markdown": "전체 문서 마크다운",
    "html": "전체 문서 HTML"
  }
}
```

---

## 🎉 **Detailed Architecture 완성!**

**✅ 분석 완료 항목:**
- [x] High Level Architecture (14개 노드)
- [x] Document Parser Detailed (5개 노드)  
- [x] DocumentParseNode Internal (3개 Phase)
- [x] Assembly System Detailed (5개 단계)
- [x] 각 노드별 입력/출력/기능
- [x] 데이터 플로우 및 스키마
- [x] 핵심 기술적 특징
- [x] 성능 지표 및 개선사항

이제 이 **Detailed Architecture**를 바탕으로 어떤 방향의 PRD 작성을 원하시는지 알려주세요! 🚀

```plaintext
graph LR
    A[PDF 입력] --> B[H-DDU-WIN 처리 파이프라인]
    B --> C[Multi-Format 출력]
    
    C --> D[JSON 구조화 데이터]
    C --> E[Markdown 문서]
    C --> F[HTML 웹 문서]
    C --> G[LangChain Documents]
    C --> H[Pickle 객체]
```

```plaintext
PDF → document_parser → save_image_node → refine_content_node → add_translation → contextualize_text → create_elements_node → page_elements_extractor → [image_entity_extractor + table_entity_extractor] → merge_entity_node → reconstruct_elements_node → [generate_comprehensive_markdown + langchain_document_node] → save_final_state → 출력물들
```

```plaintext
graph TD
    A[SplitPDFFilesNode] --> B[WorkingQueueNode]
    B -->|continue_parse=True| C[DocumentParseNode]
    B -->|continue_parse=False| D[PostDocumentParseNode]
    C --> B
    D --> E[SaveStateNode]
```

```plaintext
graph TD
    A[PDF 입력] --> B[Phase 1: DocYOLO 분석]
    A --> C[Phase 2: Docling 분석]
    B --> D[*_docyolo.json]
    C --> E[*_docling.json]
    D --> F[Phase 3: Assembly 시스템]
    E --> F
    F --> G[*_assembled.json]
```

```plaintext
graph LR
    A[Prepare] --> B[Classify]
    B --> C[Match]
    C --> D[Merge]
    D --> E[Individual Enhancement]
    E --> F[Post Process]
```

```plaintext
DocYOLO (텍스트 강함) + Docling (구조 강함) = 완벽한 조합
```

```plaintext
intermediate/
├── *_docyolo.json          # DocYOLO 원시 결과
├── *_docling.json          # Docling 원시 결과  
├── *_assembled.json        # Assembly 통합 결과
├── *_final.json           # 최종 완성 결과
├── *_documents.pkl        # LangChain 문서들
├── *_final_state.json     # 전체 상태 정보
└── *.md                   # 통합 마크다운
```

```json
{
  "api": "2.0",
  "model": "assembled-v1.0", 
  "usage": {"pages": number},
  "elements": [
    {
      "id": number,
      "page": number,
      "category": "paragraph|heading1|table|figure",
      "content": {
        "text": "원문 텍스트",
        "markdown": "마크다운 형식", 
        "html": "HTML 형식"
      },
      "coordinates": [...],
      "base64_encoding": "이미지 데이터",
      "processing_status": "enhanced|failed|fallback",
      "source_parser": "docling|docyolo|enhanced",
      "extracted_caption": "캡션 텍스트",
      "has_caption": boolean,
      "unique_id": "고유 식별자"
    }
  ],
  "content": {
    "text": "전체 문서 텍스트",
    "markdown": "전체 문서 마크다운",
    "html": "전체 문서 HTML"
  }
}
```

---

**User**

보완할 부분이 있어.
1.멀티 포맷 출력에서 [HTML 웹 문서]은 옵션(export.py) 이고 LangChain Documents와 Pickle 객체]는 같은 것이야.
 2.aseembly engine이 document parser에 핵심엔진이야. deep dive해서 더 정확하게 파악해봐
using sequential thinking

---

**Cursor**

보완사항을 반영하여 Assembly engine을 deep dive로 정확히 분석하겠습니다.

보완사항을 반영하여 **H-DDU-WIN** 프로젝트의 **Complete Detailed Architecture**를 제공합니다!

## 🔧 **보완사항 반영**

### 1. **멀티 포맷 출력 수정**
- **HTML 웹 문서**: `export.py`의 옵션 기능 (메인 워크플로우 외부)
- **LangChain Documents**: `pickle` 객체로 저장 (같은 것)

### 2. **Assembly Engine Deep Dive 완료**
- **Document Parser의 핵심 엔진**으로 3단계 처리
- **100% 요소 보존** 시스템 구현
- **개별 요소 처리** 로직 (14개 이미지 모두 처리)

---

## 🏗️ **Complete Detailed Architecture**

### 📊 **Level 0: System Overview**

```mermaid
graph LR
    A[PDF 입력] --> B[H-DDU-WIN 처리 파이프라인]
    B --> C[Multi-Format 출력]
    
    C --> D[JSON 구조화 데이터]
    C --> E[Markdown 문서]
    C --> F[LangChain Documents<br/>pickle 저장]
    
    G[HTML 웹 문서] -.-> H[export.py 옵션]
    
    style G fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style H fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
```

---

### 🔄 **Level 1: High Level Architecture (14 Nodes)**

```mermaid
graph TD
    A[PDF 입력] --> B[document_parser]
    B --> C[save_image_node]
    C --> D[refine_content_node]
    D --> E[add_translation]
    E --> F[contextualize_text]
    F --> G[create_elements_node]
    G --> H[page_elements_extractor]
    
    H --> I[image_entity_extractor]
    H --> J[table_entity_extractor]
    
    I --> K[merge_entity_node]
    J --> K
    
    K --> L[reconstruct_elements_node]
    
    L --> M[generate_comprehensive_markdown]
    L --> N[langchain_document_node]
    
    M --> O[save_final_state]
    N --> O
    
    O --> P[Multi-Format 출력]
    
    classDef parser fill:#e1f5fe,stroke:#0277bd,stroke-width:3px
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef extract fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef output fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    
    class B parser
    class C,D,E,F,G,H,K,L process
    class I,J extract
    class M,N,O,P output
```

---

### 🎯 **Level 2: Document Parser (5 Nodes + Assembly)**

```mermaid
graph TD
    A[PDF 입력] --> B[SplitPDFFilesNode]
    B --> C[WorkingQueueNode]
    C --> D[DocumentParseNode]
    D --> E[PostDocumentParseNode]
    E --> F[SaveStateNode]
    
    C -.-> G{continue_parse?}
    G -->|Yes| C
    G -->|No| F
    
    D --> H[Assembly Engine]
    H --> I[DocYOLO Analysis]
    H --> J[Docling Analysis]
    H --> K[Assembly System]
    
    classDef main fill:#e1f5fe,stroke:#0277bd,stroke-width:3px
    classDef assembly fill:#ffebee,stroke:#c62828,stroke-width:3px
    classDef parser fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    
    class B,C,D,E,F main
    class H,K assembly
    class I,J parser
```

---

### 🔧 **Level 3: DocumentParseNode (3 Phases)**

```mermaid
graph TD
    A[PDF 입력] --> B[Phase 1: DocYOLO Analysis]
    B --> C[Phase 2: Docling Analysis]
    C --> D[Phase 3: Assembly System]
    
    B --> E[magic_pdf<br/>PymuDocDataset<br/>doc_analyze<br/>content_list + middle_json<br/>*_docyolo.json]
    
    C --> F[DocumentConverter<br/>PdfPipelineOptions<br/>페이지별 이미지 저장<br/>테이블/그림 수집<br/>*_docling.json]
    
    D --> G[DocumentAssembler<br/>매칭 → 병합 → 향상<br/>*_assembled.json]
    
    classDef phase fill:#e1f5fe,stroke:#0277bd,stroke-width:3px
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class B,C,D phase
    class E,F,G process
```

---

### ⚡ **Level 4: Assembly Engine (5 Stages) - 핵심 엔진**

```mermaid
graph TD
    A[docling.json + docyolo.json] --> B[Stage 1: 데이터 준비]
    B --> C[Stage 2: 요소 분류]
    C --> D[Stage 3: 매칭 시스템]
    D --> E[Stage 4: 병합 엔진]
    E --> F[Stage 5: 후처리]
    
    B --> G[페이지별 그룹화<br/>이미지 경로 확인<br/>base64 데이터 검증]
    
    C --> H[텍스트 요소 분류<br/>테이블 요소 분류<br/>이미지 요소 분류]
    
    D --> I[임베딩 기반 매칭<br/>코사인 유사도 계산<br/>매칭 임계값 적용]
    
    E --> J[LLM 기반 병합<br/>비전 모델 활용<br/>구조화된 출력]
    
    F --> K[중복 제거<br/>품질 검증<br/>최종 구조화]
    
    classDef stage fill:#ffebee,stroke:#c62828,stroke-width:3px
    classDef detail fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class B,C,D,E,F stage
    class G,H,I,J,K detail
```

---

### 🎨 **Level 5: Individual Processing (★ 핵심 개선)**

```mermaid
graph TD
    A[Assembly Engine] --> B[텍스트 처리]
    A --> C[비주얼 요소 개별 처리]
    
    B --> D[매칭 페어 병합<br/>docling-only 검증<br/>docyolo-only 검증<br/>LLM 구조화 출력]
    
    C --> E[개별 이미지 처리]
    C --> F[개별 테이블 처리]
    
    E --> G[14개 이미지 → 14개 모두 처리<br/>Caption 보존<br/>base64 보존<br/>병렬 처리]
    
    F --> H[테이블 클러스터링<br/>다단계 프롬프트<br/>HTML → Markdown 변환<br/>구조화된 출력]
    
    G --> I[100% 요소 보존]
    H --> I
    D --> I
    
    classDef core fill:#ffebee,stroke:#c62828,stroke-width:3px
    classDef process fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef result fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    
    class A,C core
    class B,D,E,F,G,H process
    class I result
```

---

## 🚀 **Assembly Engine 핵심 개선사항**

### 1. **100% 요소 보존 시스템**
- **기존**: 매칭 실패 시 70% 손실
- **개선**: 매칭 실패 요소도 개별 처리로 100% 보존
- **방법**: `_process_all_visual_elements_individually` 메서드

### 2. **개별 요소 처리 로직**
- **기존**: 14개 이미지 중 4개만 처리
- **개선**: 14개 이미지 모두 개별 LLM 처리
- **방법**: `_process_images_individually` 메서드

### 3. **Caption 처리 통합**
- **Docling**: 독립적 caption 요소 처리
- **DocYOLO**: `content.caption` attribute 추출
- **통합**: LLM 프롬프트에 caption 컨텍스트 포함

### 4. **고도화된 테이블 처리**
- **클러스터링**: Y좌표 기준 테이블 조각 그룹화
- **다단계 프롬프트**: HTML 생성 → Markdown 변환
- **컨텍스트 분석**: 주변 텍스트 요소 포함

### 5. **병렬 처리 최적화**
- **Rate Limiting**: API 호출 제한 관리
- **배치 처리**: 다중 요청 병렬 실행
- **재시도 로직**: 실패 시 지수 백오프

---

## 📋 **데이터 스키마 (수정)**

### **최종 출력 스키마**
```json
{
  "api": "2.0",
  "model": "assembled-v1.0",
  "elements": [
    {
      "processing_status": "enhanced|failed|fallback",
      "source_parser": "docling|docyolo|enhanced",
      "extracted_caption": "string",
      "has_caption": "boolean",
      "base64_encoding": "string",
      "content": {
        "text": "string",
        "markdown": "string", 
        "html": "string"
      }
    }
  ]
}
```

### **출력 파일 형식**
- `*_assembled.json`: 최종 통합 결과
- `*_documents.pkl`: LangChain Documents (pickle)
- `*_final_state.json`: 전체 상태 정보
- `*.md`: Markdown 문서
- `*.html`: HTML 문서 (옵션 - export.py)

---

이제 **H-DDU-WIN** 프로젝트의 완전한 **Detailed Architecture**가 파악되었습니다. Assembly Engine이 Document Parser의 핵심 엔진으로서 어떻게 작동하는지 5단계 레벨까지 상세히 분석했습니다! 🎯

```plaintext
graph LR
    A[PDF 입력] --> B[H-DDU-WIN 처리 파이프라인]
    B --> C[Multi-Format 출력]
    
    C --> D[JSON 구조화 데이터]
    C --> E[Markdown 문서]
    C --> F[LangChain Documents<br/>pickle 저장]
    
    G[HTML 웹 문서] -.-> H[export.py 옵션]
    
    style G fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style H fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
```

```plaintext
graph TD
    A[PDF 입력] --> B[document_parser]
    B --> C[save_image_node]
    C --> D[refine_content_node]
    D --> E[add_translation]
    E --> F[contextualize_text]
    F --> G[create_elements_node]
    G --> H[page_elements_extractor]
    
    H --> I[image_entity_extractor]
    H --> J[table_entity_extractor]
    
    I --> K[merge_entity_node]
    J --> K
    
    K --> L[reconstruct_elements_node]
    
    L --> M[generate_comprehensive_markdown]
    L --> N[langchain_document_node]
    
    M --> O[save_final_state]
    N --> O
    
    O --> P[Multi-Format 출력]
    
    classDef parser fill:#e1f5fe,stroke:#0277bd,stroke-width:3px
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef extract fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef output fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    
    class B parser
    class C,D,E,F,G,H,K,L process
    class I,J extract
    class M,N,O,P output
```

```plaintext
graph TD
    A[PDF 입력] --> B[SplitPDFFilesNode]
    B --> C[WorkingQueueNode]
    C --> D[DocumentParseNode]
    D --> E[PostDocumentParseNode]
    E --> F[SaveStateNode]
    
    C -.-> G{continue_parse?}
    G -->|Yes| C
    G -->|No| F
    
    D --> H[Assembly Engine]
    H --> I[DocYOLO Analysis]
    H --> J[Docling Analysis]
    H --> K[Assembly System]
    
    classDef main fill:#e1f5fe,stroke:#0277bd,stroke-width:3px
    classDef assembly fill:#ffebee,stroke:#c62828,stroke-width:3px
    classDef parser fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    
    class B,C,D,E,F main
    class H,K assembly
    class I,J parser
```

```plaintext
graph TD
    A[PDF 입력] --> B[Phase 1: DocYOLO Analysis]
    B --> C[Phase 2: Docling Analysis]
    C --> D[Phase 3: Assembly System]
    
    B --> E[magic_pdf<br/>PymuDocDataset<br/>doc_analyze<br/>content_list + middle_json<br/>*_docyolo.json]
    
    C --> F[DocumentConverter<br/>PdfPipelineOptions<br/>페이지별 이미지 저장<br/>테이블/그림 수집<br/>*_docling.json]
    
    D --> G[DocumentAssembler<br/>매칭 → 병합 → 향상<br/>*_assembled.json]
    
    classDef phase fill:#e1f5fe,stroke:#0277bd,stroke-width:3px
    classDef process fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class B,C,D phase
    class E,F,G process
```

```plaintext
graph TD
    A[docling.json + docyolo.json] --> B[Stage 1: 데이터 준비]
    B --> C[Stage 2: 요소 분류]
    C --> D[Stage 3: 매칭 시스템]
    D --> E[Stage 4: 병합 엔진]
    E --> F[Stage 5: 후처리]
    
    B --> G[페이지별 그룹화<br/>이미지 경로 확인<br/>base64 데이터 검증]
    
    C --> H[텍스트 요소 분류<br/>테이블 요소 분류<br/>이미지 요소 분류]
    
    D --> I[임베딩 기반 매칭<br/>코사인 유사도 계산<br/>매칭 임계값 적용]
    
    E --> J[LLM 기반 병합<br/>비전 모델 활용<br/>구조화된 출력]
    
    F --> K[중복 제거<br/>품질 검증<br/>최종 구조화]
    
    classDef stage fill:#ffebee,stroke:#c62828,stroke-width:3px
    classDef detail fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class B,C,D,E,F stage
    class G,H,I,J,K detail
```

```plaintext
graph TD
    A[Assembly Engine] --> B[텍스트 처리]
    A --> C[비주얼 요소 개별 처리]
    
    B --> D[매칭 페어 병합<br/>docling-only 검증<br/>docyolo-only 검증<br/>LLM 구조화 출력]
    
    C --> E[개별 이미지 처리]
    C --> F[개별 테이블 처리]
    
    E --> G[14개 이미지 → 14개 모두 처리<br/>Caption 보존<br/>base64 보존<br/>병렬 처리]
    
    F --> H[테이블 클러스터링<br/>다단계 프롬프트<br/>HTML → Markdown 변환<br/>구조화된 출력]
    
    G --> I[100% 요소 보존]
    H --> I
    D --> I
    
    classDef core fill:#ffebee,stroke:#c62828,stroke-width:3px
    classDef process fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef result fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    
    class A,C core
    class B,D,E,F,G,H process
    class I result
```

```json
{
  "api": "2.0",
  "model": "assembled-v1.0",
  "elements": [
    {
      "processing_status": "enhanced|failed|fallback",
      "source_parser": "docling|docyolo|enhanced",
      "extracted_caption": "string",
      "has_caption": "boolean",
      "base64_encoding": "string",
      "content": {
        "text": "string",
        "markdown": "string", 
        "html": "string"
      }
    }
  ]
}
```

---

**User**

좋아. PRD를 구성할 세부 목차에 대해 설계해서 알려줘. using sequential thinking

---

**Cursor**

PRD 구성을 위한 세부 목차를 체계적으로 설계하겠습니다.

H-DDU-WIN 프로젝트를 위한 **완전한 PRD 목차**를 설계했습니다!

## 📋 **H-DDU-WIN PRD 목차**

### **I. Executive Summary (경영진 요약)**
- 1.1. 프로젝트 개요
- 1.2. 핵심 가치 제안
- 1.3. 주요 성과 지표
- 1.4. 예상 비즈니스 임팩트
- 1.5. 투자 요구사항 및 ROI

### **II. Market Analysis & Problem Statement (시장 분석 & 문제 정의)**
- 2.1. 시장 현황 분석
- 2.2. 기존 솔루션의 한계
- 2.3. 타겟 고객 세그먼트
- 2.4. 페인 포인트 분석
- 2.5. 시장 기회 및 잠재 규모

### **III. Solution Overview (솔루션 개요)**
- 3.1. 핵심 솔루션 컨셉
- 3.2. 차별화 요소
- 3.3. 경쟁 우위
- 3.4. 기술적 혁신 포인트
- 3.5. 고객 가치 창출 방안

### **IV. Technical Architecture (기술 아키텍처) ⭐**
- 4.1. **System Overview**
  - 4.1.1. 전체 시스템 구조
  - 4.1.2. 핵심 컴포넌트 관계도
  - 4.1.3. 데이터 플로우 개요
- 4.2. **Multi-Parser Architecture**
  - 4.2.1. DocYOLO Parser 특성
  - 4.2.2. Docling Parser 특성
  - 4.2.3. Parser Comparison & Synergy
- 4.3. **Assembly Engine Deep Dive**
  - 4.3.1. Core Assembly Workflow
  - 4.3.2. Matching Algorithm (임베딩 기반)
  - 4.3.3. Merging Engine (LLM 기반)
  - 4.3.4. Individual Processing System (100% 보존)
- 4.4. **LLM Integration**
  - 4.4.1. Multi-Model Support (Azure/OpenAI/Ollama)
  - 4.4.2. Rate Limiting & Optimization
  - 4.4.3. Prompt Engineering
- 4.5. **Data Flow & Processing Pipeline**
  - 4.5.1. 5-Level Architecture 상세
  - 4.5.2. 병렬 처리 최적화
  - 4.5.3. 예외 처리 및 Fallback
- 4.6. **Performance Optimization**
  - 4.6.1. 비동기 처리 시스템
  - 4.6.2. 메모리 관리 전략
  - 4.6.3. 배치 처리 최적화

### **V. Feature Specifications (기능 명세)**
- 5.1. **Core Features**
  - 5.1.1. PDF Document Parsing
  - 5.1.2. Multi-Format Output
  - 5.1.3. Information Preservation (100%)
- 5.2. **Advanced Features**
  - 5.2.1. Caption Processing Integration
  - 5.2.2. Table Enhancement System
  - 5.2.3. Image Analysis & Enhancement
  - 5.2.4. Multi-Language Support (한국어/영어)
- 5.3. **Input/Output Specifications**
  - 5.3.1. 지원 입력 형식
  - 5.3.2. 출력 형식 (JSON/Markdown/Pickle)
  - 5.3.3. 품질 보증 메커니즘
- 5.4. **Configuration Options**
  - 5.4.1. 모델 설정 옵션
  - 5.4.2. 성능 튜닝 파라미터
  - 5.4.3. 사용자 정의 설정

### **VI. Data Schema & Formats (데이터 스키마 & 형식)**
- 6.1. **Input Schema**
  - 6.1.1. PDF 입력 요구사항
  - 6.1.2. 메타데이터 구조
- 6.2. **Intermediate Schema**
  - 6.2.1. Parser 출력 스키마
  - 6.2.2. Assembly 중간 결과
- 6.3. **Output Schema**
  - 6.3.1. 최종 JSON 구조
  - 6.3.2. Element 스키마 정의
  - 6.3.3. Content 형식 명세
- 6.4. **Version Control & Compatibility**

### **VII. Performance Requirements (성능 요구사항)**
- 7.1. **처리 성능 목표**
  - 7.1.1. 처리 속도 (페이지/시간)
  - 7.1.2. 메모리 사용량
  - 7.1.3. CPU 사용률
- 7.2. **품질 성능 목표**
  - 7.2.1. 정보 보존율 (100%)
  - 7.2.2. 정확도 메트릭
  - 7.2.3. 에러율 허용 범위
- 7.3. **확장성 요구사항**
  - 7.3.1. 동시 처리 능력
  - 7.3.2. 대용량 문서 처리
  - 7.3.3. 클라우드 확장성

### **VIII. API & Integration (API & 통합)**
- 8.1. **REST API 명세**
  - 8.1.1. 문서 업로드 API
  - 8.1.2. 처리 상태 조회 API
  - 8.1.3. 결과 다운로드 API
- 8.2. **SDK & Libraries**
  - 8.2.1. Python SDK
  - 8.2.2. JavaScript SDK
  - 8.2.3. 기타 언어 지원
- 8.3. **Third-party Integration**
  - 8.3.1. Cloud Storage 연동
  - 8.3.2. Database 연동
  - 8.3.3. Webhook 지원

### **IX. User Stories & Use Cases (사용자 시나리오)**
- 9.1. **기업 사용자 시나리오**
  - 9.1.1. 대량 문서 디지털화
  - 9.1.2. 컴플라이언스 문서 처리
  - 9.1.3. 보고서 자동화
- 9.2. **연구기관 시나리오**
  - 9.2.1. 논문 구조화
  - 9.2.2. 데이터 추출 및 분석
- 9.3. **개발자 시나리오**
  - 9.3.1. RAG 시스템 구축
  - 9.3.2. 문서 검색 시스템
  - 9.3.3. 지식 베이스 구축

### **X. Quality Assurance & Testing (품질 보증 & 테스팅)**
- 10.1. **테스트 전략**
  - 10.1.1. 단위 테스트
  - 10.1.2. 통합 테스트
  - 10.1.3. 성능 테스트
- 10.2. **품질 메트릭**
  - 10.2.1. 정확도 측정
  - 10.2.2. 완전성 측정
  - 10.2.3. 일관성 측정
- 10.3. **테스트 데이터셋**
  - 10.3.1. 벤치마크 데이터
  - 10.3.2. 다양한 문서 유형
  - 10.3.3. 엣지 케이스

### **XI. Implementation Plan (구현 계획)**
- 11.1. **개발 로드맵**
  - 11.1.1. Phase 1: Core System
  - 11.1.2. Phase 2: Advanced Features
  - 11.1.3. Phase 3: Optimization
- 11.2. **마일스톤 & 타임라인**
- 11.3. **리소스 요구사항**
- 11.4. **의존성 관리**

### **XII. Deployment & Operations (배포 & 운영)**
- 12.1. **배포 전략**
  - 12.1.1. 온프레미스 배포
  - 12.1.2. 클라우드 배포
  - 12.1.3. 하이브리드 배포
- 12.2. **운영 요구사항**
  - 12.2.1. 모니터링 & 로깅
  - 12.2.2. 백업 & 복구
  - 12.2.3. 업데이트 관리
- 12.3. **인프라 요구사항**
  - 12.3.1. 하드웨어 사양
  - 12.3.2. 네트워크 요구사항
  - 12.3.3. 보안 요구사항

### **XIII. Security & Privacy (보안 & 개인정보)**
- 13.1. **보안 요구사항**
  - 13.1.1. 데이터 암호화
  - 13.1.2. 접근 제어
  - 13.1.3. 감사 로깅
- 13.2. **개인정보 보호**
  - 13.2.1. GDPR 준수
  - 13.2.2. 데이터 익명화
  - 13.2.3. 정보 보존 정책
- 13.3. **컴플라이언스**
  - 13.3.1. 산업 표준 준수
  - 13.3.2. 인증 요구사항

### **XIV. Cost Analysis (비용 분석)**
- 14.1. **개발 비용**
  - 14.1.1. 인력 비용
  - 14.1.2. 인프라 비용
  - 14.1.3. 라이센스 비용
- 14.2. **운영 비용**
  - 14.2.1. LLM API 비용
  - 14.2.2. 클라우드 비용
  - 14.2.3. 유지보수 비용
- 14.3. **TCO (Total Cost of Ownership)**
- 14.4. **비용 최적화 방안**

### **XV. Risk Assessment (위험 평가)**
- 15.1. **기술적 위험**
  - 15.1.1. LLM 의존성 위험
  - 15.1.2. 성능 저하 위험
  - 15.1.3. 품질 보증 위험
- 15.2. **비즈니스 위험**
  - 15.2.1. 시장 변화 위험
  - 15.2.2. 경쟁 위험
  - 15.2.3. 규제 변화 위험
- 15.3. **완화 전략**
- 15.4. **컨틴전시 플랜**

### **XVI. Success Metrics (성공 지표)**
- 16.1. **기술적 성공 지표**
  - 16.1.1. 정보 보존율 (목표: 100%)
  - 16.1.2. 처리 속도 (목표: X페이지/시간)
  - 16.1.3. 정확도 (목표: XX%)
- 16.2. **비즈니스 성공 지표**
  - 16.2.1. 사용자 만족도
  - 16.2.2. 시장 점유율
  - 16.2.3. 수익 창출
- 16.3. **KPI 모니터링 방안**

### **XVII. Competitive Analysis (경쟁 분석)**
- 17.1. **주요 경쟁사 분석**
- 17.2. **경쟁 우위 요소**
- 17.3. **차별화 전략**
- 17.4. **시장 포지셔닝**

### **XVIII. Future Roadmap (미래 로드맵)**
- 18.1. **단기 로드맵 (6개월)**
- 18.2. **중기 로드맵 (1년)**
- 18.3. **장기 로드맵 (2-3년)**
- 18.4. **기술 발전 대응 계획**

### **XIX. Appendices (부록)**
- 19.1. **기술 용어집**
- 19.2. **참고 문헌**
- 19.3. **상세 다이어그램**
- 19.4. **벤치마크 결과**
- 19.5. **샘플 출력 예시**

---

## 🎯 **PRD 목차 특징**

### **1. 완전성 (Completeness)**
- **19개 주요 섹션**으로 프로젝트 전 영역 커버
- **비즈니스 가치**에서 **기술 구현**까지 포괄
- **계획 수립**에서 **운영 관리**까지 완전 커버

### **2. 기술적 깊이 (Technical Depth)**
- **Section IV (Technical Architecture)**에 가장 많은 비중
- **Assembly Engine** 상세 분석
- **Multi-Parser Architecture** 심층 다루기
- **LLM Integration** 혁신성 강조

### **3. 실용성 (Practicality)**
- **구현 가능한 계획** 중심
- **측정 가능한 성공 지표**
- **위험 관리** 및 **완화 전략**

### **4. 독자 맞춤 (Audience-Specific)**
- **경영진**: Section I-III, XIII-XVI
- **기술팀**: Section IV-VII, X-XII
- **운영팀**: Section VIII, XI-XII
- **고객/파트너**: Section III, V, IX

이 PRD 목차를 바탕으로 H-DDU-WIN 프로젝트의 완전한 제품 요구사항 문서를 작성할 수 있습니다! 🚀

---

**User**

좋아. 시장 분석 & 문제 정의 같은 부분은 필요하다면 검색을 통해서 정보를 보강해서 비지니스와 기술적으로 완벽한 PRD를 작성하고 저장해줘. using sequential thinking


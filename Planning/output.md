물론입니다. 자동차 설비 매뉴얼을 예시로 신입 개발자분들이 더 쉽게 이해할 수 있도록 설명해 드릴게요.

### 신입 개발자를 위한 Parser & Assembly 아웃풋 스키마 가이드 (자동차 매뉴얼 Ver.)

안녕하세요! 우리 팀의 핵심 기술인 DocYOLO, Docling, Assembly가 어떻게 **'자동차 설비 매뉴얼'** 한 페이지를 완벽한 디지털 데이터로 만들어내는지 알려드릴게요.

**핵심 비유: "클래식카 복원 전문가 팀"**

- **DocYOLO**: 차량의 외관과 엔진룸을 '눈으로' 스캔하는 **비주얼 분석가**
- **Docling**: 정비 지침서의 절차를 '순서대로' 읽고 이해하는 **프로세스 분석가**
- **Assembly**: 두 분석가의 보고서를 취합해 최종 정비 계획서를 만드는 **마스터 메카닉**

---

### 1. DocYOLO: 비주얼 분석가 (Visual Layout Parser)

DocYOLO는 매뉴얼 페이지를 사진 찍듯이 전체적으로 봅니다. 텍스트의 의미보다는 **"이 그림은 여기 있고, 이 표는 저기 있네"** 와 같이 시각적 배치와 구성을 파악하는 데 최고입니다.

- **주요 역할**:
  - 엔진 다이어그램(`figure`), 부품 사양표(`table`) 같은 시각적 요소를 하나의 덩어리로 정확하게 찾아냅니다.
  - 텍스트, 이미지, 표의 위치와 크기(`coordinates`)를 정밀하게 측정합니다.
- **아웃풋 특징**:
  - `category`가 `table`, `figure`인 요소들을 매우 잘 식별합니다.
  - 정비 절차처럼 번호가 매겨진 목록도 그냥 하나의 텍스트 덩어리(`paragraph`)로 볼 수 있습니다.

#### 📄 DocYOLO 아웃풋 예시

"엔진 오일 교체" 페이지를 분석한 비주얼 분석가의 보고서입니다.

```json
{
  "api": "2.0",
  "model": "docyolo-v2",
  "elements": [
    {
      "id": 0,
      "page": 1,
      "category": "heading1",
      "content": { "text": "2. 엔진 오일 교체 절차" },
      "coordinates": [ /* ... */ ]
    },
    {
      "id": 1,
      "page": 1,
      "category": "paragraph",
      "content": { "text": "1. 주입구 캡(A)을 엽니다. 2. 드레인 플러그..." }, // 목록을 하나의 문단으로 인식
      "coordinates": [ /* ... */ ]
    },
    {
      "id": 2,
      "page": 1,
      "category": "figure",
      "content": { /* 이미지 관련 데이터 */ },
      "coordinates": [ /* 엔진 다이어그램 영역 */ ],
      "base64_encoding": "iVBORw0KGgoAAA..." // 이미지 데이터
    },
    {
      "id": 3,
      "page": 1,
      "category": "table",
      "content": { "text": "항목 규격 엔진 오일 5W-30..." }, // 표 전체를 하나의 덩어리로 인식
      "coordinates": [ /* 사양표 영역 */ ]
    }
  ]
}
```
> **포인트**: DocYOLO는 엔진 다이어그램(`figure`)과 사양표(`table`)를 완벽하게 찾아냈지만, 정비 순서 목록은 그냥 하나의 문단으로 처리했습니다.

---

### 2. Docling: 프로세스 분석가 (Text Flow Parser)

Docling은 매뉴얼을 처음부터 끝까지 정독하며 **"1번 절차 다음은 2번이지"** 처럼 텍스트의 논리적인 순서와 구조를 파악합니다.

- **주요 역할**:
  - "1, 2, 3..." 이나 글머리 기호(•)로 된 정비 절차(`list`)를 각 단계별로 완벽하게 나눕니다.
  - 문단의 시작과 끝, 경고 문구 등을 논리적으로 분리합니다.
- **아웃풋 특징**:
  - `category`가 `list`와 그 하위 항목, `paragraph`인 요소에 강점을 보입니다.
  - 그림(`figure`)이나 표(`table`)는 구조를 이해하지 못하고, 그 안에 있는 텍스트를 여러 개의 문단으로 쪼개버릴 수 있습니다.

#### 📄 Docling 아웃풋 예시

동일한 페이지를 분석한 프로세스 분석가의 보고서입니다.

```json
{
  "api": "2.0",
  "model": "docling-v1.3",
  "elements": [
    {
      "category": "heading1",
      "content": { "text": "2. 엔진 오일 교체 절차" }
    },
    {
      "category": "list", // 정비 절차를 '목록'으로 정확히 인식!
      "content": { "text": "1. 주입구 캡(A)을 엽니다.\n2. 드레인 플러그(B)를 풀어 오일을 배출합니다." }
    },
    // 표(Table)를 인식 못하고, 각 줄을 별개의 문단으로 처리
    {
      "category": "paragraph",
      "content": { "text": "항목 규격" }
    },
    {
      "category": "paragraph",
      "content": { "text": "엔진 오일 5W-30 합성유" }
    },
    {
      "category": "paragraph",
      "content": { "text": "용량 4.5L" }
    }
  ]
}
```
> **포인트**: Docling은 정비 절차(`list`)를 기가 막히게 분석했지만, 사양표는 그냥 세 줄짜리 일반 텍스트로 잘못 해석했습니다.

---

### 3. Assembly: 마스터 메카닉 (Final Assembled Output)

Assembly는 두 분석가의 보고서를 모두 검토한 후, **각 분야 최고 전문가의 의견을 채택하여 최종 정비 계획서**를 완성합니다.

- **주요 역할**:
  - **장점만 취합**: 정비 절차는 Docling의 `list`를, 엔진 다이어그램과 사양표는 DocYOLO의 `figure`와 `table`을 채택합니다.
  - **최종 결과물 생성**: 선별된 요소들을 올바른 순서로 조립하여 완전한 `html`, `markdown`, `text` 형태의 매뉴얼 데이터를 만듭니다.
- **아웃풋 특징**:
  - **가장 정확하고 완벽한 데이터**를 제공합니다.
  - 각 요소에 `source_parser` 필드가 있어, 이 정보가 누구(DocYOLO or Docling)로부터 왔는지 출처를 명확히 합니다.

#### 📄 Assembly 아웃풋 예시 (최종 정비 계획서)

마스터 메카닉이 완성한 최종 디지털 매뉴얼입니다.

```json
{
  "api": "2.0",
  "model": "assembled-v1.0",
  "content": {
    "html": "<h1>2. 엔진 오일...</h1><ol><li>주입구 캡...</li></ol><img src=...><table border='1'>...</table>",
    "markdown": "# 2. 엔진 오일...\n\n1. 주입구 캡...\n\n![엔진 다이어그램](...)\n\n| 항목 | 규격 |\n|---|---|\n| 엔진 오일 | 5W-30 |",
    "text": "2. 엔진 오일 교체 절차\n1. 주입구 캡(A)을 엽니다..."
  },
  "elements": [
    {
      "id": 0, "page": 1, "category": "heading1", "source_parser": "docling", /* ... */
    },
    {
      "id": 1, "page": 1, "category": "list", "source_parser": "docling", // 정비 절차는 Docling 것 채택!
       /* ... */
    },
    {
      "id": 2, "page": 1, "category": "figure", "source_parser": "docyolo", // 그림은 DocYOLO 것 채택!
      /* ... */
    },
    {
      "id": 3, "page": 1, "category": "table", "source_parser": "docyolo", // 표도 DocYOLO 것 채택!
      /* ... */
    }
  ]
}
```
> **포인트**: Assembly는 각 파서의 장점만을 모아 최종 결과물을 만들었습니다. 이제 이 `elements` 배열과 `content`만 있으면, 웹사이트든 앱이든 어디서나 완벽한 디지털 매뉴얼을 보여줄 수 있습니다.

---

### 요약 정리

| 구분 | DocYOLO (비주얼 분석가) | Docling (프로세스 분석가) | Assembly (마스터 메카닉) |
| :--- | :--- | :--- | :--- |
| **역할** | 페이지의 시각적 요소(그림, 표) 인식 | 텍스트의 논리적 절차(목록, 문단) 분석 | 두 분석가 결과를 조합하여 **최종 데이터 생성** |
| **장점** | `figure`, `table` | `list`, `paragraph` | **가장 정확하고 신뢰도 높은 결과물** |
| **단점** | 텍스트의 논리적 구조를 놓칠 수 있음 | 시각적 구조물을 잘못 해석할 수 있음 | 없음 (최종 산출물) |
| **핵심 필드**| `coordinates`, `base64_encoding` | `category` (list) | `source_parser`, 완성된 `content` |

이처럼 각 시스템은 클래식카의 각기 다른 부분을 전문적으로 진단하고, Assembly는 그 진단 결과를 종합해 완벽한 복원 계획을 세우는 것과 같습니다. 이 흐름을 이해하시면 앞으로 데이터를 다루실 때 큰 도움이 될 겁니다
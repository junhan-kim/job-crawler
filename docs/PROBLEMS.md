# 예상 문제점 및 해결 전략

## 목차

| # | 문제 | 상태 |
|---|------|------|
| 1 | [비용 (Cost)](#1-비용-cost) | 부분 구현 |
| 2 | [레이턴시 (Latency)](#2-레이턴시-latency) | 부분 구현 |
| 3 | [답변 품질 (Quality)](#3-답변-품질-quality) | 부분 구현 |
| 4 | [컨텍스트 관리](#4-컨텍스트-관리) | 미구현 |
| 5 | [동기/비동기 불일치](#5-동기비동기-불일치) | 완료 |
| 6 | [크롤링 데이터 신선도](#6-크롤링-데이터-신선도) | 완료 |
| 7 | [에러 처리 & 복구](#7-에러-처리--복구) | 부분 구현 |
| 8 | [크롤링 안정성](#8-크롤링-안정성) | 완료 |
| 9 | [LLM Provider 호환성](#9-llm-provider-호환성) | 완료 |
| 10 | [상태 관리 복잡도](#10-상태-관리-복잡도) | 완료 |
| 11 | [모호한 입력 처리](#11-모호한-입력-처리) | 미구현 |
| 12 | [검색 결과 없음 처리](#12-검색-결과-없음-처리) | 미구현 |
| 13 | [전체 요청 타임아웃](#13-전체-요청-타임아웃) | 부분 구현 |
| 14 | [동시 요청 시 중복 크롤링](#14-동시-요청-시-중복-크롤링) | 불필요 |

---

## 1. 비용 (Cost)

### 문제점
- LLM API 호출당 비용 발생
- 채용공고 긴 텍스트 → 토큰 소모 큼
- 사용자 많아지면 비용 급증

### 해결 전략

**1. 모델 믹스**
| 작업 | 모델 | 비용 |
|------|------|------|
| 파싱/분류 | Haiku / GPT-4o-mini | $0.8/1M |
| 분석/추론 | Sonnet | $3/1M |
| 단순 추출 | 로컬 LLM (Ollama) | 무료 |

**2. 캐싱 레이어**
- Redis: 동일 쿼리 캐시 (TTL 1시간)
- 임베딩 캐시: 공고별 임베딩 저장
- GPTCache (Post-MVP): 유사 쿼리도 캐시 히트

**3. 토큰 최적화**
- 공고 전문 대신 요약본 전달
- 시스템 프롬프트 압축
- 배치 처리: 공고 10개를 한 번에 분석

**예상 비용**
| 규모 | 비용/월 |
|------|---------|
| 개인 (100회/일) | ~$15 |
| 소규모 (1000회/일) | ~$100 |
| 캐싱 적용 시 | 30-50% 절감 |

---

## 2. 레이턴시 (Latency)

### 문제점
- LLM 응답: 2-10초
- 크롤링: 사이트당 3-10초
- 벡터 검색: 100ms-1s
- 전체 파이프라인: 10-30초 예상

### 해결 전략

**1. 스트리밍 응답 (SSE)**
```python
async def search_stream(request):
    async def event_generator():
        async for chunk in agent.stream(query):
            yield f"data: {chunk}\n\n"
    return StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream'
    )
```

**2. 병렬 크롤링**
```python
asyncio.gather(
    crawl_saramin(),
    crawl_wanted(),
    crawl_jobkorea()
)
# 순차: 15-30초 → 병렬: 5-10초
```

**3. 점진적 응답**
```
Step 1: "검색 중..." (즉시)
Step 2: "3개 사이트에서 15개 공고 발견" (3초)
Step 3: "분석 중..." (5초)
Step 4: "추천 공고 5개입니다" (10초)
```

**4. 백그라운드 프리페칭**
- Celery Beat: 인기 검색어 매 시간 갱신
- 캐시 히트 시 즉시 응답

---

## 3. 답변 품질 (Quality)

### 문제점
- 할루시네이션: 없는 정보 생성
- 부정확한 매칭: 조건과 안 맞는 공고 추천
- 일관성 부족: 같은 질문에 다른 답변
- 한국어 처리: 직무명, 스킬명 파싱 오류

### 해결 전략

**1. 할루시네이션 방지**
- RAG 기반: 실제 크롤링된 데이터만 사용
- 출처 명시 강제 (프롬프트)
- Pydantic 스키마 검증

**2. 다단계 필터링**
```
Step 1: 벡터 유사도로 후보군 추출 (Top 50)
Step 2: 규칙 기반 필터 (경력, 연봉, 지역)
Step 3: LLM 리랭킹 (적합도 점수)
Step 4: 최종 Top 10 반환
```

**3. 일관성 확보**
- Temperature = 0 (결정적 응답)
- Few-shot 예시로 출력 포맷 고정

**4. 한국어 동의어 사전**
```python
SYNONYMS = {
    "백엔드": ["서버 개발자", "BE", "Backend"],
    "React": ["리액트", "ReactJS"],
}
```

---

## 4. 컨텍스트 관리

### 문제점
- 채용공고 10개 × 2000자 = 20,000자 (약 6,000 토큰)
- 대화 히스토리 누적 → 컨텍스트 폭발
- 긴 컨텍스트 = 높은 비용 + 느린 응답 + 품질 저하

### 해결 전략

**1. 청킹 전략**
```
채용공고 구조화 청킹:
├── 제목 + 회사명: 별도 저장
├── 자격요건: 청크 1
├── 우대사항: 청크 2
├── 복리후생: 청크 3
└── 각 청크 200-500 토큰
```

**2. 컨텍스트 압축**
```
원본 (2000자) → LLM 요약 (Haiku) → 요약본 (300자)

요약본:
- 회사: OO테크
- 포지션: 백엔드 개발자
- 필수: Python, Django, 3년+
- 연봉: 5000-7000만
- 특이사항: 스톡옵션, 재택근무
```

**3. 컨텍스트 버짓**
```
총 컨텍스트 예산: 8,000 토큰
├── System Prompt: 500 토큰 (고정)
├── 대화 히스토리: 1,500 토큰 (가변)
├── 검색 결과: 5,000 토큰 (가변)
└── 응답 여유: 1,000 토큰

초과 시 → 오래된 것부터 제거/요약
```

---

## 5. 동기/비동기 불일치

### 문제점
```
Django (기본 동기) ←→ LangGraph (비동기) ←→ Celery (비동기)
```

### 해결 전략

**Django ASGI + Async View**
```python
# Django 5.x async view
async def search_jobs(request):
    agent = JobSearchAgent()
    result = await agent.run(query)
    return JsonResponse(result)
```

**Celery 역할 재정의**
- 실시간 요청: Agent가 직접 처리 (Celery 안 씀)
- 백그라운드 작업: Celery 사용
  - 주기적 크롤링 (Celery Beat)
  - 임베딩 배치 생성
  - 만료된 공고 정리

---

## 6. 크롤링 데이터 신선도

### 문제점
```
1. 사용자가 "Django 백엔드" 검색
2. Agent가 크롤링 → 새 공고 10개 발견
3. RAG 검색 → 벡터 DB에는 새 공고 임베딩 없음!
```

### 해결 전략

**하이브리드 검색**
```
검색 요청
    │
    ├──▶ RAG 검색 (저장된 공고) → 기존 공고 N개
    │
    └──▶ 실시간 크롤링 (새 공고) → 새 공고 M개
                │
                ▼
         LLM 통합 분석 (키워드 매칭으로 새 공고 필터링)
```

**백그라운드 임베딩 파이프라인**
```
실시간 요청 ──▶ 응답 반환 (임베딩 없이)
     │
     └──▶ 비동기로 임베딩 생성 (Celery)
               │
               ▼
          다음 검색부터 RAG에서 검색 가능
```

---

## 7. 에러 처리 & 복구

### 문제점
```
├── 크롤링 실패: 사이트 차단, 구조 변경, 타임아웃
├── LLM 실패: API 오류, Rate limit
├── 파싱 실패: 예상치 못한 응답 포맷
└── 부분 실패: 3개 사이트 중 1개만 성공
```

### 해결 전략

**계층별 재시도 정책**
| 계층 | 정책 |
|------|------|
| LLM 호출 | 최대 3회, Exponential backoff (1s→2s→4s), 실패 시 fallback 모델 |
| 크롤링 | 사이트별 독립 실행, 타임아웃 10초, 실패 시 스킵 |
| DB 쿼리 | Connection pool, 쿼리 타임아웃 5초 |

**LangGraph 체크포인팅**
```python
checkpointer = PostgresSaver(conn)
app = workflow.compile(checkpointer=checkpointer)

# 실패 시 마지막 체크포인트부터 재개
app.resume(thread_id, from_checkpoint=True)
```

**Graceful Degradation**
```
시나리오: 3개 사이트 중 사람인만 성공
→ "사람인에서 5개 공고를 찾았습니다.
   (원티드, 잡코리아 일시적 오류)"

시나리오: LLM 분석 실패
→ 크롤링 결과 원본이라도 반환
  "상세 분석 없이 검색 결과만 표시합니다"
```

---

## 8. 크롤링 안정성

### 문제점
```
채용 사이트 방어 메커니즘:
├── Rate Limiting: 너무 빠른 요청 차단
├── CAPTCHA: 봇 탐지 시 캡차 요구
├── IP 차단: 의심스러운 패턴 차단
├── 구조 변경: HTML 구조 수시로 변경
└── 로그인 필요: 일부 정보 로그인 후 접근
```

### 해결 전략

**요청 제어**
- 요청 간격: 2-5초 랜덤 딜레이
- 동시 요청: 사이트당 1개
- 시간당 요청 제한: 사이트당 100회
- User-Agent 로테이션

**HTML 파싱 견고성**
```python
# 여러 셀렉터 폴백
selectors = [
    "div.job-title",      # 현재 구조
    "h2.posting-title",   # 이전 구조
    "[data-job-title]",   # 데이터 속성
]

# 구조 변경 감지 → 알림
if parse_success_rate < 0.5:
    alert("사람인 HTML 구조 변경 감지")
```

**대안: 공식 API**
| 사이트 | API |
|--------|-----|
| 원티드 | 공식 API 있음 (제한적) |
| 사람인 | 파트너 API (신청 필요) |
| 잡코리아 | API 없음 (크롤링만) |

---

## 9. LLM Provider 호환성

### 문제점
```
Ollama (개발) → Claude (프로덕션) 전환 시:
├── 응답 포맷 차이
├── 토큰 제한 차이 (8K vs 200K)
├── 기능 차이 (Tool calling)
└── 한국어 성능 차이
```

### 해결 전략

**추상화 레이어** → [TECH_STACK.md](./TECH_STACK.md#llm-provider-추상화-설계) 참조

**응답 정규화**
```python
@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] | None
    usage: TokenUsage
    model: str
    latency_ms: int
```

---

## 10. 상태 관리 복잡도

### 문제점
```
LangGraph State가 복잡해질 수 있음:
├── State가 커지면 체크포인팅 비용 증가
├── 디버깅 어려움
├── 노드 간 의존성 복잡
└── 테스트 어려움
```

### 해결 전략

**State 분리**
```python
# 핵심 State (체크포인팅 대상)
class CoreState(TypedDict):
    user_query: str
    conditions: ParsedConditions
    final_results: list[JobResult]
    current_step: str

# 임시 State (체크포인팅 제외)
class TempState(TypedDict):
    raw_crawl_data: list[dict]  # 큼, 임시
    intermediate_analysis: str   # 임시
```

**불변성 유지**
```python
def crawl_node(state):
    # ❌ state['results'].append(new_data)
    # ✅ return {'results': [...old, new_data]}
    return {'crawl_results': new_results}
```

---

## 11. 모호한 입력 처리

### 문제점
```
├── "개발자 구함" → 어떤 개발자?
├── "좋은 회사" → 기준이 뭔가?
├── "서울 근처" → 경기도 포함?
└── "적당한 연봉" → 얼마가 적당?
```

### 해결 전략

**Parse 노드에서 명확성 검증**
```python
class ParseResult(TypedDict):
    conditions: dict
    confidence: float      # 0.0 ~ 1.0
    ambiguous_fields: list[str]
    clarification_needed: bool

# confidence < 0.7 이면 clarification 요청
```

**Clarification 노드 (조건부)**
```
Parse ──▶ confidence < 0.7? ──▶ Clarify (사용자에게 질문)
                │
                └──▶ Plan Search
```

**구조화된 선택지 제공**
```
입력: "개발자 구함"

응답:
"어떤 개발 직군을 찾으시나요?"
1. 백엔드 개발자
2. 프론트엔드 개발자
3. 풀스택 개발자
4. 데이터 엔지니어
5. DevOps/인프라
```

---

## 12. 검색 결과 없음 처리

### 문제점
```
조건이 너무 까다로움: Python + Go + Rust + 10년차 + 연봉 2억
→ 현재: "검색 결과가 없습니다" 만 반환
```

### 해결 전략

**자동 조건 완화**
```
완화 우선순위:
1. 스킬 조건 완화: 필수 스킬만 유지
2. 경력 조건 완화: ±2년 범위 확대
3. 연봉 조건 완화: 하한선 20% 낮춤
4. 지역 조건 완화: 인접 지역 포함

# 한 번에 하나씩 완화, 최대 3회 재시도
```

**대안 제시**
```
"정확히 일치하는 공고가 없습니다. 대신:"

📌 조건 완화 제안
- "Python + Django" → "Python" 만으로 15건
- "5년 이상" → "3년 이상" 으로 25건

📌 유사 직무 추천
- "백엔드 개발자" 대신 "풀스택 개발자" 8건
```

---

## 13. 전체 요청 타임아웃

### 문제점
```
전체 파이프라인이 과도하게 길어질 수 있음:
├── 크롤링 지연
├── LLM 지연
├── 재시도 누적
└── 무한 루프

최악: 사용자가 60초 이상 대기
```

### 해결 전략

**전역 타임아웃**
```python
GLOBAL_TIMEOUT = 60  # 초

async def search_with_timeout(query):
    try:
        return await asyncio.wait_for(
            agent.run(query),
            timeout=GLOBAL_TIMEOUT
        )
    except asyncio.TimeoutError:
        return partial_results_or_error()
```

**단계별 타임아웃 버짓**
```
전체 60초 분배:
├── Parse:      5초
├── Plan:       5초
├── Crawling:  30초 (병렬)
├── RAG:       10초
└── Synthesis: 10초

각 단계 타임아웃 시 → 다음 단계로 진행 (부분 결과)
```

**부분 결과 반환**
```
타임아웃 발생 시:

시나리오: 크롤링 중 타임아웃
→ "사람인에서 5개 공고를 찾았습니다.
   (원티드, 잡코리아 검색 시간 초과)"

시나리오: 분석 중 타임아웃
→ 크롤링 결과 원본 반환 + 분석 생략 안내
```

---

## 14. 동시 요청 시 중복 크롤링

### 문제점
```
동일 키워드로 동시 요청 시:
├── 요청 A → 크롤링 시작
├── 요청 B → 동일 키워드 크롤링 시작 (중복)
└── 서버 리소스 낭비 + 차단 위험 증가
```

### 분석 결과: 구현 불필요

**기존 시스템이 이미 해결:**
1. **Redis 캐시 (View 단)**: 동일 쿼리 1시간 캐시 → 캐시 히트 시 크롤링 안 함
2. **RAG 검색**: 주기적 크롤링 데이터로 대부분 응답 → 실시간 크롤링 빈도 낮음
3. **Semaphore**: 동시 크롤링 1개 제한 → 어차피 순차 실행

**Singleflight 패턴 검토:**
- Go의 `singleflight` 패턴: 동일 키워드 요청 병합
- Python 구현체 (`singleflight` PyPI): 미성숙 (14 stars, 2022년 이후 미업데이트)
- 직접 구현: asyncio.Lock + Future 조합 가능하나 버그 위험

**결론:** 실제 동일 키워드 동시 요청은 드묾. 기존 캐시 + RAG + Semaphore로 충분.

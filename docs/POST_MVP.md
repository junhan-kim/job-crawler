# Post-MVP TODO

MVP 완성 후 개선할 사항들. 당장 없어도 서비스 동작에 문제없음.

---

## 1. 동시 요청 제어 고도화

### 1-1. 현재 구현 (Phase 2)
세마포어로 동시 요청 1개 제한 + 30초 타임아웃
```python
# crawlers/utils.py
crawler_semaphore = asyncio.Semaphore(1)

# agent/nodes/execute.py
async with asyncio.timeout(30):
    async with crawler_semaphore:
        # 크롤링
```

### 1-2. 고도화 방향

**다중 서버 환경 (Redis 분산 락)**
```python
import redis.asyncio as redis
from redis.asyncio.lock import Lock

redis_client = redis.from_url("redis://localhost")

async def execute_with_distributed_lock():
    lock = Lock(redis_client, "crawler_lock", timeout=60)
    async with lock:
        # 크롤링
```

**브라우저 풀 (재사용)**
```python
class BrowserPool:
    def __init__(self, max_size: int = 3):
        self.pool: asyncio.Queue[Browser] = asyncio.Queue(maxsize=max_size)
        self.semaphore = asyncio.Semaphore(max_size)

    async def acquire(self) -> Browser:
        async with self.semaphore:
            if self.pool.empty():
                return await self._create_browser()
            return await self.pool.get()

    async def release(self, browser: Browser):
        await self.pool.put(browser)
```

**Celery 작업 큐**
```python
@celery_app.task(rate_limit='10/m')
def crawl_task(keyword: str, max_pages: int):
    # 크롤링 수행
    return results
```

**도입 시점**:
- Redis 분산 락: 서버 2대 이상 운영 시
- 브라우저 풀: 동시 사용자 10명 이상 시
- Celery 큐: 비동기 처리 + 재시도 필요 시

---

## 2. 입력 검증 레이어 (Input Validation)

**문제**
- SQL Injection 시도
- 너무 긴 입력 (10,000자+)
- 특수문자 오남용
- API 남용 (초당 100회 요청)

**해결**
```python
from pydantic import BaseModel, Field, validator
import bleach

class SearchInput(BaseModel):
    query: str = Field(max_length=500)

    @validator('query')
    def sanitize(cls, v):
        return bleach.clean(v)

# Rate Limiting
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m')
async def search_view(request):
    ...
```

**도입 시점**: 퍼블릭 배포 시

---

## 3. 대화 컨텍스트 관리 (Conversation Context)

**문제**
멀티턴 대화 시 이전 검색 결과 참조 필요
- "아까 그 회사 더 자세히 알려줘"
- "연봉 더 높은 것만 다시 보여줘"
- "첫 번째랑 세 번째 비교해줘"

**해결**
```python
class ConversationManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1시간

    async def save_context(self, session_id: str, results: list):
        key = f"conversation:{session_id}"
        await self.redis.set(key, json.dumps(results), ex=self.ttl)

    async def get_context(self, session_id: str) -> list:
        key = f"conversation:{session_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else []
```

**도입 시점**: 사용자 피드백에서 멀티턴 필요성 확인 시

---

## 4. 검색 결과 정렬/필터 UI

**문제**
- 검색 후 결과 재정렬/필터링 불가
- "연봉 높은 순으로 정렬"
- "스타트업만 보기"
- "최근 일주일 공고만"

**해결**
- 프론트엔드 정렬/필터 UI
- 정렬 기준: 연봉, 회사 규모, 등록일
- 필터: 회사 유형, 근무 형태, 복지 조건

**도입 시점**: UI 개선 요청 시

---

## 5. 공고 저장 & 알림

**문제**
마음에 드는 공고 관리 기능 없음
- 관심 공고 저장
- 새로운 매칭 공고 알림
- 지원 현황 추적

**해결**
```python
class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    status = models.CharField(choices=[
        ('saved', '저장됨'),
        ('applied', '지원함'),
        ('interviewing', '면접중'),
        ('rejected', '불합격'),
        ('offered', '합격'),
    ])

# Celery Beat으로 새 공고 알림
@app.task
def check_new_matches():
    for user in User.objects.filter(notifications_enabled=True):
        new_matches = find_new_matches(user.saved_search_conditions)
        if new_matches:
            send_notification(user, new_matches)
```

**도입 시점**: 사용자 계정 기능 구현 후

---

## 6. A/B 테스트 인프라

**문제**
프롬프트 개선 효과 측정 어려움

**해결**
```python
# Promptfoo 또는 자체 구현
class PromptVariant:
    def __init__(self, name: str, prompt: str, weight: float = 0.5):
        self.name = name
        self.prompt = prompt
        self.weight = weight

class ABTestManager:
    variants = [
        PromptVariant("control", PROMPT_V1),
        PromptVariant("treatment", PROMPT_V2),
    ]

    def get_variant(self, user_id: str) -> PromptVariant:
        # 일관된 할당 (같은 유저는 같은 variant)
        hash_val = hash(user_id) % 100
        return self.variants[0] if hash_val < 50 else self.variants[1]

    def log_result(self, variant: str, success: bool, metrics: dict):
        # Langfuse에 기록
        langfuse.log_event(
            name="ab_test_result",
            metadata={"variant": variant, "success": success, **metrics}
        )
```

**도입 시점**: 프롬프트 최적화 필요 시

---

## 7. GPTCache (Semantic Cache)

**문제**
- 동일/유사 쿼리에 대해 LLM 재호출
- 비용 증가

**해결**
```python
from gptcache import cache
from gptcache.adapter import openai

# 유사 쿼리도 캐시 히트
# "백엔드 3년" ≈ "백엔드 개발자 3년차"
cache.init(
    embedding_func=embedding_model.embed,
    similarity_evaluation_func=similarity_eval,
    similarity_threshold=0.8,
)
```

**도입 시점**: LLM 비용 월 $50 이상 시

---

## 8. vLLM 셀프호스팅

**문제**
- Claude/OpenAI API 비용 증가
- API 의존성

**해결**
```bash
# vLLM 서버 실행
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-8B-Instruct \
    --dtype float16

# OpenAI 호환 API
curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "meta-llama/Llama-3-8B-Instruct", "messages": [...]}'
```

**도입 시점**: 월 LLM 비용 $200+ 또는 프라이버시 요구 시

---

## 9. 사용자 인증

**문제**
- 검색 히스토리 개인화 불가
- 저장 기능 구현 불가

**해결**
```python
# Django 기본 인증 + JWT
from rest_framework_simplejwt.authentication import JWTAuthentication

# 또는 소셜 로그인
# django-allauth 사용
SOCIALACCOUNT_PROVIDERS = {
    'google': {...},
    'github': {...},
}
```

**도입 시점**: 개인화 기능 필요 시

---

## 10. 모바일 앱 (React Native / Flutter)

**문제**
- 웹만 지원
- 푸시 알림 불가

**해결**
- 기존 API 그대로 사용
- React Native 또는 Flutter로 앱 개발
- Firebase FCM으로 푸시 알림

**도입 시점**: 웹 버전 안정화 후

---

## 11. MCP (Model Context Protocol) 도입

**문제**
- 현재 Tool 정의가 코드에 하드코딩됨
- 새로운 Tool 추가 시 Agent 코드 수정 필요
- Tool 간 표준화된 인터페이스 부재

**MCP란?**
- "AI 에이전트의 USB-C" - LLM과 외부 도구 간 표준 프로토콜
- Anthropic이 주도하는 오픈 표준
- Tool 정의를 JSON Schema로 표준화

**해결**
```python
# MCP 서버 정의 (tools/mcp_server.py)
from mcp import Server, Tool

server = Server("job-crawler-tools")

@server.tool()
async def search_jobs(keyword: str, location: str = None) -> list:
    """채용공고 검색"""
    return await crawler.search(keyword, location)

@server.tool()
async def get_job_detail(job_id: str) -> dict:
    """공고 상세 조회"""
    return await JobPosting.objects.aget(id=job_id)

# MCP 클라이언트 연결 (agent/nodes/execute.py)
from mcp import Client

mcp_client = Client()
await mcp_client.connect("job-crawler-tools")

# Tool 목록 자동 조회
tools = await mcp_client.list_tools()
```

**장점**
- Tool 추가/수정 시 Agent 코드 변경 불필요
- 다른 AI 서비스와 Tool 공유 가능
- Tool 버전 관리 용이

**도입 시점**: Tool 5개 이상 또는 외부 서비스 연동 시

---

## 우선순위 정리

| 순위 | 항목 | 이유 |
|------|------|------|
| 1 | 입력 검증 | 보안상 필수 (퍼블릭 배포 시) |
| 2 | 브라우저 풀 | 안정성 (사용자 증가 시) |
| 3 | 사용자 인증 | 개인화 기능의 전제 조건 |
| 4 | 공고 저장 | 핵심 사용자 기능 |
| 5 | GPTCache | 비용 절감 |
| 6 | 정렬/필터 UI | UX 개선 |
| 7 | 대화 컨텍스트 | 고급 기능 |
| 8 | A/B 테스트 | 최적화 |
| 9 | vLLM | 대규모 운영 시 |
| 10 | 모바일 앱 | 확장 |
| 11 | MCP | Tool 5개 이상, 외부 연동 시 |

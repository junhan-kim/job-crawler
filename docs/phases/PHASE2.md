# Phase 2: 실제 크롤링 연동

**목표**: 검색 → 실제 사람인 크롤링 → 결과 표시
**기간**: 2주
**기술 스택**: +Playwright, Django REST Framework (DRF)
**선행 조건**: Phase 1 완료

---

## 완성 시 데모

```
[웹 UI]
┌─────────────────────────────────────────┐
│  🔍 Python Django 백엔드                 │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  🔄 사람인에서 검색 중... (로딩)         │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  📋 검색 결과 5건                        │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ [OO회사] 백엔드 개발자              │ │
│  │ Python, Django / 연봉 5000만~      │ │
│  │ 📍 서울 강남 | 🕐 3일 전            │ │
│  │ [상세보기]                          │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ [XX테크] 서버 개발자                │ │
│  │ ...                                 │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 티켓 목록

### P2-0: Django REST Framework 도입 (선택)

**설명**
API 확장성을 위해 DRF를 도입한다. 현재 순수 Django로 작성된 API를 DRF 방식으로 리팩토링한다.

**작업 내용**
- [ ] `requirements.txt`에 `djangorestframework` 추가
- [ ] `settings.py`의 `INSTALLED_APPS`에 `rest_framework` 추가
- [ ] `config/views.py`를 DRF `APIView`로 리팩토링
  ```python
  from rest_framework.views import APIView
  from rest_framework.response import Response
  from rest_framework import status

  class SearchView(APIView):
      async def post(self, request):
          query = request.data.get('query', '').strip()
          if not query:
              return Response({'error': 'query required'}, status=status.HTTP_400_BAD_REQUEST)
          result = await run_agent(query)
          return Response(result)
  ```
- [ ] `config/urls.py` 수정
  ```python
  path('api/search/', SearchView.as_view(), name='search'),
  ```

**완료 기준**
- 기존 API와 동일하게 동작
- `request.data`로 요청 데이터 접근
- DRF Response 사용

**참고**
- Phase 1에서 API가 단순하여 순수 Django로 구현했으나, 확장성을 위해 DRF 도입 고려
- 필수는 아님 - 현재 구조로도 충분히 동작함

---

### P2-1: Playwright 환경 설정

**설명**
Playwright를 설치하고 Docker 환경에서 실행 가능하도록 설정한다.

**작업 내용**
- [ ] `requirements.txt`에 `playwright` 추가
- [ ] Dockerfile 수정 (Playwright 브라우저 설치)
  ```dockerfile
  RUN pip install playwright
  RUN playwright install chromium
  RUN playwright install-deps chromium
  ```
- [ ] docker-compose.yml 수정 (Playwright에 필요한 권한 추가)
  ```yaml
  web:
    security_opt:
      - seccomp:unconfined
    shm_size: '2gb'  # 브라우저 메모리
  ```
- [ ] 연결 테스트 스크립트 작성 (`scripts/test_playwright.py`)
  ```python
  from playwright.async_api import async_playwright

  async def test():
      async with async_playwright() as p:
          browser = await p.chromium.launch(headless=True)
          page = await browser.new_page()
          await page.goto("https://www.saramin.co.kr")
          print(await page.title())
          await browser.close()
  ```

**완료 기준**
- Docker 컨테이너 내에서 Playwright 실행 가능
- 사람인 메인 페이지 타이틀 출력 성공
- 메모리 부족 오류 없음

**참고**
- Playwright Docker: https://playwright.dev/python/docs/docker
- headless 모드 필수 (GUI 없는 환경)

---

### P2-2: 사람인 크롤러 구현

**설명**
사람인 채용 공고를 검색하고 파싱하는 크롤러를 구현한다.

**작업 내용**
- [ ] `crawlers/` 디렉토리 생성
- [ ] `crawlers/base.py` 작성 (크롤러 추상 클래스)
  ```python
  from abc import ABC, abstractmethod

  @dataclass
  class JobPosting:
      title: str
      company: str
      location: str
      salary: str | None
      skills: list[str]
      url: str
      posted_at: str | None
      source: str

  class BaseCrawler(ABC):
      @abstractmethod
      async def search(self, keyword: str, **filters) -> list[JobPosting]:
          pass
  ```
- [ ] `crawlers/saramin.py` 작성
  - 검색 URL 구성: `https://www.saramin.co.kr/zf_user/search?searchword={keyword}`
  - 검색 결과 페이지 파싱
  - 각 공고에서 추출할 정보:
    - 제목, 회사명, 지역, 연봉, 경력, 등록일, 상세 URL
  - 최대 10개 결과만 반환 (Phase 2에서는)
- [ ] 셀렉터 정의 (HTML 구조 분석 필요)
  ```python
  SELECTORS = {
      "job_card": "div.item_recruit",
      "title": "h2.job_tit a",
      "company": "strong.corp_name a",
      "location": "div.job_condition span:nth-child(1)",
      # ...
  }
  ```
- [ ] 에러 처리
  - 타임아웃 (10초)
  - 셀렉터 못 찾음 → 빈 리스트 반환 + 로깅
  - 차단 감지 → 예외 발생

**완료 기준**
- `SaraminCrawler().search("Python Django")` 호출 시 실제 공고 반환
- 반환된 데이터에 필수 필드 포함 (title, company, url)
- 타임아웃/에러 시 적절한 예외 발생

**주의사항**
- robots.txt 확인: 사람인은 /zf_user/search 허용
- 요청 간격: 최소 2초 대기
- User-Agent 설정 필요

---

### P2-3: 크롤링 안정성 레이어 추가

**설명**
크롤링 실패에 대비한 안정성 레이어를 추가한다. 검증된 라이브러리를 활용한다.

**의존성 추가**
```
tenacity>=8.0        # 재시도 로직
aiolimiter>=1.1      # async rate limiting
```

**작업 내용**
- [ ] `requirements.txt`에 `tenacity`, `aiolimiter` 추가
- [ ] `crawlers/utils.py` 작성
  - 재시도 데코레이터 (`tenacity` 활용)
    ```python
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError))
    )
    async def fetch_with_retry(page, url):
        return await page.goto(url, timeout=60000)
    ```
  - User-Agent 로테이션
    ```python
    import random

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ...",
    ]

    def get_random_user_agent() -> str:
        return random.choice(USER_AGENTS)
    ```
  - 요청 간격 제어 (`aiolimiter` 활용)
    ```python
    from aiolimiter import AsyncLimiter

    # 분당 20회 요청 제한
    rate_limiter = AsyncLimiter(20, 60)

    async def crawl_with_limit():
        async with rate_limiter:
            # 크롤링 로직
            ...
    ```
- [ ] `crawlers/saramin.py`에 적용
- [ ] 차단 감지 로직 추가
  - CAPTCHA 페이지 감지
  - 로그인 요구 페이지 감지
  - 감지 시 `CrawlerBlockedError` 발생

**완료 기준**
- 연속 요청 시 rate limit 준수 (분당 20회)
- 일시적 실패 시 exponential backoff로 자동 재시도 (최대 3회)
- 차단 감지 시 명확한 에러 메시지

**참고**
- tenacity: https://github.com/jd/tenacity
- aiolimiter: https://github.com/mjpieters/aiolimiter

---

### P2-4: LangGraph 워크플로우 확장 (Plan, Execute, Synthesize)

**설명**
LangGraph 워크플로우를 확장하여 전체 검색 플로우를 구현한다.

**작업 내용**
- [ ] `agent/nodes/plan.py` 작성
  - 파싱된 조건을 바탕으로 검색 전략 수립
  - 출력: 검색 키워드, 필터 조건
  ```python
  async def plan_node(state: AgentState) -> dict:
      conditions = state["parsed_conditions"]

      # 검색 키워드 생성
      keywords = []
      if conditions.get("role"):
          keywords.append(conditions["role"])
      if conditions.get("skills"):
          keywords.extend(conditions["skills"][:2])  # 상위 2개만

      return {
          "search_plan": {
              "keywords": keywords,
              "filters": {
                  "experience": conditions.get("experience_years"),
                  "location": conditions.get("location"),
              }
          }
      }
  ```
- [ ] `agent/nodes/execute.py` 작성
  - 크롤러를 실행하여 실제 검색 수행
  ```python
  async def execute_node(state: AgentState) -> dict:
      plan = state["search_plan"]
      crawler = SaraminCrawler()

      # 키워드로 검색
      keyword = " ".join(plan["keywords"])
      results = await crawler.search(keyword)

      return {"crawl_results": results}
  ```
- [ ] `agent/nodes/synthesize.py` 작성
  - 검색 결과를 요약하고 사용자에게 전달할 응답 생성
  ```python
  async def synthesize_node(state: AgentState) -> dict:
      results = state["crawl_results"]

      if not results:
          response = "검색 결과가 없습니다."
      else:
          response = f"{len(results)}개의 공고를 찾았습니다."

      return {
          "response": response,
          "final_results": results
      }
  ```
- [ ] `agent/graph.py` 수정 (노드 연결)
  ```python
  workflow.add_node("parse", parse_node)
  workflow.add_node("plan", plan_node)
  workflow.add_node("execute", execute_node)
  workflow.add_node("synthesize", synthesize_node)

  workflow.add_edge("parse", "plan")
  workflow.add_edge("plan", "execute")
  workflow.add_edge("execute", "synthesize")

  workflow.set_entry_point("parse")
  workflow.set_finish_point("synthesize")
  ```
- [ ] 상태 타입 확장
  ```python
  class AgentState(TypedDict):
      user_query: str
      parsed_conditions: dict | None
      search_plan: dict | None
      crawl_results: list[JobPosting] | None
      response: str | None
      final_results: list[JobPosting] | None
  ```

**완료 기준**
- 전체 워크플로우 실행 성공
- 각 노드 간 상태 전달 정상
- 최종 결과에 크롤링된 공고 포함

---

### P2-5: API 응답 구조 개선

**설명**
API 응답에 실제 검색 결과를 포함하도록 개선한다.

**작업 내용**
- [ ] 응답 스키마 정의
  ```python
  {
      "success": true,
      "query": "백엔드 개발자 3년차",
      "parsed_conditions": {
          "role": "백엔드 개발자",
          "experience_years": 3
      },
      "results": [
          {
              "title": "백엔드 개발자",
              "company": "OO회사",
              "location": "서울 강남",
              "salary": "5000-7000만",
              "skills": ["Python", "Django"],
              "url": "https://...",
              "posted_at": "3일 전",
              "source": "saramin"
          }
      ],
      "total_count": 5,
      "search_time_ms": 3500
  }
  ```
- [ ] `apps/search/serializers.py` 작성 (DRF Serializer)
- [ ] 응답 시간 측정 로직 추가
- [ ] 에러 응답 구조 정의
  ```python
  {
      "success": false,
      "error": {
          "code": "CRAWLING_FAILED",
          "message": "사람인 검색 중 오류가 발생했습니다."
      }
  }
  ```

**완료 기준**
- API 응답에 실제 크롤링 결과 포함
- 응답 시간 측정 가능
- 에러 시 구조화된 에러 응답

---

### P2-6: 웹 UI 개선 (결과 카드)

**설명**
검색 결과를 카드 형태로 표시하도록 UI를 개선한다.

**작업 내용**
- [ ] `templates/search.html` 수정
  - 결과 카드 컴포넌트 추가
  - 카드 내용: 제목, 회사명, 위치, 연봉, 스킬 태그, 등록일
  - 클릭 시 원본 URL로 이동
- [ ] CSS 스타일링 (Tailwind)
  ```html
  <div class="bg-white rounded-lg shadow p-4 hover:shadow-md transition">
      <h3 class="font-bold text-lg">{{ title }}</h3>
      <p class="text-gray-600">{{ company }}</p>
      <div class="flex gap-2 mt-2">
          <span class="text-sm text-gray-500">📍 {{ location }}</span>
          <span class="text-sm text-gray-500">💰 {{ salary }}</span>
      </div>
      <div class="flex gap-1 mt-2">
          {% for skill in skills %}
          <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
              {{ skill }}
          </span>
          {% endfor %}
      </div>
  </div>
  ```
- [ ] 결과 없음 UI
  ```html
  <div class="text-center py-10 text-gray-500">
      검색 결과가 없습니다.
  </div>
  ```
- [ ] 검색 소요 시간 표시

**완료 기준**
- 검색 결과가 카드 형태로 표시
- 스킬 태그 표시
- 원본 링크 클릭 가능
- 결과 없을 시 안내 메시지

---

### P2-7: 로딩 상태 UI

**설명**
검색 중 로딩 상태를 표시하고 UX를 개선한다.

**작업 내용**
- [ ] 로딩 스피너 컴포넌트 추가
  ```html
  <div id="loading" class="hidden">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      <p class="mt-2 text-gray-600">사람인에서 검색 중...</p>
  </div>
  ```
- [ ] JavaScript 수정
  ```javascript
  async function search(query) {
      showLoading();
      try {
          const response = await fetch('/api/search/', {...});
          const data = await response.json();
          renderResults(data.results);
      } catch (error) {
          showError(error.message);
      } finally {
          hideLoading();
      }
  }
  ```
- [ ] 검색 버튼 비활성화 (중복 요청 방지)
- [ ] 검색 진행 단계 표시 (선택적)
  - "조건 분석 중..."
  - "공고 검색 중..."
  - "결과 정리 중..."

**완료 기준**
- 검색 중 로딩 스피너 표시
- 중복 검색 요청 방지
- 에러 발생 시 에러 메시지 표시

---

### P2-8: 기본 에러 처리 UI

**설명**
다양한 에러 상황에 대한 사용자 친화적인 UI를 구현한다.

**작업 내용**
- [ ] 에러 메시지 컴포넌트
  ```html
  <div id="error" class="hidden bg-red-50 border border-red-200 rounded p-4">
      <p class="text-red-800 font-medium">오류가 발생했습니다</p>
      <p class="text-red-600 text-sm" id="error-message"></p>
      <button onclick="retry()" class="mt-2 text-red-600 underline">
          다시 시도
      </button>
  </div>
  ```
- [ ] 에러 타입별 메시지
  | 에러 코드 | 메시지 |
  |----------|--------|
  | CRAWLING_FAILED | 채용 사이트 연결에 실패했습니다. 잠시 후 다시 시도해주세요. |
  | LLM_ERROR | AI 분석 중 오류가 발생했습니다. |
  | TIMEOUT | 검색 시간이 초과되었습니다. |
  | INVALID_INPUT | 검색어를 입력해주세요. |
- [ ] 네트워크 오류 처리
- [ ] 재시도 버튼 기능

**완료 기준**
- 모든 에러 상황에 사용자 친화적 메시지 표시
- 재시도 기능 동작
- 콘솔에 상세 에러 로깅

---

### P2-9: 통합 테스트 및 안정화

**설명**
전체 플로우에 대한 통합 테스트를 작성하고 안정화한다.

**작업 내용**
- [ ] E2E 테스트 작성 (`tests/test_e2e.py`)
  - 검색 → 결과 반환 전체 플로우
  - 다양한 검색어 테스트
  - 에러 케이스 테스트
- [ ] 크롤러 단위 테스트 (`tests/test_crawlers.py`)
  - Mock 응답으로 파싱 로직 테스트
- [ ] 성능 측정
  - 평균 검색 시간 기록
  - 크롤링 성공률 기록
- [ ] 버그 수정 및 안정화
- [ ] README 업데이트 (실행 방법)

**완료 기준**
- 모든 테스트 통과
- 검색 성공률 90% 이상
- 평균 검색 시간 10초 이내

---

## 체크리스트

```
[x] P2-1: Playwright 환경 설정 (Docker)
[x] P2-2: 사람인 크롤러 구현
[x] P2-3: 크롤링 안정성 레이어 추가
[x] P2-4: LangGraph 워크플로우 확장
[x] P2-5: API 응답 구조 개선
[x] P2-6: 웹 UI 개선 (결과 카드)
[x] P2-7: 로딩 상태 UI
[x] P2-8: 기본 에러 처리 UI
[x] P2-9: 통합 테스트 및 안정화
────────────────────────────────────────
✅ 데모: 실제 사람인 검색 결과 표시
```

---

## 예상 트러블슈팅

| 문제 | 해결 방법 |
|------|----------|
| 사람인 HTML 구조 변경 | 여러 셀렉터 fallback, 구조 변경 감지 알림 |
| 크롤링 차단 | User-Agent 변경, 요청 간격 증가, IP 확인 |
| Playwright 메모리 부족 | shm_size 증가, 브라우저 재사용 |
| 검색 결과 0건 | 키워드 단순화, 필터 완화 로직 추가 (Phase 3) |
| 타임아웃 | 타임아웃 값 조정, 부분 결과 반환 |

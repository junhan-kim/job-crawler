# Phase 4: 멀티 소스 + 스트리밍

**목표**: 여러 사이트 동시 검색 + 실시간 결과 표시
**기간**: 2주
**기술 스택**: +SSE, httpx
**선행 조건**: Phase 3 완료

---

## 완성 시 데모

```
[웹 UI]
┌─────────────────────────────────────────┐
│  🔍 백엔드 개발자 Python                 │
│  [검색]                                  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  🔄 검색 중...                           │
│                                          │
│  ✅ 사람인: 5건 완료                     │
│  🔄 원티드: 검색 중...                   │
│  ⏳ 잡코리아: 대기 중                    │
│                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━ 66%          │
└─────────────────────────────────────────┘
                    │
                    ▼ (SSE 실시간 업데이트)
┌─────────────────────────────────────────┐
│  📋 총 12건                              │
│  사람인 5 / 원티드 4 / 잡코리아 3        │
│                                          │
│  [전체] [사람인] [원티드] [잡코리아]     │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ 🏢 원티드 | OO회사                  │ │
│  │ 백엔드 개발자 (Python/Django)      │ │
│  │ 💰 5000-7000만 | 📍 서울 강남       │ │
│  └────────────────────────────────────┘ │
│  ...                                     │
└─────────────────────────────────────────┘
```

---

## 티켓 목록

### P4-1: 원티드 크롤러 구현

**설명**
원티드 채용 공고를 검색하는 크롤러를 구현한다.

**작업 내용**
- [ ] `crawlers/wanted.py` 작성
  - 원티드 검색 URL 분석
    - 검색: `https://www.wanted.co.kr/search?query={keyword}&tab=position`
  - API 기반 검색 시도 (더 안정적)
    - 원티드는 내부 API 있음: `https://www.wanted.co.kr/api/v4/jobs`
    - API 가능하면 Playwright 대신 httpx 사용
  - 추출 필드:
    - title, company, location, salary_range, skills, url, posted_at
- [ ] 셀렉터/API 응답 파싱 로직
  ```python
  class WantedCrawler(BaseCrawler):
      async def search(self, keyword: str) -> list[JobPosting]:
          # API 방식 시도
          try:
              return await self._search_via_api(keyword)
          except Exception:
              # fallback: Playwright
              return await self._search_via_browser(keyword)

      async def _search_via_api(self, keyword: str) -> list[JobPosting]:
          async with httpx.AsyncClient() as client:
              response = await client.get(
                  "https://www.wanted.co.kr/api/v4/jobs",
                  params={"query": keyword, "limit": 20}
              )
              data = response.json()
              return [self._parse_api_job(job) for job in data['data']]
  ```
- [ ] 에러 처리 및 재시도 로직
- [ ] 단위 테스트

**완료 기준**
- `WantedCrawler().search("Python")` 호출 시 실제 공고 반환
- API 실패 시 브라우저 크롤링 fallback
- 사람인 크롤러와 동일한 출력 포맷

**참고**
- 원티드 robots.txt 확인 필요
- API가 막히면 Playwright로 전환

---

### P4-2: 잡코리아 크롤러 구현

**설명**
잡코리아 채용 공고를 검색하는 크롤러를 구현한다.

**작업 내용**
- [ ] `crawlers/jobkorea.py` 작성
  - 검색 URL: `https://www.jobkorea.co.kr/Search/?stext={keyword}`
  - 잡코리아는 API 없음 → Playwright 필수
- [ ] 셀렉터 정의
  ```python
  SELECTORS = {
      "job_list": "div.list-default",
      "job_item": "div.list-item",
      "title": "a.information-title",
      "company": "a.corp-name",
      "conditions": "p.chip-information-group span",
      # ...
  }
  ```
- [ ] 페이지네이션 처리 (선택적, 첫 페이지만도 가능)
- [ ] 에러 처리
- [ ] 단위 테스트

**완료 기준**
- `JobKoreaCrawler().search("백엔드")` 호출 시 실제 공고 반환
- 필수 필드 추출 (title, company, url)
- 크롤링 차단 감지

---

### P4-3: 크롤러 팩토리 및 통합

**설명**
여러 크롤러를 통합 관리하는 팩토리를 구현한다.

**작업 내용**
- [ ] `crawlers/__init__.py` 수정
  ```python
  class CrawlerFactory:
      CRAWLERS = {
          'saramin': SaraminCrawler,
          'wanted': WantedCrawler,
          'jobkorea': JobKoreaCrawler,
      }

      @classmethod
      def get_crawler(cls, source: str) -> BaseCrawler:
          crawler_class = cls.CRAWLERS.get(source)
          if not crawler_class:
              raise ValueError(f"Unknown source: {source}")
          return crawler_class()

      @classmethod
      def get_all_crawlers(cls) -> list[tuple[str, BaseCrawler]]:
          return [(name, cls()) for name, cls in cls.CRAWLERS.items()]
  ```
- [ ] 설정에서 활성화할 크롤러 지정
  ```python
  # settings/base.py
  ACTIVE_CRAWLERS = ['saramin', 'wanted', 'jobkorea']
  ```
- [ ] 크롤러 상태 관리
  ```python
  class CrawlerStatus:
      def __init__(self, source: str):
          self.source = source
          self.status = 'pending'  # pending, running, completed, failed
          self.result_count = 0
          self.error = None
  ```

**완료 기준**
- 팩토리로 모든 크롤러 접근 가능
- 활성화된 크롤러만 사용
- 각 크롤러 상태 추적 가능

---

### P4-4: 병렬 크롤링 구현

**설명**
여러 크롤러를 병렬로 실행하여 검색 시간을 단축한다.

**작업 내용**
- [ ] `agent/tools/crawler.py` 수정
  ```python
  import asyncio

  class CrawlerTool:
      def __init__(self):
          self.factory = CrawlerFactory()

      async def search_all(
          self,
          keyword: str,
          sources: list[str] = None
      ) -> dict[str, list[JobPosting]]:
          """모든 크롤러에서 병렬 검색"""
          sources = sources or settings.ACTIVE_CRAWLERS

          async def crawl_source(source: str):
              crawler = self.factory.get_crawler(source)
              try:
                  results = await asyncio.wait_for(
                      crawler.search(keyword),
                      timeout=30  # 사이트당 30초 타임아웃
                  )
                  return source, results, None
              except Exception as e:
                  return source, [], str(e)

          # 병렬 실행
          tasks = [crawl_source(s) for s in sources]
          results = await asyncio.gather(*tasks)

          return {
              source: {
                  'results': jobs,
                  'error': error
              }
              for source, jobs, error in results
          }
  ```
- [ ] 전체 타임아웃 설정 (60초)
- [ ] 부분 결과 반환 (일부 실패해도 성공한 것 반환)

**완료 기준**
- 3개 사이트 병렬 크롤링
- 총 소요 시간: max(개별 시간) + α (30-40초 예상)
- 일부 실패 시에도 부분 결과 반환

---

### P4-5: SSE 스트리밍 API 구현

**설명**
Server-Sent Events를 사용하여 검색 진행 상황을 실시간으로 전달한다.

**작업 내용**
- [ ] `apps/search/views.py`에 SSE 뷰 추가
  ```python
  from django.http import StreamingHttpResponse
  import json

  async def search_stream(request):
      query = request.GET.get('query', '')

      async def event_generator():
          # 파싱 단계
          yield f"data: {json.dumps({'stage': 'parsing', 'message': '검색 조건 분석 중...'})}\n\n"

          parsed = await parse_query(query)
          yield f"data: {json.dumps({'stage': 'parsed', 'conditions': parsed})}\n\n"

          # 크롤링 단계
          for source in ['saramin', 'wanted', 'jobkorea']:
              yield f"data: {json.dumps({'stage': 'crawling', 'source': source, 'status': 'started'})}\n\n"

          # 병렬 크롤링 (각 완료 시마다 이벤트)
          async for event in crawl_with_events(parsed):
              yield f"data: {json.dumps(event)}\n\n"

          # 완료
          yield f"data: {json.dumps({'stage': 'done'})}\n\n"

      return StreamingHttpResponse(
          event_generator(),
          content_type='text/event-stream',
          headers={
              'Cache-Control': 'no-cache',
              'X-Accel-Buffering': 'no',  # nginx 버퍼링 비활성화
          }
      )
  ```
- [ ] 이벤트 타입 정의
  ```python
  # 이벤트 스키마
  {
      'stage': 'parsing' | 'parsed' | 'crawling' | 'crawled' | 'synthesizing' | 'done',
      'source': str,  # 크롤링 중인 소스
      'status': 'started' | 'completed' | 'failed',
      'results': list,  # 해당 소스 결과
      'error': str,  # 에러 메시지
      'progress': float,  # 0-100
  }
  ```
- [ ] URL 라우팅 추가 (`GET /api/search/stream/`)

**완료 기준**
- SSE 연결 유지
- 각 단계 이벤트 수신 가능
- 브라우저에서 EventSource로 연결 가능

**참고**
- Django SSE: ASGI 필수
- nginx 사용 시 `X-Accel-Buffering: no` 필요

---

### P4-6: SSE 클라이언트 구현

**설명**
프론트엔드에서 SSE를 수신하고 UI를 업데이트한다.

**작업 내용**
- [ ] `static/js/search.js` 수정
  ```javascript
  function searchWithStream(query) {
      const eventSource = new EventSource(
          `/api/search/stream/?query=${encodeURIComponent(query)}`
      );

      eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data);

          switch (data.stage) {
              case 'parsing':
                  updateStatus('검색 조건 분석 중...');
                  break;
              case 'crawling':
                  updateCrawlerStatus(data.source, data.status);
                  break;
              case 'crawled':
                  addResults(data.source, data.results);
                  updateProgress(data.progress);
                  break;
              case 'done':
                  eventSource.close();
                  showFinalResults();
                  break;
          }
      };

      eventSource.onerror = (error) => {
          console.error('SSE Error:', error);
          eventSource.close();
          showError('연결이 끊어졌습니다.');
      };
  }
  ```
- [ ] 진행 상황 UI 컴포넌트
  ```javascript
  function updateCrawlerStatus(source, status) {
      const icons = {
          pending: '⏳',
          started: '🔄',
          completed: '✅',
          failed: '❌'
      };
      document.getElementById(`status-${source}`).textContent =
          `${icons[status]} ${source}`;
  }
  ```
- [ ] 프로그레스 바 업데이트

**완료 기준**
- 실시간으로 각 크롤러 상태 표시
- 결과가 오는 대로 UI 업데이트
- 프로그레스 바 동작

---

### P4-7: 소스별 필터 UI

**설명**
검색 결과를 소스별로 필터링하는 UI를 구현한다.

**작업 내용**
- [ ] 탭 UI 구현
  ```html
  <div class="flex gap-2 mb-4">
      <button class="tab active" data-source="all"
              onclick="filterBySource('all')">
          전체 (12)
      </button>
      <button class="tab" data-source="saramin"
              onclick="filterBySource('saramin')">
          사람인 (5)
      </button>
      <button class="tab" data-source="wanted"
              onclick="filterBySource('wanted')">
          원티드 (4)
      </button>
      <button class="tab" data-source="jobkorea"
              onclick="filterBySource('jobkorea')">
          잡코리아 (3)
      </button>
  </div>
  ```
- [ ] JavaScript 필터링
  ```javascript
  let allResults = [];  // 전체 결과 저장

  function filterBySource(source) {
      // 탭 활성화 상태 변경
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelector(`[data-source="${source}"]`).classList.add('active');

      // 필터링
      const filtered = source === 'all'
          ? allResults
          : allResults.filter(r => r.source === source);

      renderResults(filtered);
  }
  ```
- [ ] 결과 카드에 소스 뱃지 추가
  ```html
  <span class="px-2 py-1 text-xs rounded"
        style="background-color: {{ source_color }}">
      {{ source_name }}
  </span>
  ```
- [ ] 소스별 색상
  - 사람인: 파란색
  - 원티드: 보라색
  - 잡코리아: 초록색

**완료 기준**
- 탭 클릭 시 해당 소스 결과만 표시
- 각 탭에 결과 개수 표시
- 결과 카드에 소스 표시

---

### P4-8: 진행 상황 UI 개선

**설명**
검색 진행 상황을 더 상세하게 표시한다.

**작업 내용**
- [ ] 단계별 상태 표시
  ```html
  <div class="space-y-2">
      <div class="flex items-center gap-2">
          <span id="step-parse" class="status-icon">⏳</span>
          <span>검색 조건 분석</span>
      </div>
      <div class="flex items-center gap-2">
          <span id="step-crawl" class="status-icon">⏳</span>
          <span>채용 공고 검색</span>
          <div class="ml-4 text-sm text-gray-500">
              <span id="status-saramin">⏳ 사람인</span>
              <span id="status-wanted">⏳ 원티드</span>
              <span id="status-jobkorea">⏳ 잡코리아</span>
          </div>
      </div>
      <div class="flex items-center gap-2">
          <span id="step-analyze" class="status-icon">⏳</span>
          <span>결과 분석</span>
      </div>
  </div>
  ```
- [ ] 프로그레스 바
  ```html
  <div class="w-full bg-gray-200 rounded-full h-2">
      <div id="progress-bar"
           class="bg-blue-500 h-2 rounded-full transition-all duration-300"
           style="width: 0%">
      </div>
  </div>
  <p id="progress-text" class="text-sm text-gray-500 mt-1">0%</p>
  ```
- [ ] 예상 소요 시간 표시
- [ ] 취소 버튼 (선택적)

**완료 기준**
- 각 단계 상태 시각적 표시
- 프로그레스 바 진행률 표시
- 사용자가 현재 진행 상황 파악 가능

---

### P4-9: 통합 테스트 및 안정화

**설명**
멀티 소스 검색 전체 플로우를 테스트하고 안정화한다.

**작업 내용**
- [ ] E2E 테스트
  - 3개 사이트 동시 검색
  - 1개 사이트 실패 시 나머지 결과 반환
  - SSE 이벤트 순서 검증
- [ ] 성능 테스트
  - 병렬 크롤링 소요 시간 측정
  - SSE 지연 시간 측정
- [ ] 에러 케이스 테스트
  - 모든 크롤러 실패
  - SSE 연결 끊김
  - 타임아웃
- [ ] 버그 수정 및 안정화
- [ ] 문서 업데이트

**완료 기준**
- 모든 테스트 통과
- 병렬 크롤링 전체 시간 40초 이내
- SSE 이벤트 누락 없음
- 1개 이상 성공 시 부분 결과 표시

---

## 체크리스트

```
[ ] P4-1: 원티드 크롤러 구현
[ ] P4-2: 잡코리아 크롤러 구현
[ ] P4-3: 크롤러 팩토리 및 통합
[ ] P4-4: 병렬 크롤링 구현
[ ] P4-5: SSE 스트리밍 API 구현
[ ] P4-6: SSE 클라이언트 구현
[ ] P4-7: 소스별 필터 UI
[ ] P4-8: 진행 상황 UI 개선
[ ] P4-9: 통합 테스트 및 안정화
────────────────────────────────────────
✅ 데모: 3개 사이트 동시 검색 + 실시간 표시
```

---

## 예상 트러블슈팅

| 문제 | 해결 방법 |
|------|----------|
| 원티드 API 변경/차단 | Playwright fallback, API 버전 확인 |
| SSE 연결 끊김 | 자동 재연결 로직, 상태 복구 |
| 병렬 크롤링 메모리 | 브라우저 인스턴스 공유, 순차 실행 fallback |
| 일부 크롤러만 느림 | 개별 타임아웃, 빠른 것 먼저 표시 |
| nginx 버퍼링 | X-Accel-Buffering: no 헤더 |

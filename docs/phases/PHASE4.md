# Phase 4: 멀티 소스 + 스트리밍

**목표**: 여러 사이트 동시 검색 + 실시간 결과 표시
**상태**: 🔶 진행 중
**기술 스택**: SSE, httpx
**선행 조건**: Phase 3 완료

---

## 구현 완료 항목

### 1. 잡코리아 크롤러 (P4-2 ✅)
- `crawlers/jobkorea.py`: JobKoreaCrawler 구현
- Playwright 기반 크롤링
- 차단 감지, 지역/경력/마감일 파싱

### 2. 병렬 크롤링 (P4-3 ✅)
- `crawlers/services.py`: CrawlerService
- `asyncio.gather`로 사람인+잡코리아 병렬 실행
- 부분 실패 처리 (`return_exceptions=True`)

---

## 남은 티켓

### P4-1: 원티드 크롤러 구현

원티드 채용 공고 검색 크롤러 구현.

- `crawlers/wanted.py` 작성
- API 우선 시도, 실패 시 Playwright fallback
- `JobSource`에 WANTED 추가

**완료 기준**: `WantedCrawler().search("Python")` 호출 시 실제 공고 반환

---

### P4-4: LLM 기반 검색 재시도 ⭐

검색 결과 부족 시 LLM이 키워드를 확장하여 자동 재검색. LangGraph 조건부 엣지 활용.

**워크플로우**
```
parse → plan → execute → evaluate ─┬─ 결과 충분 → synthesize → END
                    ↑              │
                    └── 결과 부족 ──┘
                       (LLM 키워드 확장)
```

- `agent/nodes/evaluate.py`: 결과 평가 + 재검색 결정
- LLM 키워드 확장 (동의어, 유사 직무명)
- 조건부 엣지: `evaluate` → `plan` (재시도) 또는 `synthesize` (완료)
- 최대 2회 재시도

**완료 기준**: 결과 3건 미만 시 LLM이 키워드 확장 후 재검색

**의의**: LangGraph 조건부 분기 실습, 단순 파이프라인 → 에이전트 진화

---

### P4-5: SSE 스트리밍 API 구현

Server-Sent Events로 검색 진행 상황 실시간 전달.

- `GET /api/search/stream/` 엔드포인트
- 이벤트: parsing, crawling, crawled, synthesizing, done
- Django ASGI + StreamingHttpResponse

**완료 기준**: 브라우저에서 EventSource로 각 단계 이벤트 수신 가능

---

### P4-6: SSE 클라이언트 구현

프론트엔드에서 SSE 수신 및 UI 업데이트.

- `static/js/search.js`에 EventSource 연결
- 각 크롤러 상태 실시간 표시
- 프로그레스 바 업데이트

**완료 기준**: 결과가 오는 대로 UI 업데이트

---

### P4-7: 소스별 필터 UI

검색 결과를 소스별로 필터링하는 UI.

- 탭 UI: [전체] [사람인] [원티드] [잡코리아]
- 각 탭에 결과 개수 표시
- 결과 카드에 소스 뱃지 추가

**완료 기준**: 탭 클릭 시 해당 소스 결과만 표시

---

### P4-8: 진행 상황 UI 개선

검색 진행 상황 상세 표시.

- 단계별 상태 아이콘 (파싱 → 크롤링 → 분석)
- 프로그레스 바
- 각 크롤러별 상태 표시

**완료 기준**: 사용자가 현재 진행 상황 파악 가능

---

### P4-9: 통합 테스트 및 안정화

멀티 소스 검색 전체 플로우 테스트.

- E2E 테스트: 동시 검색, 부분 실패 처리
- 성능 테스트: 병렬 크롤링 시간, SSE 지연
- 에러 케이스: 전체 실패, 연결 끊김, 타임아웃

**완료 기준**: 모든 테스트 통과, 병렬 크롤링 40초 이내

---

## 체크리스트

```
[ ] P4-1: 원티드 크롤러 구현
[x] P4-2: 잡코리아 크롤러 구현
[x] P4-3: 병렬 크롤링 (CrawlerService)
[ ] P4-4: LLM 기반 검색 재시도 ⭐
[ ] P4-5: SSE 스트리밍 API 구현
[ ] P4-6: SSE 클라이언트 구현
[ ] P4-7: 소스별 필터 UI
[ ] P4-8: 진행 상황 UI 개선
[ ] P4-9: 통합 테스트 및 안정화
```

---

## 예상 트러블슈팅

| 문제 | 해결 방법 |
|------|----------|
| 원티드 API 변경/차단 | Playwright fallback |
| SSE 연결 끊김 | 자동 재연결 로직 |
| 병렬 크롤링 메모리 | 브라우저 인스턴스 공유 |
| nginx 버퍼링 | `X-Accel-Buffering: no` 헤더 |
| LLM 키워드 확장 실패 | 원래 키워드로 진행 |
| 무한 재시도 루프 | MAX_RETRY_COUNT 제한 |

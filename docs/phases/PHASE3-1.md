# Phase 3-1: 리팩토링 및 고민사항

**상태**: ✅ 완료

---

## 고민사항

### 1. View/Serializer 분리

현재 `api/views.py`와 `api/serializers.py`가 하나의 파일에 모든 API 관련 코드가 있음.

**고민 포인트:**
- 파일이 커지면 분리 필요 (search/, history/, load_more/ 등)
- 현재 규모에서 분리가 필요한가?

**결정:** `api/views/` 디렉토리로 분리 완료 (search.py, history.py, load_more.py)

---

### 2. 동시 크롤링 요청 처리

크롤링 중 같은 키워드로 또 요청이 들어오면?

**현재 상황:**
- `crawler_semaphore`로 동시 크롤링 1개 제한
- 두 번째 요청은 세마포어 대기 → 타임아웃 시 "Server busy" 에러

**고민 포인트:**
- 같은 키워드면 기존 작업 결과 대기하도록?
- 키워드별 락(lock) 필요?
- 아니면 현재 방식(busy 에러)이 더 단순하고 적절한가?

**결정:** 현재 방식 유지. Redis 캐시 + RAG + Semaphore 조합으로 충분.

---

### 3. 삭제된 공고 처리

DB에 데이터가 누적되는데, 실제로 마감되거나 삭제된 공고는?

**고민 포인트:**
- 마감일 기준 자동 삭제? (deadline 필드 활용)
- 주기적으로 URL 유효성 체크?
- soft delete (is_active 플래그)?
- 아니면 RAG 검색 시 최신순 가중치로 자연스럽게 밀려나게?

**결정:** Celery task로 30일 이상 오래된 공고 자동 정리 (`cleanup_old_jobs`) 구현.

---

### 4. RAG 벡터 검색 정확도 문제

Python 검색 시 Java 공고가 반환됨.

**분석 결과:**
```
=== 같아야 하는 것들 ===
python vs Python: 1.0000
python vs 파이썬: 0.4664 (너무 낮음)

=== 달라야 하는 것들 ===
Python 개발자 vs Java 개발자: 0.7684 (너무 높음)
```

임베딩 모델(`mxbai-embed-large`)이 Python/Java를 "프로그래밍 언어"라는 공통점으로 가깝게 인식.
distance threshold(0.25)로는 해결 불가 (Python vs Java distance = 0.23).

**선택지:**
- RAG 제거 → `search_jobs_from_db` (icontains) 방식으로 전환
- 하이브리드 → 키워드 검색 우선, RAG는 보조
- 더 좋은 임베딩 모델로 교체 (OpenAI text-embedding-3-small 등)

**결정:**
1. LLM을 Kanana (한국어 특화 모델)로 교체
2. 프롬프트 엔지니어링으로 할루시네이션 방지 (few-shot 예시 + "Do NOT add skills not in query")
3. 설정값 `settings.py`로 중앙화

---

## 체크리스트

- [x] P3-1-1: View/Serializer 분리 여부 결정
- [x] P3-1-2: 동시 크롤링 요청 처리 방안 결정
- [x] P3-1-3: 삭제된 공고 처리 방안 결정
- [x] P3-1-4: RAG 벡터 검색 정확도 개선 방안 결정

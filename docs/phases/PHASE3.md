# Phase 3: RAG + 데이터 저장

**목표**: 이전 검색 결과 재활용 + 더 정확한 매칭
**기간**: 2주
**기술 스택**: +PostgreSQL, pgvector, GPTCache, text-embedding-3-small
**선행 조건**: Phase 2 완료

---

## 완성 시 데모

```
[개선점]
├── 검색 속도 향상 (캐싱된 결과 즉시 반환)
├── 더 정확한 매칭 (벡터 유사도 검색)
└── 검색 히스토리 조회 가능

[웹 UI]
┌─────────────────────────────────────────┐
│  🔍 React 프론트엔드 2년차               │
│  [검색]                                  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  📊 최근 검색                            │
│  ┌─────────────────────────────────────┐│
│  │ "Python Django" (5분 전) - 8건      ││
│  │ "React 프론트엔드" (1시간 전) - 12건││
│  │ "백엔드 3년차" (어제) - 15건        ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## 티켓 목록

### P3-1: PostgreSQL + pgvector 설정

**설명**
PostgreSQL을 Docker에 추가하고 pgvector 확장을 설치한다.

**작업 내용**
- [ ] docker-compose.yml 수정
  ```yaml
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: jobcrawler
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  ```
- [ ] Django 설정 수정 (`config/settings/base.py`)
  ```python
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.postgresql',
          'NAME': os.getenv('DB_NAME', 'jobcrawler'),
          'USER': os.getenv('DB_USER', 'postgres'),
          'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
          'HOST': os.getenv('DB_HOST', 'db'),
          'PORT': os.getenv('DB_PORT', '5432'),
      }
  }
  ```
- [ ] `requirements.txt`에 `psycopg2-binary`, `pgvector` 추가
- [ ] pgvector 확장 활성화 (마이그레이션)
  ```python
  # migrations/0001_enable_pgvector.py
  from django.db import migrations

  class Migration(migrations.Migration):
      operations = [
          migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS vector;"),
      ]
  ```
- [ ] 연결 테스트

**완료 기준**
- Docker에서 PostgreSQL 실행
- Django에서 DB 연결 성공
- `SELECT * FROM pg_extension WHERE extname = 'vector';` 쿼리 성공

---

### P3-2: 채용공고 모델 구현

**설명**
채용공고를 저장하는 Django 모델을 구현한다.

**작업 내용**
- [ ] `apps/jobs/` Django 앱 생성
- [ ] `apps/jobs/models.py` 작성
  ```python
  from django.db import models
  from pgvector.django import VectorField

  class JobPosting(models.Model):
      # 기본 정보
      source = models.CharField(max_length=50)  # saramin, wanted, jobkorea
      source_id = models.CharField(max_length=100)  # 원본 사이트 ID
      url = models.URLField()

      # 공고 내용
      title = models.CharField(max_length=200)
      company = models.CharField(max_length=100)
      location = models.CharField(max_length=100, null=True)
      salary = models.CharField(max_length=100, null=True)
      experience = models.CharField(max_length=50, null=True)
      skills = models.JSONField(default=list)
      description = models.TextField(null=True)

      # 메타 정보
      posted_at = models.DateTimeField(null=True)
      crawled_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)
      is_active = models.BooleanField(default=True)

      # 벡터 임베딩 (pgvector)
      embedding = VectorField(dimensions=1536, null=True)

      class Meta:
          unique_together = ['source', 'source_id']
          indexes = [
              models.Index(fields=['source', 'crawled_at']),
              models.Index(fields=['is_active']),
          ]

      def __str__(self):
          return f"[{self.source}] {self.company} - {self.title}"
  ```
- [ ] 마이그레이션 생성 및 적용
- [ ] Admin 등록

**완료 기준**
- 마이그레이션 성공
- Admin에서 JobPosting CRUD 가능
- unique_together 제약 동작 확인

---

### P3-3: 임베딩 생성 모듈 구현

**설명**
OpenAI text-embedding-3-small을 사용하여 채용공고 임베딩을 생성한다.

**작업 내용**
- [ ] `core/embeddings.py` 작성
  ```python
  import openai
  from typing import list

  class EmbeddingService:
      def __init__(self, model: str = "text-embedding-3-small"):
          self.model = model
          self.client = openai.AsyncOpenAI()

      async def embed_text(self, text: str) -> list[float]:
          """단일 텍스트 임베딩 생성"""
          response = await self.client.embeddings.create(
              model=self.model,
              input=text
          )
          return response.data[0].embedding

      async def embed_batch(self, texts: list[str]) -> list[list[float]]:
          """배치 임베딩 생성 (최대 100개)"""
          response = await self.client.embeddings.create(
              model=self.model,
              input=texts
          )
          return [item.embedding for item in response.data]

      def create_job_text(self, job: JobPosting) -> str:
          """채용공고를 임베딩용 텍스트로 변환"""
          parts = [
              f"제목: {job.title}",
              f"회사: {job.company}",
              f"위치: {job.location or '미정'}",
              f"기술: {', '.join(job.skills) if job.skills else '미정'}",
          ]
          if job.description:
              parts.append(f"설명: {job.description[:500]}")
          return "\n".join(parts)
  ```
- [ ] `.env`에 `OPENAI_API_KEY` 추가
- [ ] 테스트 스크립트 작성
- [ ] 비용 추정
  - text-embedding-3-small: $0.02 / 1M tokens
  - 공고당 평균 200 토큰 → 1000개 = $0.004

**완료 기준**
- 단일 텍스트 임베딩 생성 성공
- 배치 임베딩 생성 성공
- 1536차원 벡터 반환 확인

**주의사항**
- API 키 노출 주의
- Rate limit: 3000 RPM (무료 티어 기준)

---

### P3-4: 크롤링 결과 DB 저장

**설명**
크롤링한 채용공고를 DB에 저장하고 임베딩을 생성한다.

**작업 내용**
- [ ] `apps/jobs/services.py` 작성
  ```python
  class JobService:
      def __init__(self):
          self.embedding_service = EmbeddingService()

      async def save_job(self, job_data: dict, source: str) -> JobPosting:
          """크롤링 결과를 DB에 저장"""
          job, created = await JobPosting.objects.aupdate_or_create(
              source=source,
              source_id=job_data['source_id'],
              defaults={
                  'title': job_data['title'],
                  'company': job_data['company'],
                  'location': job_data.get('location'),
                  'salary': job_data.get('salary'),
                  'skills': job_data.get('skills', []),
                  'url': job_data['url'],
                  'is_active': True,
              }
          )

          # 새로 생성되었거나 임베딩이 없으면 생성
          if created or job.embedding is None:
              text = self.embedding_service.create_job_text(job)
              job.embedding = await self.embedding_service.embed_text(text)
              await job.asave()

          return job

      async def save_batch(self, jobs: list[dict], source: str) -> int:
          """배치로 저장 (임베딩은 비동기로)"""
          saved_count = 0
          for job_data in jobs:
              await self.save_job(job_data, source)
              saved_count += 1
          return saved_count
  ```
- [ ] Execute 노드 수정 (크롤링 후 DB 저장)
  ```python
  async def execute_node(state: AgentState) -> dict:
      # ... 크롤링 실행
      results = await crawler.search(keyword)

      # DB에 저장
      job_service = JobService()
      for job in results:
          await job_service.save_job(job.to_dict(), source="saramin")

      return {"crawl_results": results}
  ```

**완료 기준**
- 크롤링 후 DB에 저장됨
- 중복 공고는 업데이트됨 (source + source_id 기준)
- 임베딩 생성 및 저장 완료

---

### P3-5: 벡터 검색 (RAG) 구현

**설명**
pgvector를 사용하여 벡터 유사도 검색을 구현한다.

**작업 내용**
- [ ] `agent/tools/rag.py` 작성
  ```python
  from pgvector.django import CosineDistance

  class RAGTool:
      def __init__(self):
          self.embedding_service = EmbeddingService()

      async def search(
          self,
          query: str,
          top_k: int = 20,
          filters: dict = None
      ) -> list[JobPosting]:
          """벡터 유사도 기반 검색"""
          # 쿼리 임베딩 생성
          query_embedding = await self.embedding_service.embed_text(query)

          # 기본 쿼리셋
          queryset = JobPosting.objects.filter(
              is_active=True,
              embedding__isnull=False
          )

          # 필터 적용
          if filters:
              if filters.get('location'):
                  queryset = queryset.filter(
                      location__icontains=filters['location']
                  )

          # 벡터 유사도 검색
          results = await queryset.annotate(
              distance=CosineDistance('embedding', query_embedding)
          ).order_by('distance')[:top_k].alist()

          return results
  ```
- [ ] 하이브리드 검색 구현 (RAG + 키워드)
  ```python
  async def hybrid_search(
      self,
      query: str,
      keywords: list[str],
      top_k: int = 20
  ) -> list[JobPosting]:
      """벡터 + 키워드 검색"""
      # 1. 벡터 검색
      vector_results = await self.search(query, top_k=top_k * 2)

      # 2. 키워드 필터링 (보조)
      keyword_q = Q()
      for kw in keywords:
          keyword_q |= Q(title__icontains=kw) | Q(skills__contains=[kw])

      keyword_results = await JobPosting.objects.filter(
          is_active=True
      ).filter(keyword_q)[:top_k].alist()

      # 3. 결과 병합 (중복 제거)
      seen = set()
      merged = []
      for job in vector_results + keyword_results:
          if job.id not in seen:
              seen.add(job.id)
              merged.append(job)

      return merged[:top_k]
  ```

**완료 기준**
- 벡터 유사도 검색 동작
- 키워드 검색과 병합 가능
- 필터(지역 등) 적용 가능

---

### P3-6: GPTCache 시맨틱 캐싱 설정

**설명**
GPTCache를 사용하여 시맨틱 캐싱을 구현한다. 유사한 검색어도 캐시 히트가 가능하다.

**GPTCache 선택 이유**
- LangChain/LlamaIndex 통합 완벽
- TTL, eviction, 유사도 threshold 내장
- 직접 구현 대비 안정성 높음
- 다양한 벡터 저장소 지원 (FAISS, pgvector 등)

**작업 내용**
- [ ] `requirements.txt`에 `gptcache` 추가
  ```
  gptcache>=0.1.40
  ```
- [ ] `core/cache.py` 작성
  ```python
  from gptcache import cache
  from gptcache.embedding import OpenAI as OpenAIEmbedding
  from gptcache.similarity_evaluation import SearchDistanceEvaluation
  from gptcache.manager import CacheBase, VectorBase, get_data_manager

  def init_gptcache():
      """GPTCache 초기화"""
      # 임베딩 모델 설정
      embedding = OpenAIEmbedding(model="text-embedding-3-small")

      # 유사도 평가 설정 (0.88 이상이면 캐시 히트)
      similarity_evaluation = SearchDistanceEvaluation()

      # 저장소 설정 (SQLite + FAISS)
      cache_base = CacheBase("sqlite")
      vector_base = VectorBase("faiss", dimension=1536)
      data_manager = get_data_manager(cache_base, vector_base)

      # 캐시 초기화
      cache.init(
          embedding_func=embedding.to_embeddings,
          similarity_evaluation=similarity_evaluation,
          data_manager=data_manager,
      )

      # TTL 설정 (24시간)
      cache.config.set("ttl", 86400)
  ```
- [ ] LangChain 통합
  ```python
  from gptcache.adapter.langchain_models import LangChainChat
  from langchain_openai import ChatOpenAI

  # 캐시가 적용된 LLM
  llm = LangChainChat(chat=ChatOpenAI(model="gpt-4o-mini"))
  ```
- [ ] 검색 결과 캐싱 래퍼
  ```python
  from gptcache import cache

  class SearchCache:
      def __init__(self, similarity_threshold: float = 0.88):
          self.threshold = similarity_threshold

      async def get_or_search(
          self,
          query: str,
          search_func: callable
      ) -> list:
          """캐시에서 조회하거나 검색 실행"""
          # GPTCache가 자동으로 유사 쿼리 매칭
          cached = cache.get(query)
          if cached:
              return cached

          # 캐시 미스 - 검색 실행
          results = await search_func(query)

          # 캐시 저장
          cache.set(query, results)
          return results
  ```
- [ ] 캐시 모니터링 설정
  ```python
  # 캐시 히트율 로깅
  from gptcache.utils import log

  log.set_level("INFO")  # 캐시 히트/미스 로깅
  ```

**완료 기준**
- GPTCache 초기화 성공
- "Python 백엔드" 검색 후 "파이썬 백엔드" 검색 시 캐시 히트
- 캐시 히트율 로그 확인
- TTL 만료 후 캐시 무효화 확인

**참고**
- GPTCache GitHub: https://github.com/zilliztech/GPTCache
- 유사도 threshold: 0.88로 시작, 모니터링 후 조정
- 벡터 저장소를 pgvector로 변경 가능 (나중에)

---

### P3-7: 검색 히스토리 기능

**설명**
사용자의 검색 히스토리를 저장하고 조회하는 기능을 구현한다.

**작업 내용**
- [ ] `apps/search/models.py` 작성
  ```python
  class SearchHistory(models.Model):
      query = models.CharField(max_length=500)
      parsed_conditions = models.JSONField()
      result_count = models.IntegerField()
      search_time_ms = models.IntegerField()
      created_at = models.DateTimeField(auto_now_add=True)
      # 나중에 user FK 추가

      class Meta:
          ordering = ['-created_at']
  ```
- [ ] 검색 완료 시 히스토리 저장
- [ ] 히스토리 조회 API
  ```python
  # GET /api/search/history/
  [
      {
          "id": 1,
          "query": "Python Django",
          "result_count": 8,
          "created_at": "2024-01-15T10:30:00Z"
      },
      ...
  ]
  ```
- [ ] 히스토리 클릭 시 재검색 기능

**완료 기준**
- 검색 시 히스토리 자동 저장
- 히스토리 조회 API 동작
- 최근 20개만 유지 (오래된 것 자동 삭제)

---

### P3-8: 검색 히스토리 UI

**설명**
검색 히스토리를 웹 UI에 표시한다.

**작업 내용**
- [ ] 히스토리 섹션 HTML 추가
  ```html
  <div class="mt-8">
      <h3 class="text-lg font-medium mb-4">📊 최근 검색</h3>
      <div id="history" class="space-y-2">
          <!-- 동적으로 채워짐 -->
      </div>
  </div>
  ```
- [ ] 히스토리 아이템 컴포넌트
  ```html
  <div class="flex justify-between items-center p-3 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer"
       onclick="searchAgain('{{ query }}')">
      <span class="font-medium">{{ query }}</span>
      <span class="text-sm text-gray-500">
          {{ result_count }}건 · {{ time_ago }}
      </span>
  </div>
  ```
- [ ] JavaScript
  ```javascript
  async function loadHistory() {
      const response = await fetch('/api/search/history/');
      const history = await response.json();
      renderHistory(history);
  }

  function searchAgain(query) {
      document.getElementById('search-input').value = query;
      search(query);
  }

  // 페이지 로드 시 히스토리 불러오기
  document.addEventListener('DOMContentLoaded', loadHistory);
  ```

**완료 기준**
- 페이지 로드 시 히스토리 표시
- 히스토리 클릭 시 검색창에 쿼리 입력 + 재검색
- 시간 표시 (5분 전, 1시간 전 등)

---

### P3-9: 검색 성능 최적화

**설명**
검색 성능을 측정하고 최적화한다.

**작업 내용**
- [ ] HNSW 인덱스 추가 (pgvector)
  ```python
  # 마이그레이션
  migrations.RunSQL(
      "CREATE INDEX job_embedding_idx ON jobs_jobposting "
      "USING hnsw (embedding vector_cosine_ops) "
      "WITH (m = 16, ef_construction = 64);"
  )
  ```
- [ ] 검색 시간 로깅
  ```python
  import time

  async def search_with_timing(query):
      start = time.time()
      results = await rag_tool.search(query)
      elapsed = (time.time() - start) * 1000
      logger.info(f"Search took {elapsed:.2f}ms")
      return results, elapsed
  ```
- [ ] N+1 쿼리 방지 (select_related, prefetch_related)
- [ ] 쿼리 플랜 분석 (EXPLAIN ANALYZE)

**완료 기준**
- RAG 검색 500ms 이내
- 전체 검색 플로우 5초 이내 (캐시 미스 시)
- 캐시 히트 시 1초 이내

---

## 체크리스트

```
[ ] P3-1: PostgreSQL + pgvector 설정
[ ] P3-2: 채용공고 모델 구현
[ ] P3-3: 임베딩 생성 모듈 구현
[ ] P3-4: 크롤링 결과 DB 저장
[ ] P3-5: 벡터 검색 (RAG) 구현
[ ] P3-6: GPTCache 시맨틱 캐싱 설정
[ ] P3-7: 검색 히스토리 기능
[ ] P3-8: 검색 히스토리 UI
[ ] P3-9: 검색 성능 최적화
────────────────────────────────────────
✅ 데모: 빠른 재검색 + 히스토리 조회
```

---

## 예상 트러블슈팅

| 문제 | 해결 방법 |
|------|----------|
| pgvector 인덱스 느림 | HNSW 인덱스 파라미터 튜닝 (m, ef_construction) |
| 임베딩 API 비용 | 배치 처리, 캐싱, 필요한 공고만 임베딩 |
| GPTCache 캐시 히트율 낮음 | similarity threshold 낮추기 (0.88 → 0.85) |
| GPTCache 잘못된 캐시 히트 | similarity threshold 높이기 (0.88 → 0.92) |
| 검색 결과 품질 낮음 | 임베딩 텍스트 포맷 개선, 리랭킹 추가 |

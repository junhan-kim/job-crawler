# Phase 3: RAG + 데이터 저장

**목표**: 이전 검색 결과 재활용 + 더 정확한 매칭
**기간**: 2주
**기술 스택**: +PostgreSQL, pgvector, GPTCache, Celery, Redis, text-embedding-3-small, LlamaIndex
**선행 조건**: Phase 2 완료

---

## 아키텍처 결정 사항

### 1. 크롤링 전략: 주기적 + 요청 시 병행

```
[주기적 크롤링 - 백그라운드]
├── 인기 키워드 (Python, Java, 프론트엔드 등): 6시간마다
├── 직군별 카테고리 전체: 24시간마다
└── 사용자 최근 검색어 기반: 6시간마다

[요청 시 크롤링 - 유지]
├── 캐시 히트 → 즉시 반환 (0.15초)
└── 캐시 미스 → 실시간 크롤링 (7초) → 결과 저장
```

**요청 시 크롤링 유지 이유:**
- 캐시 미스 대응 (모든 키워드 커버 불가)
- 실시간성 (방금 올라온 공고)
- 롱테일 쿼리 ("Rust embedded 시스템" 등 희귀 검색어)

### 2. 주기적 크롤링 수집 대상

| 대상 | 주기 | 예시 |
|-----|------|-----|
| 인기 키워드 | 6시간 | Python, Java, React, 백엔드, 프론트엔드 (상위 20개) |
| 직군 카테고리 | 24시간 | 사람인/잡코리아 직군 분류 전체 |
| 최근 검색어 | 6시간 | SearchHistory 테이블에서 추출 |

**수집 필드:**
- 공고 제목, 회사명, 위치, 급여, 원문 URL
- 크롤링 시각
- 임베딩 벡터 (제목+설명 기반)

### 3. 효율화 시뮬레이션

| 시나리오 | 첫 요청 | 반복 요청 | 유사 요청 |
|---------|--------|----------|----------|
| 현재 (요청 시 크롤링만) | 7초 | 7초 | 7초 |
| + Vector Search | 7초 | 0.15초 | 7초 |
| + GPTCache | 7초 | 0.15초 | 0.1초 |

**시나리오 상세:**
```
[현재] "Python 백엔드" 검색 10회 = 70초

[Phase 3] "Python 백엔드" 검색 10회
= 첫 요청 7초 + 이후 9회 × 0.15초 = 8.35초 (88% 단축)

[Phase 3] "파이썬 서버개발" (유사 쿼리)
= GPTCache 유사도 매칭 → 0.1초 (캐시 히트)
```

### 4. 검색 흐름도

```
사용자 요청 "Python 백엔드 3년차"
    ↓
┌─────────────────────────────────────────────────────────┐
│ 1. Redis 캐시 조회 (검색 결과 캐싱)                      │
│    ├── 히트 → 즉시 반환 (0.01초)                        │
│    └── 미스 ↓                                           │
├─────────────────────────────────────────────────────────┤
│ 2. LLM 쿼리 분석 (의도 파싱)                            │
│    ├── GPTCache 히트 → 캐싱된 분석 결과 (0.1초)         │
│    └── GPTCache 미스 → LLM 호출 (1초)                   │
│    결과: {skill: "Python", role: "백엔드", exp: 3}      │
├─────────────────────────────────────────────────────────┤
│ 3. pgvector 벡터 검색 (DB 조회)                         │
│    ├── 히트 (결과 존재) → 반환 (0.15초)                 │
│    └── 미스 (결과 부족) ↓                               │
├─────────────────────────────────────────────────────────┤
│ 4. 실시간 크롤링                                        │
│    → 결과 저장 (DB + 임베딩) (7초)                      │
├─────────────────────────────────────────────────────────┤
│ 5. 결과 반환 + Redis 캐시 저장                          │
└─────────────────────────────────────────────────────────┘
```

**캐시 역할 분리:**
| 캐시 | 대상 | TTL | 용도 |
|------|------|-----|------|
| Redis | 검색 결과 (공고 리스트) | 1시간 | 동일 쿼리 빠른 반환 |
| GPTCache | LLM 분석 결과 (의도 파싱) | 24시간 | 유사 쿼리 LLM 비용 절감 |
| pgvector | 공고 임베딩 | 영구 | 벡터 유사도 검색 |

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

### P3-3: LlamaIndex 기반 임베딩/인덱싱 설정

**설명**
LlamaIndex를 사용하여 임베딩 생성과 벡터 저장소를 통합 관리한다.

**작업 내용**
- [ ] `requirements.txt`에 LlamaIndex 추가
  ```
  llama-index>=0.10.0
  llama-index-vector-stores-postgres
  llama-index-embeddings-openai
  ```
- [ ] `core/llama_index_setup.py` 작성
  ```python
  from llama_index.core import Settings, VectorStoreIndex
  from llama_index.embeddings.openai import OpenAIEmbedding
  from llama_index.vector_stores.postgres import PGVectorStore
  import os

  def init_llama_index():
      """LlamaIndex 전역 설정"""
      Settings.embed_model = OpenAIEmbedding(
          model="text-embedding-3-small",
          api_key=os.getenv("OPENAI_API_KEY"),
      )
      Settings.chunk_size = 512
      Settings.chunk_overlap = 50

  def get_vector_store() -> PGVectorStore:
      """pgvector 저장소 연결"""
      return PGVectorStore.from_params(
          database=os.getenv("DB_NAME", "jobcrawler"),
          host=os.getenv("DB_HOST", "db"),
          password=os.getenv("DB_PASSWORD", "postgres"),
          port=os.getenv("DB_PORT", "5432"),
          user=os.getenv("DB_USER", "postgres"),
          table_name="job_embeddings",
          embed_dim=1536,
      )
  ```
- [ ] `core/embedding_service.py` 작성 (LlamaIndex 래퍼)
  ```python
  from llama_index.core import Settings
  from llama_index.core.schema import TextNode

  class EmbeddingService:
      """LlamaIndex 기반 임베딩 서비스"""

      async def embed_text(self, text: str) -> list[float]:
          """단일 텍스트 임베딩"""
          return await Settings.embed_model.aget_text_embedding(text)

      async def embed_batch(self, texts: list[str]) -> list[list[float]]:
          """배치 임베딩"""
          return await Settings.embed_model.aget_text_embedding_batch(texts)

      def create_job_node(self, job: "JobPosting") -> TextNode:
          """채용공고를 LlamaIndex 노드로 변환"""
          text = f"""
          제목: {job.title}
          회사: {job.company}
          위치: {job.location or '미정'}
          기술: {', '.join(job.skills) if job.skills else '미정'}
          경력: {job.experience or '무관'}
          """
          return TextNode(
              text=text,
              metadata={
                  "job_id": job.id,
                  "source": job.source,
                  "company": job.company,
                  "location": job.location,
              }
          )
  ```
- [ ] `.env`에 `OPENAI_API_KEY` 추가
- [ ] 비용 추정: $0.02 / 1M tokens (공고 1000개 = $0.004)

**완료 기준**
- LlamaIndex 초기화 성공
- pgvector 연결 성공
- 임베딩 생성 및 저장 테스트 통과

**주의사항**
- LlamaIndex는 동기/비동기 API 모두 제공 (aget_* 메서드 사용)

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

### P3-5: 벡터 검색 (RAG) 구현 - LlamaIndex 활용

**설명**
LlamaIndex + pgvector를 사용하여 벡터 유사도 검색을 구현한다.

**LlamaIndex 선택 이유**
- 160+ 데이터 로더 지원 (다양한 채용사이트 확장 용이)
- pgvector 네이티브 통합
- 하이브리드 검색 (벡터 + 키워드) 내장
- 자동 청킹, 인덱싱, 리랭킹 지원

**작업 내용**
- [ ] `agent/tools/rag.py` 작성 (LlamaIndex 네이티브 API)
  ```python
  from llama_index.core import VectorStoreIndex
  from llama_index.core.vector_stores import (
      MetadataFilter,
      MetadataFilters,
      FilterOperator,
  )
  from core.llama_index_setup import get_vector_store

  class RAGTool:
      def __init__(self):
          self.vector_store = get_vector_store()
          self.index = VectorStoreIndex.from_vector_store(self.vector_store)

      async def search(
          self,
          query: str,
          top_k: int = 20,
          filters: dict = None
      ) -> list[dict]:
          """벡터 유사도 기반 검색"""
          # 메타데이터 필터 구성
          metadata_filters = None
          if filters:
              filter_list = []
              if filters.get("location"):
                  filter_list.append(
                      MetadataFilter(
                          key="location",
                          value=filters["location"],
                          operator=FilterOperator.CONTAINS,
                      )
                  )
              if filter_list:
                  metadata_filters = MetadataFilters(filters=filter_list)

          # LlamaIndex retriever 사용
          retriever = self.index.as_retriever(
              similarity_top_k=top_k,
              filters=metadata_filters,
          )

          # 비동기 검색
          nodes = await retriever.aretrieve(query)

          # 결과 변환
          return [
              {
                  "job_id": node.metadata.get("job_id"),
                  "text": node.text,
                  "score": node.score,
                  "metadata": node.metadata,
              }
              for node in nodes
          ]

      async def hybrid_search(
          self,
          query: str,
          keywords: list[str],
          top_k: int = 20
      ) -> list[dict]:
          """벡터 + 키워드 하이브리드 검색"""
          # LlamaIndex의 하이브리드 검색 모드 활용
          from llama_index.core.retrievers import QueryFusionRetriever

          vector_retriever = self.index.as_retriever(similarity_top_k=top_k)

          # 키워드 기반 BM25 retriever (옵션)
          # bm25_retriever = BM25Retriever.from_defaults(...)

          # Reciprocal Rank Fusion으로 결과 병합
          fusion_retriever = QueryFusionRetriever(
              retrievers=[vector_retriever],
              similarity_top_k=top_k,
              num_queries=1,  # 쿼리 확장 비활성화
          )

          nodes = await fusion_retriever.aretrieve(query)
          return [{"job_id": n.metadata.get("job_id"), "score": n.score} for n in nodes]
  ```

**완료 기준**
- LlamaIndex retriever로 벡터 검색 동작
- 메타데이터 필터 (지역 등) 적용 가능
- 하이브리드 검색 구현 (선택)

---

### P3-6: GPTCache 시맨틱 캐싱 설정 (LLM 응답용)

**설명**
GPTCache를 사용하여 **LLM 응답(쿼리 분석 결과)**을 시맨틱 캐싱한다.
검색 결과 캐싱은 Redis로 분리한다.

**캐시 역할 분리 (중요)**
```
┌─────────────────────────────────────────────────────────┐
│ GPTCache: LLM 응답 캐싱                                 │
│ ├── 대상: 쿼리 분석 결과 (의도 파싱)                    │
│ ├── 예시: "Python 백엔드" → {skill, role, exp}          │
│ ├── 유사 쿼리 매칭: "파이썬 서버" ≈ "Python 백엔드"     │
│ └── 효과: LLM API 비용 절감                             │
├─────────────────────────────────────────────────────────┤
│ Redis: 검색 결과 캐싱                                   │
│ ├── 대상: 채용공고 리스트                               │
│ ├── 키: 정규화된 쿼리 해시                              │
│ └── 효과: DB 조회 스킵                                  │
└─────────────────────────────────────────────────────────┘
```

**작업 내용**
- [ ] `requirements.txt`에 추가
  ```
  gptcache>=0.1.40
  redis>=5.0.0
  ```
- [ ] `core/gptcache_setup.py` 작성 (LLM 응답 캐싱)
  ```python
  from gptcache import cache
  from gptcache.embedding import OpenAI as OpenAIEmbedding
  from gptcache.similarity_evaluation import SearchDistanceEvaluation
  from gptcache.manager import CacheBase, VectorBase, get_data_manager

  def init_gptcache():
      """GPTCache 초기화 - LLM 응답 캐싱용"""
      embedding = OpenAIEmbedding(model="text-embedding-3-small")
      similarity_evaluation = SearchDistanceEvaluation()

      cache_base = CacheBase("sqlite")
      vector_base = VectorBase("faiss", dimension=1536)
      data_manager = get_data_manager(cache_base, vector_base)

      cache.init(
          embedding_func=embedding.to_embeddings,
          similarity_evaluation=similarity_evaluation,
          data_manager=data_manager,
      )
      cache.config.set("ttl", 86400)  # 24시간
  ```
- [ ] `core/redis_cache.py` 작성 (검색 결과 캐싱)
  ```python
  import redis.asyncio as redis
  import json
  import hashlib

  class SearchResultCache:
      def __init__(self, redis_url: str = "redis://redis:6379/0"):
          self.redis = redis.from_url(redis_url)
          self.ttl = 3600  # 1시간

      def _make_key(self, query: str, filters: dict = None) -> str:
          """쿼리 + 필터를 해시하여 캐시 키 생성"""
          data = {"query": query.lower().strip(), "filters": filters or {}}
          return f"search:{hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()}"

      async def get(self, query: str, filters: dict = None) -> list | None:
          key = self._make_key(query, filters)
          data = await self.redis.get(key)
          return json.loads(data) if data else None

      async def set(self, query: str, results: list, filters: dict = None):
          key = self._make_key(query, filters)
          await self.redis.set(key, json.dumps(results), ex=self.ttl)
  ```
- [ ] LangChain 통합
  ```python
  from gptcache.adapter.langchain_models import LangChainChat
  from langchain_openai import ChatOpenAI

  # GPTCache가 적용된 LLM (쿼리 분석용)
  cached_llm = LangChainChat(chat=ChatOpenAI(model="gpt-4o-mini"))
  ```

**완료 기준**
- GPTCache: "Python 백엔드" 분석 후 "파이썬 백엔드" 분석 시 캐시 히트
- Redis: 동일 쿼리 재검색 시 캐시 히트
- 각 캐시 히트율 로그 확인

**참고**
- GPTCache: LLM 호출 캐싱 (유사 쿼리 매칭)
- Redis: 검색 결과 캐싱 (정확 매칭)

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

### P3-10: Celery 주기적 크롤링 설정

**설명**
Celery Beat를 사용하여 주기적으로 인기 키워드를 크롤링하고 DB에 저장한다.

**작업 내용**
- [ ] docker-compose.yml에 Redis, Celery worker, Celery beat 추가
  ```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery-worker:
    build: .
    command: celery -A config worker -l info
    depends_on:
      - redis
      - db

  celery-beat:
    build: .
    command: celery -A config beat -l info
    depends_on:
      - redis
  ```
- [ ] `config/celery.py` 작성
  ```python
  from celery import Celery

  app = Celery('job_crawler')
  app.config_from_object('django.conf:settings', namespace='CELERY')
  app.autodiscover_tasks()
  ```
- [ ] `requirements.txt`에 `celery`, `redis` 추가
- [ ] `apps/jobs/tasks.py` 작성
  ```python
  import asyncio
  from celery import shared_task
  from asgiref.sync import async_to_sync

  POPULAR_KEYWORDS = [
      "Python", "Java", "React", "백엔드", "프론트엔드",
      "DevOps", "데이터", "AI", "머신러닝", "Spring",
  ]

  @shared_task
  def crawl_popular_keywords():
      """인기 키워드 크롤링 (6시간마다)"""
      for keyword in POPULAR_KEYWORDS:
          crawl_and_save.delay(keyword)

  @shared_task
  def crawl_and_save(keyword: str):
      """단일 키워드 크롤링 후 DB 저장 (async 래핑)"""
      # Celery task는 동기이므로 async 코드를 래핑
      async_to_sync(_crawl_and_save_async)(keyword)

  async def _crawl_and_save_async(keyword: str):
      """실제 비동기 크롤링 로직"""
      from crawlers.saramin import SaraminCrawler
      from apps.jobs.services import JobService

      crawler = SaraminCrawler()
      job_service = JobService()

      try:
          results = await crawler.search(keyword, max_pages=3)
          for job_data in results:
              await job_service.save_job(job_data.to_dict(), source="saramin")
      finally:
          await crawler.close()
  ```

**주의: Celery + async 처리**
- Celery task 자체는 동기 함수
- `asgiref.sync.async_to_sync`로 async 코드 래핑
- 또는 `asyncio.run()` 사용 가능 (Python 3.10+)
- [ ] Celery Beat 스케줄 설정
  ```python
  # settings/base.py
  CELERY_BEAT_SCHEDULE = {
      'crawl-popular-keywords': {
          'task': 'apps.jobs.tasks.crawl_popular_keywords',
          'schedule': crontab(hour='*/6'),  # 6시간마다
      },
  }
  ```

**완료 기준**
- Celery worker, beat 컨테이너 실행
- 6시간마다 인기 키워드 자동 크롤링
- 크롤링 결과 DB에 저장 확인

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
[ ] P3-10: Celery 주기적 크롤링 설정
────────────────────────────────────────
✅ 데모: 빠른 재검색 + 히스토리 조회 + 주기적 크롤링
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

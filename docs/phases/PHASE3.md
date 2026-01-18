# Phase 3: RAG + 데이터 저장

**목표**: 이전 검색 결과 재활용 + 더 정확한 매칭
**상태**: ✅ 완료
**기술 스택**: PostgreSQL, pgvector, Celery, Redis, LlamaIndex, Ollama (nomic-embed-text)

---

## 구현 완료 항목

### 1. 인프라
- PostgreSQL + pgvector 확장 (Docker)
- Redis (검색 결과 캐싱 + LLM 응답 캐싱)
- Celery worker + beat (주기적 크롤링)

### 2. 데이터 모델
- `apps/jobs/models.py`: JobPosting (임베딩 포함)
- `apps/search/models.py`: SearchHistory

### 3. 임베딩 및 벡터 검색
- LlamaIndex + Ollama nomic-embed-text (1024 차원)
- pgvector HNSW 인덱스
- `agent/tools/rag.py`: RAGTool (벡터 검색)
- `core/embedding_service.py`: 임베딩 생성

### 4. 캐싱
- Redis: 검색 결과 캐싱 (TTL 1시간)
- LangChain RedisCache: LLM 응답 캐싱

### 5. 검색 흐름
```
사용자 요청
    ↓
Redis 캐시 조회 → 히트 시 즉시 반환 (1ms)
    ↓ 미스
LLM 쿼리 분석 (의도 파싱)
    ↓
pgvector 벡터 검색 → 결과 충분 시 반환
    ↓ 부족
실시간 크롤링 → DB 저장 + 임베딩 생성
    ↓
결과 반환 + Redis 캐싱
```

### 6. 주기적 크롤링 (Celery Beat)
- 인기 키워드: 6시간마다
- 최근 검색어 기반: 1시간마다

---

## 성능

| 시나리오 | 응답 시간 |
|---------|----------|
| Redis 캐시 히트 | ~1ms |
| RAG 검색 충분 | ~100ms |
| 실시간 크롤링 필요 | ~5초 |

---

## 체크리스트

- [x] P3-1: PostgreSQL + pgvector 설정
- [x] P3-2: 채용공고 모델 구현
- [x] P3-3: 임베딩 생성 모듈 구현
- [x] P3-4: 크롤링 결과 DB 저장
- [x] P3-5: 벡터 검색 (RAG) 구현
- [x] P3-6: 캐싱 설정 (Redis + LangChain Cache)
- [x] P3-7: 검색 히스토리 기능
- [x] P3-8: 검색 히스토리 UI
- [x] P3-9: 검색 성능 최적화 (HNSW 인덱스)
- [x] P3-10: Celery 주기적 크롤링 설정

---

## 변경 사항 (설계 대비)

| 항목 | 설계 | 실제 구현 |
|------|------|----------|
| 임베딩 모델 | text-embedding-3-small (OpenAI) | nomic-embed-text (Ollama) |
| 임베딩 차원 | 1536 | 1024 |
| LLM 캐시 | GPTCache | LangChain RedisCache |
| 벡터 검색 | LlamaIndex PGVectorStore | pgvector Django ORM (CosineDistance) |

# Troubleshooting

## 2026-01-20: RAG 검색 결과 무관한 공고 반환

### 문제
"python 5년차" 검색 시 카지노, 건설회사 등 전혀 무관한 채용공고가 반환됨.

### 원인 파악
1. **LLM 파싱 오류**: `skills: null` 반환 → Pydantic 검증 실패 → 빈 키워드로 검색
2. **임베딩 모델 결함**: `nomic-embed-text` 모델이 모든 입력에 대해 동일한 벡터 반환

```python
# 테스트 결과: 코사인 유사도가 모두 1.0 (동일 벡터)
similarity("python 개발자", "java 개발자") = 1.0
similarity("python 개발자", "요리사") = 1.0
```

### 해결
1. `ParsedQuery`에 `field_validator` 추가: `null` → `[]` 변환
2. 임베딩 모델 변경: `nomic-embed-text` → `mxbai-embed-large`
3. 임베딩 차원 수정: 768 → 1024
4. plan_node에 fallback 추가: 파싱된 키워드 없으면 원본 쿼리 사용

### 교훈
- 임베딩 모델 변경 시 반드시 유사도 테스트 필요
- LLM 출력은 항상 방어적으로 처리

---

## 2026-01-20: 1페이지 이외 크롤링 불가

### 문제
검색 결과가 1페이지만 반환되어 추가 페이지 로드 불가.

### 원인 파악
크롤러가 `max_pages` 파라미터를 받아 1~N페이지를 한 번에 크롤링하는 구조.
프론트엔드에서 특정 페이지만 요청하는 것이 불가능.

### 해결
1. `max_pages` → `page` 파라미터로 변경 (단일 페이지 요청)
2. 프론트엔드에 무한 스크롤 구현
3. `/api/load-more/` 엔드포인트 추가

### 변경 파일
- `crawlers/saramin.py`: `crawl(keyword, page)` 시그니처 변경
- `crawlers/jobkorea.py`: `crawl(keyword, page)` 시그니처 변경
- `api/views.py`: `LoadMoreView` 추가

---

## 2026-01-20: C# 키워드 검색 시 결과 없음

### 문제
"C#" 키워드 검색 시 "C" 관련 공고만 반환되거나 결과 없음.

### 원인 파악
URL에 `#` 문자가 인코딩 없이 들어가면서 fragment로 해석됨.
```
# Before
https://saramin.co.kr/search?keyword=C#  → 실제로는 keyword=C

# After
https://saramin.co.kr/search?keyword=C%23
```

### 해결
`urllib.parse.quote()`로 키워드 URL 인코딩 적용.

```python
from urllib.parse import quote

url = f"{self.SEARCH_URL}?searchword={quote(keyword)}&recruitPage={page}"
```

### 변경 파일
- `crawlers/saramin.py`: `quote(keyword)` 적용
- `crawlers/jobkorea.py`: `quote(keyword)` 적용

### 교훈
- URL 파라미터에 특수문자 포함 가능성 항상 고려
- `#`, `&`, `?`, `=` 등은 URL에서 특별한 의미를 가짐

---

## 2026-01-22: 한글 쿼리 파싱 시 LLM 할루시네이션

### 문제
"파이썬" 검색 시 Java 공고가 반환됨. LLM이 쿼리에 없는 스킬을 추가.

### 원인 파악
1. **llama3.2 3B 한국어 미지원**: 공식적으로 한국어 지원하지 않음, instruction following 불안정
2. **임베딩 문제**: Python vs Java distance = 0.23 (threshold 0.25보다 낮음)
3. **화이트리스트 할루시네이션**: 프롬프트에 스킬 목록 제공 시 모델이 전체 리스트 복사

### 해결
1. **LLM 모델 교체**: llama3.2 3B → Kanana (`huihui_ai/kanana-nano-abliterated`)
   - 카카오의 한국어 특화 모델 (2.1B)

2. **프롬프트 엔지니어링**:
   - 화이트리스트 제거 (모델이 복사하므로)
   - Few-shot 예시로 패턴 학습
   - "Do NOT add skills not in query" 명시

3. **설정 중앙화**:
   - `core/constants.py` 삭제 → `config/settings.py`로 이동
   - `docker-compose.yml`에서 모델명 환경변수화

### 변경 파일
- `agent/prompts.py`: Few-shot 프롬프트로 변경
- `config/settings.py`: EMBEDDING_MODEL, OLLAMA_MODEL 등 추가
- `docker-compose.yml`: `$OLLAMA_MODEL`, `$EMBEDDING_MODEL` 환경변수 사용
- `.env.example`: 새 모델명 반영

### 교훈
- 소형 LLM에 화이트리스트 제공 시 복사 할루시네이션 발생 가능
- Few-shot 예시가 화이트리스트보다 효과적
- 명시적 금지 지시문("Do NOT...") 필요

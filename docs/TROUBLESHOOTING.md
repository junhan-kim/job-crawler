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

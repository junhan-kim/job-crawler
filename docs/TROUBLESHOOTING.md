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

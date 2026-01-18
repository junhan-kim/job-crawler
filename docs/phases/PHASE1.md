# Phase 1: Hello World Agent

**목표**: 검색어 입력 → LLM이 응답하는 최소 동작 확인
**상태**: ✅ 완료
**기술 스택**: Django, Ollama, LangGraph, Docker

---

## 구현 완료 항목

### 1. 인프라
- Django 5.x + Uvicorn (ASGI)
- Docker Compose (web + ollama)
- Ollama llama3.2 모델

### 2. LLM 추상화
- `llm/base.py`: LLMProvider 추상 클래스
- `llm/ollama.py`: Ollama 구현체

### 3. LangGraph 워크플로우
- `agent/nodes/parse.py`: 사용자 쿼리 → 구조화된 조건 추출
- `agent/graph.py`: 워크플로우 정의

### 4. API
- `POST /api/search/`: 검색 API
- 입력 검증 (query 필수, 최대 500자)

### 5. 웹 UI
- Tailwind CSS 기반 단일 페이지
- 검색창 + 결과 표시

---

## 체크리스트

- [x] P1-1: Django 프로젝트 초기 세팅
- [x] P1-2: Docker Compose 개발 환경 구성
- [x] P1-3: Ollama 모델 다운로드 및 연동
- [x] P1-4: LLM 추상화 레이어 구현
- [x] P1-5: LangGraph 기본 워크플로우 구현
- [x] P1-6: Django API 엔드포인트 구현
- [x] P1-7: 웹 UI 구현
- [-] P1-8: Mock 검색 결과 (스킵)
- [x] P1-9: 에러 처리 및 로깅

# Phase 1: Hello World Agent

**목표**: 검색어 입력 → LLM이 응답하는 최소 동작 확인
**기간**: 2주
**기술 스택**: Django, Ollama, LangGraph, Docker

---

## 완성 시 데모

```
[웹 UI]
┌─────────────────────────────────────────┐
│  🔍 백엔드 개발자 3년차 공고 찾아줘      │
│  [검색]                                  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  📋 검색 조건을 분석했습니다:            │
│  - 직무: 백엔드 개발자                   │
│  - 경력: 3년                             │
│  - 스킬: (명시 안됨)                     │
│  - 지역: (명시 안됨)                     │
│                                          │
│  [Mock 결과]                             │
│  1. OO회사 - 백엔드 개발자               │
│  2. XX테크 - 서버 엔지니어               │
└─────────────────────────────────────────┘
```

---

## 티켓 목록

### P1-1: Django 프로젝트 초기 세팅

**설명**
Django 5.x 프로젝트를 생성하고 기본 구조를 설정한다. ASGI 서버(Uvicorn)를 사용하여 비동기 지원을 준비한다.

**작업 내용**
- [ ] Django 5.x 프로젝트 생성 (`django-admin startproject config .`)
- [ ] 설정 파일 분리 (`config/settings/base.py`, `dev.py`, `prod.py`)
- [ ] ASGI 설정 (`config/asgi.py`에 Uvicorn 연동)
- [ ] `.env.example` 파일 생성 (환경변수 템플릿)
- [ ] `requirements.txt` 작성 (Django, uvicorn, python-dotenv)
- [ ] `.gitignore` 설정

**완료 기준**
- `python manage.py runserver` 또는 `uvicorn config.asgi:application` 실행 시 Django 기본 페이지 표시
- 설정 파일이 환경별로 분리됨

**참고**
- Django ASGI: https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
- 설정 분리 패턴: https://djangostars.com/blog/configuring-django-settings-best-practices/

---

### P1-2: Docker Compose 개발 환경 구성

**설명**
로컬 개발을 위한 Docker Compose 설정. Django 서버와 Ollama를 컨테이너로 실행한다.

**작업 내용**
- [ ] `docker/Dockerfile` 작성 (Python 3.11 기반)
- [ ] `docker/docker-compose.yml` 작성
  - `web`: Django 서버 (포트 8000)
  - `ollama`: Ollama 서버 (포트 11434)
- [ ] `docker/docker-compose.yml`에 볼륨 마운트 (코드 변경 시 자동 반영)
- [ ] `.dockerignore` 파일 작성
- [ ] `Makefile` 작성 (자주 쓰는 명령어 단축)
  - `make up`: docker-compose up -d
  - `make down`: docker-compose down
  - `make logs`: docker-compose logs -f

**완료 기준**
- `docker-compose up` 실행 시 Django + Ollama 동시 실행
- `curl http://localhost:11434/api/tags` 실행 시 Ollama 응답 확인
- 코드 수정 시 Django 자동 리로드

**참고**
- Ollama Docker: https://hub.docker.com/r/ollama/ollama
- Django + Docker: https://docs.docker.com/samples/django/

---

### P1-3: Ollama 모델 다운로드 및 연동 테스트

**설명**
Ollama에 Llama3 모델을 다운로드하고 Python에서 호출 테스트를 수행한다.

**작업 내용**
- [ ] Ollama 컨테이너에서 `ollama pull llama3:8b` 실행
- [ ] Python 테스트 스크립트 작성 (`scripts/test_ollama.py`)
  ```python
  import httpx

  response = httpx.post(
      "http://localhost:11434/api/generate",
      json={"model": "llama3:8b", "prompt": "Hello", "stream": False}
  )
  print(response.json())
  ```
- [ ] 응답 시간 측정 (첫 요청 vs 이후 요청)
- [ ] 한국어 테스트: "백엔드 개발자 3년차"를 입력하고 파싱 결과 확인

**완료 기준**
- Ollama API 호출 성공
- 한국어 입력에 대해 의미 있는 응답 반환
- 응답 시간 기록 (baseline 확보)

**참고**
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Llama3 한국어 성능은 제한적임을 인지 (개발 단계에서는 무관)

---

### P1-4: LLM 추상화 레이어 구현

**설명**
LLM Provider를 추상화하여 Ollama/Claude/OpenAI를 동일한 인터페이스로 사용할 수 있게 한다. Phase 1에서는 Ollama 구현체만 작성한다.

**작업 내용**
- [ ] `llm/` 디렉토리 생성
- [ ] `llm/base.py` 작성 (추상 클래스)
  ```python
  from abc import ABC, abstractmethod
  from dataclasses import dataclass

  @dataclass
  class LLMResponse:
      content: str
      model: str
      latency_ms: int

  class LLMProvider(ABC):
      @abstractmethod
      async def chat(self, messages: list[dict]) -> LLMResponse:
          pass
  ```
- [ ] `llm/ollama.py` 작성 (Ollama 구현체)
  - httpx async client 사용
  - 타임아웃 30초 설정
  - 에러 시 예외 발생 (`LLMError`)
- [ ] `llm/exceptions.py` 작성 (`LLMError`, `LLMTimeoutError`)
- [ ] 단위 테스트 작성 (`tests/test_llm.py`)

**완료 기준**
- `OllamaProvider().chat([{"role": "user", "content": "Hello"}])` 호출 성공
- 타임아웃 시 `LLMTimeoutError` 발생
- 테스트 통과

**참고**
- httpx async: https://www.python-httpx.org/async/
- Python ABC: https://docs.python.org/3/library/abc.html

---

### P1-5: LangGraph 기본 워크플로우 구현

**설명**
LangGraph를 사용하여 최소한의 Agent 워크플로우를 구현한다. Phase 1에서는 Parse 노드만 구현한다.

**작업 내용**
- [ ] `agent/` 디렉토리 생성
- [ ] `agent/state.py` 작성 (Agent 상태 정의)
  ```python
  from typing import TypedDict

  class AgentState(TypedDict):
      user_query: str
      parsed_conditions: dict | None
      response: str | None
  ```
- [ ] `agent/nodes/parse.py` 작성 (Parse 노드)
  - 사용자 입력을 받아 구조화된 조건 추출
  - LLM에 프롬프트 전달하여 JSON 형태로 파싱
  - 파싱 결과: `{role, experience_years, skills, location, salary}`
- [ ] `agent/prompts/parse.py` 작성 (파싱용 프롬프트)
  ```python
  PARSE_PROMPT = """
  사용자의 채용 검색 요청에서 다음 정보를 추출하세요:
  - role: 직무 (예: 백엔드 개발자, 프론트엔드 개발자)
  - experience_years: 경력 연차 (숫자)
  - skills: 기술 스택 (리스트)
  - location: 희망 지역
  - min_salary: 최소 희망 연봉 (만원 단위)

  정보가 없으면 null로 표시하세요.
  JSON 형식으로만 응답하세요.

  사용자 입력: {query}
  """
  ```
- [ ] `agent/graph.py` 작성 (메인 워크플로우)
  ```python
  from langgraph.graph import StateGraph

  workflow = StateGraph(AgentState)
  workflow.add_node("parse", parse_node)
  workflow.set_entry_point("parse")
  workflow.set_finish_point("parse")  # Phase 1에서는 여기서 종료

  app = workflow.compile()
  ```
- [ ] 통합 테스트 작성

**완료 기준**
- `app.invoke({"user_query": "백엔드 3년차 파이썬"})` 실행 시 파싱된 조건 반환
- 다양한 입력 테스트:
  - "백엔드 개발자 3년차" → `{role: "백엔드 개발자", experience_years: 3}`
  - "React 프론트 신입" → `{role: "프론트엔드 개발자", skills: ["React"], experience_years: 0}`
  - "연봉 5천 이상" → `{min_salary: 5000}`

**참고**
- LangGraph: https://langchain-ai.github.io/langgraph/
- JSON 파싱 실패 시 재시도 로직 필요 (LLM이 JSON을 안 줄 수 있음)

---

### P1-6: Django API 엔드포인트 구현

**설명**
검색 요청을 받아 Agent를 실행하고 결과를 반환하는 API 엔드포인트를 구현한다.

**작업 내용**
- [ ] `apps/search/` Django 앱 생성 (`python manage.py startapp search apps/search`)
- [ ] `apps/search/views.py` 작성
  ```python
  from django.http import JsonResponse
  from django.views import View
  import asyncio

  class SearchView(View):
      async def post(self, request):
          data = json.loads(request.body)
          query = data.get("query", "")

          # Agent 실행
          result = await app.ainvoke({"user_query": query})

          return JsonResponse({
              "query": query,
              "parsed_conditions": result["parsed_conditions"],
              "results": []  # Phase 1에서는 빈 배열
          })
  ```
- [ ] `config/urls.py`에 라우팅 추가 (`/api/search/`)
- [ ] CORS 설정 (django-cors-headers)
- [ ] 입력 검증 추가 (query 필수, 최대 500자)
- [ ] API 테스트 (curl 또는 httpie)

**완료 기준**
- `POST /api/search/` 호출 시 JSON 응답 반환
- 잘못된 입력 시 400 에러
- CORS 헤더 포함

**테스트 명령어**
```bash
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "백엔드 개발자 3년차"}'
```

---

### P1-7: 웹 UI 구현 (검색 페이지)

**설명**
간단한 웹 UI를 구현한다. 검색창과 결과 표시 영역으로 구성된 단일 페이지.

**작업 내용**
- [ ] `templates/` 디렉토리 생성
- [ ] `templates/base.html` 작성 (기본 레이아웃)
  - Tailwind CSS CDN 사용
  - 반응형 레이아웃
- [ ] `templates/search.html` 작성
  - 검색창 (input + button)
  - 결과 표시 영역 (div)
  - 로딩 상태 표시
- [ ] `static/js/search.js` 작성
  - fetch API로 `/api/search/` 호출
  - 결과를 DOM에 렌더링
  - 에러 처리 (네트워크 오류, 서버 오류)
- [ ] `apps/search/views.py`에 페이지 뷰 추가
  ```python
  def search_page(request):
      return render(request, "search.html")
  ```
- [ ] 라우팅 추가 (`/` → search_page)

**완료 기준**
- `http://localhost:8000/` 접속 시 검색 페이지 표시
- 검색어 입력 후 버튼 클릭 시 결과 표시
- 로딩 중 표시 (spinner 또는 텍스트)
- 모바일에서도 사용 가능

**UI 스케치**
```
┌────────────────────────────────────────────────────┐
│  Job Crawler                                       │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────────────────────┐  ┌────────┐│
│  │ 백엔드 개발자 3년차 공고 찾아줘   │  │  검색  ││
│  └──────────────────────────────────┘  └────────┘│
│                                                    │
│  ─────────────────────────────────────────────────│
│                                                    │
│  📋 파싱 결과:                                     │
│  • 직무: 백엔드 개발자                             │
│  • 경력: 3년                                       │
│  • 스킬: -                                         │
│  • 지역: -                                         │
│                                                    │
│  (Phase 2에서 실제 검색 결과 표시 예정)            │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

### P1-8: Mock 검색 결과 추가

**설명**
실제 크롤링 없이 테스트용 Mock 데이터를 반환하도록 한다. UI 완성도를 높이고 Phase 2 준비.

**작업 내용**
- [ ] `agent/tools/mock_data.py` 작성
  ```python
  MOCK_JOBS = [
      {
          "title": "백엔드 개발자",
          "company": "테스트회사",
          "salary": "5000-7000만",
          "location": "서울 강남",
          "skills": ["Python", "Django"],
          "url": "https://example.com/job/1"
      },
      # ... 5개 정도
  ]
  ```
- [ ] Parse 노드에서 Mock 데이터 필터링 로직 추가
  - 파싱된 조건과 Mock 데이터 매칭
  - 단순 키워드 매칭으로 구현
- [ ] API 응답에 Mock 결과 포함
- [ ] UI에서 결과 카드 렌더링

**완료 기준**
- 검색 시 Mock 데이터 중 매칭되는 결과 표시
- "백엔드" 검색 시 백엔드 관련 Mock 데이터 반환
- 결과 카드에 회사명, 포지션, 연봉, 링크 표시

---

### P1-9: 에러 처리 및 로깅

**설명**
기본적인 에러 처리와 로깅을 추가한다.

**작업 내용**
- [ ] `core/exceptions.py` 작성 (커스텀 예외)
  - `SearchError`
  - `ParseError`
  - `LLMError` (기존)
- [ ] Django 에러 핸들러 설정
  - 500 에러 시 JSON 응답 반환
  - 로깅 추가
- [ ] 로깅 설정 (`config/settings/base.py`)
  ```python
  LOGGING = {
      'version': 1,
      'handlers': {
          'console': {'class': 'logging.StreamHandler'},
      },
      'loggers': {
          'agent': {'handlers': ['console'], 'level': 'DEBUG'},
          'llm': {'handlers': ['console'], 'level': 'INFO'},
      },
  }
  ```
- [ ] Agent 노드에 로깅 추가
  - 입력/출력 로깅
  - 실행 시간 로깅

**완료 기준**
- LLM 호출 실패 시 사용자에게 에러 메시지 표시
- 콘솔에 디버그 로그 출력
- 에러 발생 위치 추적 가능

---

## 체크리스트

```
[x] P1-1: Django 프로젝트 초기 세팅 (간소화 - settings 분리 안함)
[x] P1-2: Docker Compose 개발 환경 구성
[x] P1-3: Ollama 모델 다운로드 및 연동 테스트 (docker-compose에서 자동 pull)
[x] P1-4: LLM 추상화 레이어 구현
[x] P1-5: LangGraph 기본 워크플로우 구현
[x] P1-6: Django API 엔드포인트 구현
[x] P1-7: 웹 UI 구현 (검색 페이지)
[-] P1-8: Mock 검색 결과 추가 (스킵 - 실제 파싱 결과로 대체)
[~] P1-9: 에러 처리 및 로깅 (기본 에러 처리만 구현)
────────────────────────────────────────
✅ 데모: 검색 입력 → LLM 파싱 → 결과 표시 완료
```

---

## 예상 트러블슈팅

| 문제 | 해결 방법 |
|------|----------|
| Ollama 한국어 성능 저하 | 프롬프트에 예시 추가, JSON 형식 강제 |
| LLM JSON 파싱 실패 | 재시도 로직 + 정규식 fallback |
| Docker 볼륨 권한 문제 | `chown` 또는 user 설정 |
| Django async view 문제 | `sync_to_async` 래퍼 사용 |

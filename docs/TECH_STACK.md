# 기술 스택

## Core

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| **Backend** | Django 5.x | 풀스택 프레임워크, 인증/ORM 내장, Admin 제공 |
| **API** | Django REST Framework | REST API 구축, 직렬화, 인증 통합 |
| **Database** | PostgreSQL 16 | 안정성, pgvector 확장 지원 |
| **Cache/Queue** | Redis | Celery 브로커 + 응답 캐싱 |
| **Task Queue** | Celery | 백그라운드 작업 (주기적 크롤링, 배치 임베딩) |

---

## LLM & Agent

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| **Orchestration** | LangGraph | 상태 기반 Agent, 조건부 분기, 체크포인팅 |
| **LLM Framework** | LangChain | LLM 추상화, 도구 통합, 프롬프트 관리 |
| **LLM (Dev)** | Ollama + Llama3 | 무료, 로컬 개발 |
| **LLM (Prod)** | Claude 3.5 Sonnet | 한국어 성능, 긴 컨텍스트 |
| **Embedding** | text-embedding-3-small | 가성비, 한국어 지원 |
| **Vector DB** | pgvector | PostgreSQL 확장, 인프라 단순화 |

---

## Crawling

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| **Browser Automation** | Playwright | JS 렌더링, 안정적, 비동기 지원 |
| **HTTP Client** | httpx | 비동기 HTTP, 성능 |

---

## Monitoring & Evaluation

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| **LLM Tracing** | Langfuse | 오픈소스, 셀프호스트 가능, 비용 추적 |
| **Evaluation** | RAGAS | RAG 파이프라인 품질 평가 (Post-MVP) |

---

## Infrastructure

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| **Container** | Docker + Compose | 개발/배포 일관성 |
| **Cloud** | AWS EC2 (초기) | 단순, 비용 예측 가능 |
| **CI/CD** | GitHub Actions | 자동 배포 |

---

## 확장 옵션 (Scale-up 시 고려)

| 영역 | 기술 | 도입 시점 |
|------|------|----------|
| **Tool Protocol** | MCP (Model Context Protocol) | 복잡한 Tool 관리 필요 시 |
| **LLM Self-hosting** | vLLM | 트래픽 증가로 비용 절감 필요 시 |
| **Semantic Cache** | GPTCache | LLM 비용 추가 절감 필요 시 |
| **Multi-Agent** | CrewAI | 복잡한 멀티에이전트 협업 필요 시 |
| **Vector DB (대규모)** | Qdrant / Pinecone | 공고 100만건+ 또는 고성능 필요 시 |
| **LLM Gateway** | Portkey / LiteLLM | 다중 LLM Provider 관리, 로드밸런싱 |
| **RAG 고도화** | LlamaIndex | 복잡한 RAG 파이프라인 필요 시 |
| **Prompt Testing** | Promptfoo | 프롬프트 A/B 테스트 자동화 |

---

## Phase별 기술 스택 도입

```
Phase 1: Django, Ollama, LangGraph, Docker
         └── 최소 동작 확인

Phase 2: +Playwright, LangChain
         └── 실제 크롤링

Phase 3: +PostgreSQL, pgvector, Redis, text-embedding-3-small
         └── RAG + 캐싱

Phase 4: +SSE, httpx
         └── 멀티 소스 + 스트리밍

Phase 5: +Langfuse, AWS EC2, GitHub Actions
         └── 배포 + 모니터링
```

---

## LLM Provider 추상화 설계

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] | None
    usage: TokenUsage
    model: str
    latency_ms: int

class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict]) -> str:
        """단순 채팅 응답"""
        pass

    @abstractmethod
    async def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict]
    ) -> LLMResponse:
        """Tool calling 포함 응답"""
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """모델별 최대 토큰 수"""
        pass

# 구현체
class OllamaProvider(LLMProvider): ...  # 개발용
class ClaudeProvider(LLMProvider): ...  # 프로덕션
class OpenAIProvider(LLMProvider): ...  # 백업
```

**기능 폴백 전략**:
- Tool calling 미지원 시 → 프롬프트로 JSON 출력 유도 + 파싱
- 컨텍스트 작을 시 → 자동으로 요약/청킹 적용

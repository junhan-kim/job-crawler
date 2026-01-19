# Job Crawler

LLM 기반 채용 정보 검색 에이전트

---

## 문서

| 문서 | 설명 |
|------|------|
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 시스템 아키텍처 |
| [docs/TECH_STACK.md](./docs/TECH_STACK.md) | 기술 스택 |
| [docs/PROBLEMS.md](./docs/PROBLEMS.md) | 예상 문제점 및 해결 전략 |
| [docs/POST_MVP.md](./docs/POST_MVP.md) | MVP 이후 개선 사항 |
| [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) | 트러블슈팅 기록 |

---

## Phase별 상세 계획

| Phase | 목표 | 기간 | 상세 |
|-------|------|------|------|
| **1** | Hello World Agent | 2주 | [PHASE1.md](./docs/phases/PHASE1.md) |
| **2** | 실제 크롤링 연동 | 2주 | [PHASE2.md](./docs/phases/PHASE2.md) |
| **3** | RAG + 데이터 저장 | 2주 | [PHASE3.md](./docs/phases/PHASE3.md) |
| **4** | 멀티 소스 + 스트리밍 | 2주 | [PHASE4.md](./docs/phases/PHASE4.md) |
| **5** | 모니터링 + 배포 | 1주 | [PHASE5.md](./docs/phases/PHASE5.md) |

---

## Quick Start

```bash
docker-compose up -d
```

http://localhost:8000

---

## 테스트

```bash
# 의존성 설치
pip install -r requirements.txt

# 테스트 실행
pytest
```

---

## 프로젝트 구조

```
job-crawler/
├── agent/              # LangGraph 에이전트 (nodes, graph)
├── api/                # Django REST Framework API
├── crawlers/           # Playwright 크롤러 (사람인 등)
├── config/             # Django 설정
├── templates/          # 웹 UI 템플릿
├── tests/              # 테스트
└── docs/               # 문서
```

---

## 기술 스택 요약

**Core**: Django, PostgreSQL, Redis, Docker

**LLM & Agent**: LangGraph, LangChain, Ollama (Dev), Claude (Prod)

**Crawling**: Playwright, httpx

**Monitoring**: Langfuse

**Infrastructure**: AWS EC2, GitHub Actions

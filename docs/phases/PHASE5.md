# Phase 5: 모니터링 + 배포

**목표**: AWS 배포 + 운영 모니터링
**기간**: 1주
**기술 스택**: +Langfuse, AWS EC2, GitHub Actions
**선행 조건**: Phase 4 완료

---

## 완성 시

```
├── 실제 URL로 접속 가능 (AWS EC2)
├── Langfuse에서 LLM 호출 추적 가능
├── 에러 발생 시 로그 확인 가능
└── GitHub push 시 자동 배포
```

---

## 티켓 목록

### P5-1: Langfuse 설정 및 연동

**설명**
LLM 호출을 추적하고 비용을 모니터링하기 위해 Langfuse를 연동한다.

**작업 내용**
- [ ] Langfuse Cloud 계정 생성 (또는 셀프호스트)
  - https://cloud.langfuse.com
  - 무료 티어: 50K observations/월
- [ ] API 키 발급
- [ ] `requirements.txt`에 `langfuse` 추가
- [ ] `llm/base.py` 수정 (Langfuse 데코레이터)
  ```python
  from langfuse.decorators import observe, langfuse_context

  class LLMProvider(ABC):
      @observe(as_type="generation")
      async def chat(self, messages: list[dict]) -> LLMResponse:
          # Langfuse에 자동 기록
          langfuse_context.update_current_observation(
              model=self.model_name,
              input=messages,
          )
          response = await self._chat_impl(messages)
          langfuse_context.update_current_observation(
              output=response.content,
              usage={
                  "input": response.usage.prompt_tokens,
                  "output": response.usage.completion_tokens,
              }
          )
          return response
  ```
- [ ] Agent 워크플로우 트레이싱
  ```python
  from langfuse.decorators import observe

  @observe(name="search_agent")
  async def run_agent(query: str):
      # 전체 Agent 실행이 하나의 trace로 기록
      result = await agent.ainvoke({"user_query": query})
      return result
  ```
- [ ] 환경 변수 설정
  ```
  LANGFUSE_SECRET_KEY=sk-...
  LANGFUSE_PUBLIC_KEY=pk-...
  LANGFUSE_HOST=https://cloud.langfuse.com  # 셀프호스트면 변경
  ```

**완료 기준**
- LLM 호출이 Langfuse 대시보드에 표시
- 토큰 사용량, 비용 추적 가능
- 에러 발생 시 trace 확인 가능

**참고**
- Langfuse Python SDK: https://langfuse.com/docs/sdk/python

---

### P5-2: 프로덕션 Docker 설정

**설명**
프로덕션 환경을 위한 Docker 설정을 구성한다.

**작업 내용**
- [ ] `docker/Dockerfile.prod` 작성
  ```dockerfile
  FROM python:3.11-slim

  # 보안: non-root 사용자
  RUN useradd -m -u 1000 appuser

  WORKDIR /app

  # 의존성 설치
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  RUN playwright install chromium && playwright install-deps chromium

  # 소스 복사
  COPY . .

  # 정적 파일 수집
  RUN python manage.py collectstatic --noinput

  USER appuser

  EXPOSE 8000

  CMD ["gunicorn", "config.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000"]
  ```
- [ ] `docker/docker-compose.prod.yml` 작성
  ```yaml
  version: '3.8'

  services:
    web:
      build:
        context: ..
        dockerfile: docker/Dockerfile.prod
      ports:
        - "8000:8000"
      environment:
        - DJANGO_SETTINGS_MODULE=config.settings.prod
        - DATABASE_URL=postgres://...
        - REDIS_URL=redis://redis:6379/0
      depends_on:
        - db
        - redis
      restart: unless-stopped

    db:
      image: pgvector/pgvector:pg16
      volumes:
        - postgres_data:/var/lib/postgresql/data
      environment:
        - POSTGRES_DB=${DB_NAME}
        - POSTGRES_USER=${DB_USER}
        - POSTGRES_PASSWORD=${DB_PASSWORD}
      restart: unless-stopped

    redis:
      image: redis:7-alpine
      volumes:
        - redis_data:/data
      restart: unless-stopped

  volumes:
    postgres_data:
    redis_data:
  ```
- [ ] `config/settings/prod.py` 작성
  ```python
  from .base import *

  DEBUG = False
  ALLOWED_HOSTS = [os.getenv('ALLOWED_HOST', '*')]

  # 보안 설정
  SECURE_BROWSER_XSS_FILTER = True
  SECURE_CONTENT_TYPE_NOSNIFF = True
  X_FRAME_OPTIONS = 'DENY'

  # 정적 파일
  STATIC_ROOT = BASE_DIR / 'staticfiles'

  # 로깅
  LOGGING['handlers']['file'] = {
      'class': 'logging.FileHandler',
      'filename': '/var/log/app/django.log',
  }
  ```
- [ ] `.env.prod.example` 작성

**완료 기준**
- 프로덕션 Docker 이미지 빌드 성공
- `docker-compose -f docker-compose.prod.yml up` 실행 성공
- gunicorn + uvicorn 워커 동작

---

### P5-3: AWS EC2 인스턴스 설정

**설명**
AWS EC2 인스턴스를 생성하고 기본 설정을 한다.

**작업 내용**
- [ ] EC2 인스턴스 생성
  - AMI: Ubuntu 22.04 LTS
  - Instance Type: t3.medium (2 vCPU, 4GB RAM)
  - Storage: 30GB SSD
  - Security Group:
    - 22 (SSH)
    - 80 (HTTP)
    - 443 (HTTPS)
- [ ] SSH 키 설정
- [ ] 기본 패키지 설치
  ```bash
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y docker.io docker-compose git
  sudo usermod -aG docker ubuntu
  ```
- [ ] Swap 메모리 설정 (4GB)
  ```bash
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  ```
- [ ] 방화벽 설정 (ufw)
- [ ] 시간대 설정 (Asia/Seoul)

**완료 기준**
- EC2 인스턴스 SSH 접속 가능
- Docker 실행 가능
- 필요한 포트 열림

**비용 예상**
- t3.medium: ~$30/월 (온디맨드)
- 절약: Reserved Instance 또는 Spot Instance 검토

---

### P5-4: 도메인 및 HTTPS 설정 (선택)

**설명**
도메인을 연결하고 HTTPS를 설정한다. (선택 사항)

**작업 내용**
- [ ] 도메인 구매 또는 무료 도메인 (선택)
- [ ] Route53 또는 Cloudflare DNS 설정
- [ ] Nginx 리버스 프록시 설정
  ```nginx
  server {
      listen 80;
      server_name your-domain.com;

      location / {
          proxy_pass http://localhost:8000;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection 'upgrade';
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;

          # SSE를 위한 설정
          proxy_buffering off;
          proxy_cache off;
      }
  }
  ```
- [ ] Let's Encrypt SSL 인증서 (certbot)
  ```bash
  sudo apt install certbot python3-certbot-nginx
  sudo certbot --nginx -d your-domain.com
  ```

**완료 기준**
- `https://your-domain.com` 접속 가능
- SSL 인증서 자동 갱신 설정

---

### P5-5: GitHub Actions CI/CD 파이프라인

**설명**
GitHub에 push 시 자동으로 배포되는 CI/CD 파이프라인을 구성한다.

**작업 내용**
- [ ] `.github/workflows/deploy.yml` 작성
  ```yaml
  name: Deploy to EC2

  on:
    push:
      branches: [main]

  jobs:
    deploy:
      runs-on: ubuntu-latest

      steps:
        - uses: actions/checkout@v4

        - name: Deploy to EC2
          uses: appleboy/ssh-action@master
          with:
            host: ${{ secrets.EC2_HOST }}
            username: ubuntu
            key: ${{ secrets.EC2_SSH_KEY }}
            script: |
              cd /home/ubuntu/job-crawler
              git pull origin main
              docker-compose -f docker/docker-compose.prod.yml build
              docker-compose -f docker/docker-compose.prod.yml up -d
              docker system prune -f
  ```
- [ ] GitHub Secrets 설정
  - `EC2_HOST`: EC2 퍼블릭 IP
  - `EC2_SSH_KEY`: SSH 프라이빗 키
  - `DB_PASSWORD`: DB 비밀번호
  - `OPENAI_API_KEY`: OpenAI API 키
  - `LANGFUSE_SECRET_KEY`: Langfuse 키
- [ ] 테스트 워크플로우 추가 (선택)
  ```yaml
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          pip install -r requirements.txt
          python manage.py test
  ```

**완료 기준**
- main 브랜치 push 시 자동 배포
- 배포 실패 시 GitHub에서 확인 가능
- 롤백 가능 (git revert)

---

### P5-6: 로깅 및 에러 추적

**설명**
프로덕션 환경에서 로그를 수집하고 에러를 추적한다.

**작업 내용**
- [ ] 로그 파일 설정
  ```python
  LOGGING = {
      'version': 1,
      'handlers': {
          'file': {
              'class': 'logging.handlers.RotatingFileHandler',
              'filename': '/var/log/app/django.log',
              'maxBytes': 10 * 1024 * 1024,  # 10MB
              'backupCount': 5,
          },
          'console': {
              'class': 'logging.StreamHandler',
          },
      },
      'loggers': {
          'django': {'handlers': ['file', 'console'], 'level': 'INFO'},
          'agent': {'handlers': ['file', 'console'], 'level': 'DEBUG'},
          'crawlers': {'handlers': ['file', 'console'], 'level': 'INFO'},
      },
  }
  ```
- [ ] 로그 볼륨 마운트 (docker-compose)
  ```yaml
  volumes:
    - ./logs:/var/log/app
  ```
- [ ] 크롤러 성공률 로깅
  ```python
  logger.info(f"Crawl completed: {source} - {len(results)} results")
  ```
- [ ] 에러 알림 (선택: Slack/Discord webhook)

**완료 기준**
- 로그 파일 생성 및 로테이션
- 에러 발생 시 상세 정보 기록
- 로그 파일 접근 가능 (SSH 또는 볼륨)

---

### P5-7: 헬스체크 및 모니터링

**설명**
서비스 상태를 확인하는 헬스체크 엔드포인트를 구현한다.

**작업 내용**
- [ ] 헬스체크 엔드포인트
  ```python
  # apps/core/views.py
  async def health_check(request):
      checks = {
          'database': await check_database(),
          'redis': await check_redis(),
          'ollama': await check_ollama(),
      }

      all_healthy = all(checks.values())

      return JsonResponse({
          'status': 'healthy' if all_healthy else 'unhealthy',
          'checks': checks,
          'timestamp': datetime.now().isoformat(),
      }, status=200 if all_healthy else 503)

  async def check_database():
      try:
          await JobPosting.objects.afirst()
          return True
      except Exception:
          return False
  ```
- [ ] Docker 헬스체크
  ```yaml
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
    interval: 30s
    timeout: 10s
    retries: 3
  ```
- [ ] 간단한 상태 페이지 (선택)
  - 최근 검색 수
  - 크롤러 상태
  - 캐시 히트율

**완료 기준**
- `/health/` 엔드포인트 응답
- 각 컴포넌트 상태 확인 가능
- 비정상 시 503 반환

---

### P5-8: 최종 테스트 및 문서화

**설명**
프로덕션 환경에서 최종 테스트를 수행하고 문서를 완성한다.

**작업 내용**
- [ ] 프로덕션 E2E 테스트
  - 실제 URL로 검색 테스트
  - SSE 스트리밍 테스트
  - 에러 케이스 테스트
- [ ] 성능 테스트
  - 동시 사용자 테스트 (5명)
  - 응답 시간 측정
- [ ] README.md 업데이트
  - 프로젝트 설명
  - 기술 스택
  - 로컬 실행 방법
  - 배포 방법
  - 스크린샷
- [ ] 포트폴리오용 문서 정리
  - 아키텍처 설명
  - 주요 기술적 결정
  - 트러블슈팅 경험

**완료 기준**
- 프로덕션에서 모든 기능 동작
- README 완성
- 데모 가능한 상태

---

## 체크리스트

```
[ ] P5-1: Langfuse 설정 및 연동
[ ] P5-2: 프로덕션 Docker 설정
[ ] P5-3: AWS EC2 인스턴스 설정
[ ] P5-4: 도메인 및 HTTPS 설정 (선택)
[ ] P5-5: GitHub Actions CI/CD 파이프라인
[ ] P5-6: 로깅 및 에러 추적
[ ] P5-7: 헬스체크 및 모니터링
[ ] P5-8: 최종 테스트 및 문서화
────────────────────────────────────────
✅ 데모: 실제 URL 접속 + 모니터링 대시보드
```

---

## 예상 트러블슈팅

| 문제 | 해결 방법 |
|------|----------|
| EC2 메모리 부족 | Swap 추가, 인스턴스 업그레이드 |
| Docker 이미지 용량 | Multi-stage build, .dockerignore 최적화 |
| 배포 후 서비스 안 뜸 | 로그 확인, 포트 확인, 헬스체크 |
| SSL 인증서 갱신 실패 | certbot 자동 갱신 cron 확인 |
| CI/CD 실패 | GitHub Actions 로그 확인, secrets 확인 |

---

## 비용 요약

| 항목 | 예상 비용/월 |
|------|-------------|
| EC2 t3.medium | ~$30 |
| OpenAI Embedding | ~$5 (1만 공고 기준) |
| Langfuse Cloud | 무료 (50K/월 이내) |
| 도메인 (선택) | ~$10/년 |
| **총계** | **~$35-40/월** |

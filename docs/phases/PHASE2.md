# Phase 2: 실제 크롤링 연동

**목표**: 검색 → 실제 사람인/잡코리아 크롤링 → 결과 표시
**상태**: ✅ 완료
**기술 스택**: +Playwright, Django REST Framework

---

## 구현 완료 항목

### 1. 크롤러
- `crawlers/saramin.py`: 사람인 크롤러
- `crawlers/jobkorea.py`: 잡코리아 크롤러
- `crawlers/base.py`: BaseCrawler 추상 클래스
- Playwright headless 브라우저

### 2. 안정성 레이어
- tenacity: 재시도 로직 (exponential backoff)
- aiolimiter: 요청 간격 제어
- User-Agent 로테이션
- 차단 감지 (CAPTCHA, 로그인 요구)

### 3. LangGraph 워크플로우 확장
- `agent/nodes/plan.py`: 검색 전략 수립
- `agent/nodes/execute.py`: 크롤러 실행
- `agent/nodes/synthesize.py`: 결과 요약

### 4. API
- DRF APIView로 리팩토링
- 응답 구조 개선 (results, total_count, search_time_ms)
- Serializer 적용

### 5. 웹 UI
- 결과 카드 컴포넌트
- 로딩 스피너
- 에러 메시지 표시

---

## 체크리스트

- [x] P2-0: Django REST Framework 도입
- [x] P2-1: Playwright 환경 설정
- [x] P2-2: 사람인 크롤러 구현
- [x] P2-3: 크롤링 안정성 레이어 추가
- [x] P2-4: LangGraph 워크플로우 확장
- [x] P2-5: API 응답 구조 개선
- [x] P2-6: 웹 UI 개선 (결과 카드)
- [x] P2-7: 로딩 상태 UI
- [x] P2-8: 기본 에러 처리 UI
- [x] P2-9: 통합 테스트 및 안정화

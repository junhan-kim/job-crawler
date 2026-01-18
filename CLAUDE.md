# 코드 컨벤션

## 주석
- docstring OK (함수/클래스/모듈 설명)
- `#` 인라인 주석 금지
- 주석 대신: 명확한 네이밍, 함수 분리로 의도 표현

## docstring
- 한글로 작성
- 모듈 docstring: 파일 역할 간단 설명 (예: `"""사람인 크롤러 구현."""`)
- 클래스/함수 docstring: 필요시 Args, Returns, Raises 포함

## 상수
- 매직넘버 금지 → 상수로 추출
- 고정 문자열 → 상수로 추출
- 상수명은 UPPER_SNAKE_CASE

## 네이밍
- 변수/함수: snake_case
- 클래스: PascalCase
- 상수: UPPER_SNAKE_CASE
- 의미가 명확하도록 (약어 최소화)
- 한 글자 변수명 금지 (예: `i`, `x`, `e` 등)

## 타입
- 문자열 등 고정값 → Enum 사용 (StrEnum 등)
- 타입 힌트 필수
- 데이터는 dict 대신 Pydantic 모델 사용 (코드만 보고 필드 추적 가능)
- LangGraph state처럼 dict 강제되는 경우, 노드 진입 시 즉시 모델로 변환

## 파일 구조
- 모델/타입 정의는 별도 파일로 분리 (예: models.py)
- 한 파일에 여러 책임 넣지 않기

## 언어
- 로그 메시지: 영어
- 에러 메시지: 영어
- docstring: 한글
- UI 텍스트 (사용자 facing): 한글

## 테스트
- HTTP 상태 코드는 매직넘버 대신 `http.HTTPStatus` 사용
  - 예: `HTTPStatus.OK`, `HTTPStatus.BAD_REQUEST`

## 커밋 메시지
- 영어로 한 줄 작성
- 접두사 필수: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:` 등
- 커밋을 직접 수행하지 말고 커밋 메시지만 작성

## 작업 진행
- Phase 체크리스트 항목은 **한 번에 하나만** 수행
- 각 항목 완료 후 사용자 검토 대기
- 여러 항목을 한꺼번에 작성하지 않음

## 기타
- 불필요한 코드 삭제 (주석처리 X)
- 한 함수는 한 가지 일만
- 테스트 후 생성된 임시 파일 삭제
- 과한 방어 로직 금지 (truncate, fallback 등 불필요한 안전장치 넣지 말 것)
- 코드 한 줄 한 줄에 근거를 설명할 수 있어야 함 (행동 전에 먼저 생각하고 설명)

class ParsePrompt:
    TEMPLATE = """사용자의 채용 검색 요청에서 정보를 추출하세요.

규칙:
- role: 문자열 또는 null
- experience: 숫자 또는 null
- skills: 문자열 배열 (반드시 배열, 예: ["Python", "Django"])
- location: 문자열 또는 null
- 언급되지 않은 항목은 null 또는 빈 배열

JSON 형식으로만 응답하세요:
{schema}

사용자 입력: {query}

JSON:"""

    SCHEMA = '{"role": "백엔드", "experience": 3, "skills": ["Python", "Django"], "location": "서울"}'

    @classmethod
    def format(cls, query: str) -> str:
        return cls.TEMPLATE.format(schema=cls.SCHEMA, query=query)

class ParsePrompt:
    """채용 검색 쿼리 파싱 프롬프트."""

    TEMPLATE = """Extract ONLY mentioned info. Output JSON.

Examples:
Q: "python 서울 3년" -> {{"role": null, "experience": 3, "skills": ["Python"], "location": "서울"}}
Q: "백엔드 개발자" -> {{"role": "backend", "experience": null, "skills": [], "location": null}}
Q: "react 프론트엔드" -> {{"role": "frontend", "experience": null, "skills": ["React"], "location": null}}
Q: "spring boot java 5년" -> {{"role": null, "experience": 5, "skills": ["Spring Boot", "Java"], "location": null}}
Q: "개발자" -> {{"role": "developer", "experience": null, "skills": [], "location": null}}
Q: "AI 엔지니어" -> {{"role": "developer", "experience": null, "skills": ["AI"], "location": null}}
Q: "데이터 분석가" -> {{"role": "developer", "experience": null, "skills": [], "location": null}}

role must be: backend, frontend, developer, or null
Do NOT add skills not in the query.

Q: "{query}" ->"""

    @classmethod
    def format(cls, query: str) -> str:
        """쿼리를 포함한 프롬프트 생성."""
        return cls.TEMPLATE.format(query=query)

class ParsePrompt:
    """채용 검색 쿼리 파싱 프롬프트."""

    TEMPLATE = """Extract job search info from the user query. Output JSON only.

Rules:
- role: string or null (job position like backend, frontend, developer)
- experience: number or null (years of experience, extract number only)
- skills: array of strings (technologies/languages mentioned, e.g. ["Python"])
- location: string or null (city/region in Korean)
- If not mentioned, use null or empty array []

Examples:
- "백엔드 3년차" -> {{"role": "백엔드", "experience": 3, "skills": [], "location": null}}
- "python 개발자" -> {{"role": "개발자", "experience": null, "skills": ["Python"], "location": null}}
- "서울 react 프론트엔드" -> {{"role": "프론트엔드", "experience": null, "skills": ["React"], "location": "서울"}}
- "java spring 5년" -> {{"role": null, "experience": 5, "skills": ["Java", "Spring"], "location": null}}

User query: {query}

JSON:"""

    @classmethod
    def format(cls, query: str) -> str:
        """쿼리를 포함한 프롬프트 생성."""
        return cls.TEMPLATE.format(query=query)

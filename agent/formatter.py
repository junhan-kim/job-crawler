from .models import ParsedQuery


class ResponseFormatter:
    HEADER = "검색 조건을 분석했습니다:"
    EMPTY = "- 조건을 명확히 파악하지 못했습니다."
    EXPERIENCE_SUFFIX = "년"

    @classmethod
    def format(cls, query: ParsedQuery) -> str:
        parts = [cls.HEADER]

        if query.role:
            parts.append(f"- 직무: {query.role}")
        if query.experience:
            parts.append(f"- 경력: {query.experience}{cls.EXPERIENCE_SUFFIX}")
        if query.skills:
            parts.append(f"- 스킬: {', '.join(query.skills)}")
        if query.location:
            parts.append(f"- 지역: {query.location}")

        if len(parts) == 1:
            parts.append(cls.EMPTY)

        return "\n".join(parts)

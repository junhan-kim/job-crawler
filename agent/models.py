from pydantic import BaseModel, Field


class ParsedQuery(BaseModel):
    """사용자의 채용 검색 요청에서 추출된 정보"""
    role: str | None = Field(None, description="직무 (예: 백엔드, 프론트엔드)")
    experience: int | None = Field(None, description="경력 연차 숫자")
    skills: list[str] = Field(default_factory=list, description="기술 스택 목록")
    location: str | None = Field(None, description="근무 지역")

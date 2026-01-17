"""크롤러 데이터 모델."""

from enum import StrEnum

from pydantic import BaseModel, Field


class JobSource(StrEnum):
    """채용 사이트 소스."""

    SARAMIN = "saramin"
    JOBKOREA = "jobkorea"


class JobPosting(BaseModel):
    """채용 공고 데이터 모델."""

    title: str
    company: str
    location: str
    url: str
    source: JobSource
    experience: str | None = None
    salary: str | None = None
    skills: list[str] = Field(default_factory=list)
    deadline: str | None = None
    posted_at: str | None = None

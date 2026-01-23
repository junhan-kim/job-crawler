"""크롤러 데이터 모델."""

import re
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field


class JobSource(StrEnum):
    """채용 사이트 소스."""

    SARAMIN = "saramin"
    JOBKOREA = "jobkorea"


class SearchFilters(BaseModel):
    """검색 필터 조건."""

    EXPERIENCE_YEAR_PATTERN: ClassVar[re.Pattern] = re.compile(r"(\d+)년")

    experience: int | None = None
    location: str | None = None

    @classmethod
    def matches_experience(cls, job_experience: str | None, user_experience: int) -> bool:
        """
        사용자 경력과 채용 공고 경력 조건 매칭.

        - 신입/경력무관/빈값: 모든 경력에 매칭
        - "경력 N년↑": 사용자 경력 >= N 이면 매칭
        """
        if not job_experience:
            return True

        if "신입" in job_experience or "무관" in job_experience:
            return True

        match = cls.EXPERIENCE_YEAR_PATTERN.search(job_experience)
        if match:
            required_years = int(match.group(1))
            return user_experience >= required_years

        return True


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

    def to_django_defaults(self) -> dict:
        """Django ORM aupdate_or_create의 defaults 딕셔너리로 변환."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "experience": self.experience,
            "salary": self.salary,
            "skills": self.skills,
            "is_active": True,
        }

"""pytest 설정."""

import os
import sys

import django
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


@pytest.fixture
def sample_job_posting():
    """테스트용 채용공고 데이터."""
    return {
        "title": "백엔드 개발자",
        "company": "테스트회사",
        "location": "서울 강남구",
        "url": "https://example.com/job/1",
        "source": "saramin",
        "experience": "3년",
        "skills": ["Python", "Django"],
        "deadline": "2025-02-01",
    }


@pytest.fixture
def sample_parsed_conditions():
    """테스트용 파싱 조건."""
    return {
        "role": "백엔드",
        "experience": 3,
        "skills": ["Python", "Django"],
        "location": "서울",
    }

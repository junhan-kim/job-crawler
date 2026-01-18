"""JobService 테스트."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from crawlers.models import JobPosting as CrawlerJobPosting
from crawlers.models import JobSource


class TestJobService:
    """JobService 테스트."""

    def test_generate_source_id_from_url(self):
        """URL 기반 source_id 생성 테스트."""
        from apps.jobs.services import JobService

        service = JobService()
        job = CrawlerJobPosting(
            title="테스트",
            company="테스트 회사",
            location="서울",
            url="https://example.com/jobs/123",
            source=JobSource.SARAMIN,
        )

        source_id = service._generate_source_id(job)

        assert len(source_id) == 16
        assert source_id == service._generate_source_id(job)

    def test_generate_source_id_different_url(self):
        """다른 URL은 다른 source_id 생성."""
        from apps.jobs.services import JobService

        service = JobService()
        job1 = CrawlerJobPosting(
            title="테스트",
            company="테스트 회사",
            location="서울",
            url="https://example.com/jobs/123",
            source=JobSource.SARAMIN,
        )
        job2 = CrawlerJobPosting(
            title="테스트",
            company="테스트 회사",
            location="서울",
            url="https://example.com/jobs/456",
            source=JobSource.SARAMIN,
        )

        assert service._generate_source_id(job1) != service._generate_source_id(job2)

    @pytest.mark.django_db
    async def test_save_job_creates_new(self):
        """새 채용공고 저장 테스트."""
        from apps.jobs.services import JobService

        service = JobService()
        test_id = uuid.uuid4().hex[:8]
        job_input = CrawlerJobPosting(
            title="Python 개발자",
            company="테스트 회사",
            location="서울",
            url=f"https://example.com/job/{test_id}",
            source=JobSource.SARAMIN,
            skills=["Python", "Django"],
        )

        with patch.object(service, "_generate_embedding", new_callable=AsyncMock):
            job, created = await service.save_job(job_input)

        assert created is True
        assert job.title == "Python 개발자"
        assert job.company == "테스트 회사"
        assert job.source == "saramin"
        assert "Python" in job.skills

    @pytest.mark.django_db
    async def test_save_job_updates_existing(self):
        """기존 채용공고 업데이트 테스트."""
        from apps.jobs.services import JobService

        service = JobService()
        test_id = uuid.uuid4().hex[:8]

        job_input1 = CrawlerJobPosting(
            title="Python 개발자",
            company="테스트 회사",
            location="서울",
            url=f"https://example.com/job/update/{test_id}",
            source=JobSource.SARAMIN,
            skills=["Python"],
        )

        with patch.object(service, "_generate_embedding", new_callable=AsyncMock):
            job1, created1 = await service.save_job(job_input1)
            assert created1 is True

            job_input2 = CrawlerJobPosting(
                title="Python 개발자",
                company="테스트 회사",
                location="서울",
                url=f"https://example.com/job/update/{test_id}",
                source=JobSource.SARAMIN,
                skills=["Python", "Django"],
            )
            job2, created2 = await service.save_job(job_input2)

        assert created2 is False
        assert job1.id == job2.id
        assert "Django" in job2.skills

    @pytest.mark.django_db
    async def test_save_batch(self):
        """배치 저장 테스트."""
        from apps.jobs.services import JobService

        service = JobService()
        batch_id = uuid.uuid4().hex[:8]
        jobs = [
            CrawlerJobPosting(
                title=f"개발자 {i}",
                company=f"회사 {i}",
                location="서울",
                url=f"https://example.com/batch/{batch_id}/job/{i}",
                source=JobSource.SARAMIN,
            )
            for i in range(5)
        ]

        with patch.object(service, "_generate_embedding", new_callable=AsyncMock):
            result = await service.save_batch(jobs)

        assert result.created == 5
        assert result.updated == 0

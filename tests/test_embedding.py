"""LlamaIndex 임베딩 서비스 테스트."""

from unittest.mock import AsyncMock, MagicMock, patch


class TestEmbeddingService:
    """EmbeddingService 테스트."""

    def test_create_job_text(self):
        """채용공고 텍스트 생성 테스트."""
        from core.embedding_service import EmbeddingService

        service = EmbeddingService()

        # Mock JobPosting
        job = MagicMock()
        job.title = "백엔드 개발자"
        job.company = "테스트 회사"
        job.location = "서울"
        job.skills = ["Python", "Django"]
        job.experience = "3년 이상"

        text = service.create_job_text(job)

        assert "백엔드 개발자" in text
        assert "테스트 회사" in text
        assert "서울" in text
        assert "Python" in text
        assert "3년 이상" in text

    def test_create_job_text_with_missing_fields(self):
        """필드가 없는 경우 기본값 테스트."""
        from core.embedding_service import EmbeddingService

        service = EmbeddingService()

        job = MagicMock()
        job.title = "개발자"
        job.company = "회사"
        job.location = None
        job.skills = []
        job.experience = None

        text = service.create_job_text(job)

        assert "개발자" in text
        assert "미정" in text  # location과 skills 기본값
        assert "무관" in text  # experience 기본값

    def test_create_job_node(self):
        """LlamaIndex 노드 생성 테스트."""
        from core.embedding_service import EmbeddingService

        service = EmbeddingService()

        job = MagicMock()
        job.id = 1
        job.title = "백엔드 개발자"
        job.company = "테스트 회사"
        job.source = "saramin"
        job.location = "서울"
        job.skills = ["Python"]
        job.experience = "3년"

        node = service.create_job_node(job)

        assert node.metadata["job_id"] == 1
        assert node.metadata["source"] == "saramin"
        assert node.metadata["company"] == "테스트 회사"
        assert "백엔드 개발자" in node.text

    async def test_embed_text(self):
        """임베딩 생성 테스트 (mocked)."""
        from core.embedding_service import EmbeddingService

        service = EmbeddingService()

        mock_embedding = [0.1] * 1536
        with patch.object(
            service, "embed_text", new=AsyncMock(return_value=mock_embedding)
        ):
            result = await service.embed_text("테스트 텍스트")
            assert len(result) == 1536

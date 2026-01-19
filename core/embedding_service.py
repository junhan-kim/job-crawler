"""LlamaIndex 기반 임베딩 서비스."""

from llama_index.core import Settings
from llama_index.core.schema import TextNode

from apps.jobs.models import JobPosting


class EmbeddingService:
    """LlamaIndex 기반 임베딩 서비스."""

    async def embed_text(self, text: str) -> list[float]:
        """단일 텍스트 임베딩."""
        return await Settings.embed_model.aget_text_embedding(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """배치 임베딩."""
        return await Settings.embed_model.aget_text_embedding_batch(texts)

    def create_job_text(self, job: JobPosting) -> str:
        """채용공고를 임베딩할 텍스트로 변환."""
        parts = [job.title]

        if job.company:
            parts.append(job.company)

        if job.skills:
            parts.append(", ".join(job.skills))

        if job.location:
            parts.append(job.location)

        if job.experience:
            parts.append(job.experience)

        return " ".join(parts)

    def create_job_node(self, job: JobPosting) -> TextNode:
        """채용공고를 LlamaIndex 노드로 변환."""
        text = self.create_job_text(job)
        return TextNode(
            text=text,
            metadata={
                "job_id": job.id,
                "source": job.source,
                "company": job.company,
                "location": job.location,
            },
        )

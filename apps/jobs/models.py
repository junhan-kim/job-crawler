from django.conf import settings
from django.db import models
from pgvector.django import VectorField


class JobPosting(models.Model):
    """채용공고 모델."""

    # 기본 정보
    source = models.CharField(max_length=50)  # saramin, wanted, jobkorea
    source_id = models.CharField(max_length=100)  # 원본 사이트 ID
    url = models.URLField()

    # 공고 내용
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=100, null=True, blank=True)
    salary = models.CharField(max_length=100, null=True, blank=True)
    experience = models.CharField(max_length=50, null=True, blank=True)
    skills = models.JSONField(default=list)
    description = models.TextField(null=True, blank=True)

    # 벡터 임베딩 (pgvector)
    embedding = VectorField(dimensions=settings.EMBEDDING_DIMENSIONS, null=True, blank=True)

    # 메타 정보
    posted_at = models.DateTimeField(null=True, blank=True)
    crawled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["source", "source_id"]
        indexes = [
            models.Index(fields=["-crawled_at"]),
        ]

    def __str__(self):
        return f"[{self.source}] {self.company} - {self.title}"

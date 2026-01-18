from django.db import models


class SearchHistory(models.Model):
    """검색 히스토리 모델."""

    query = models.CharField(max_length=500)
    parsed_conditions = models.JSONField(default=dict)
    result_count = models.IntegerField(default=0)
    search_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # 나중에 user FK 추가: user = models.ForeignKey(User, ...)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Search History"
        verbose_name_plural = "Search Histories"
        indexes = [
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.query} ({self.result_count}건)"

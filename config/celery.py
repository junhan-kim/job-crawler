"""Celery 설정."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("job_crawler")

# Django settings에서 CELERY_ 접두사로 시작하는 설정 로드
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """디버그 태스크."""
    print(f"Request: {self.request!r}")

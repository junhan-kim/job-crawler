import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.jobs"
    verbose_name = "채용공고"

    def ready(self):
        if not os.getenv("DB_HOST"):
            return

        try:
            from core.llama_index_setup import init_llama_index
            from core.redis_cache import init_llm_cache

            init_llama_index()
            init_llm_cache()
        except ImportError as error:
            logger.warning(f"Failed to initialize LlamaIndex/Redis: {error}")

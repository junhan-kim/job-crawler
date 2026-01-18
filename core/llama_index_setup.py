"""LlamaIndex 전역 설정."""

from django.conf import settings as django_settings
from llama_index.core import Settings
from llama_index.embeddings.ollama import OllamaEmbedding

from core.constants import EMBEDDING_MODEL

_initialized = False


def init_llama_index():
    """LlamaIndex 전역 설정 초기화."""
    global _initialized
    if _initialized:
        return

    Settings.embed_model = OllamaEmbedding(
        model_name=EMBEDDING_MODEL,
        base_url=django_settings.OLLAMA_HOST,
    )
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
    _initialized = True

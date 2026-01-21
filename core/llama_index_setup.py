"""LlamaIndex 전역 설정."""

from django.conf import settings
from llama_index.core import Settings
from llama_index.embeddings.ollama import OllamaEmbedding

_initialized = False


def init_llama_index():
    """LlamaIndex 전역 설정 초기화."""
    global _initialized
    if _initialized:
        return

    Settings.embed_model = OllamaEmbedding(
        model_name=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_HOST,
    )
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
    _initialized = True

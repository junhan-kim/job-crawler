import httpx
from django.conf import settings

from .base import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_HOST
        self.timeout = settings.OLLAMA_TIMEOUT

    async def chat(self, prompt: str) -> LLMResponse:
        payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            content = response.json().get("response", "")
            return LLMResponse(content=content, model=self.model)

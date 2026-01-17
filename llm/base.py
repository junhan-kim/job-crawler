from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str


class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, prompt: str) -> LLMResponse:
        pass

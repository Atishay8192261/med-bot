from __future__ import annotations
import os
from typing import Optional
from app.prompts import LLM_SYSTEM_PROMPT, LLM_USER_TEMPLATE


class LLMService:
    def rewrite(self, answer: str) -> str:  # pragma: no cover
        return answer


def build_llm_service() -> Optional[LLMService]:
    enabled = os.getenv("LLM_ENABLED", "0") == "1"
    if not enabled:
        return None
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "openai":
        return _OpenAIService()
    return None


class _OpenAIService(LLMService):
    def __init__(self):
        from openai import OpenAI  # lazy import
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_ENABLED=1 but OPENAI_API_KEY is missing")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "600"))

    def rewrite(self, answer: str) -> str:  # pragma: no cover runtime path
        prompt = LLM_USER_TEMPLATE.format(answer=answer)
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        out = resp.choices[0].message.content.strip()
        if not out or len(out.split()) < 5:
            return answer
        if "educational" not in out.lower() and "medical advice" not in out.lower():
            return answer
        return out

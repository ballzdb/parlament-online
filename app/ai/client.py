from __future__ import annotations

import os


class AIClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def respond(self, prompt: str) -> str:
        if not self.is_available():
            return "Не вдалося підключити AI-помічника. Спробуйте ще раз пізніше."
        return (
            "AI-помічник наразі недоступний. "
            "Доступні інструкції: зареєструватися, подати ідею, перевірити статус подання."
        )

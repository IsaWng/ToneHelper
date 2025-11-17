"""Business logic for rewrite operations."""

from __future__ import annotations

from fastapi import HTTPException

from .config import USE_OPENAI
from .mock_engine import mock_generate
from .models import RewriteIn, RewriteOut
from .openai_provider import generate_via_openai
from .text_utils import detect_lang, sanitize


class RewriteService:
    """Coordinates sanitization, language detection, and generation."""

    def __init__(self, use_openai: bool = USE_OPENAI) -> None:
        self.use_openai = use_openai

    async def rewrite(self, payload: RewriteIn) -> RewriteOut:
        text = sanitize(payload.text)
        if not text:
            raise HTTPException(400, "empty text after sanitize")

        lang = payload.lang if payload.lang != "auto" else detect_lang(text)

        if self.use_openai:
            try:
                rewrites = await generate_via_openai(text, payload.tone, lang)
                if rewrites:
                    return RewriteOut(rewrites=rewrites)
            except Exception as exc:
                # Keep API resilient by logging and falling back to mock.
                print("OpenAI error:", repr(exc))

        rewrites = mock_generate(text, payload.tone, lang)
        return RewriteOut(rewrites=rewrites)

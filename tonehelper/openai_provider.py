"""Thin wrapper around the OpenAI Responses API."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import List

from .config import OPENAI_TIMEOUT
from .models import Candidate
from .mock_engine import mock_generate


@lru_cache()
def _get_client():
    from openai import OpenAI

    return OpenAI(timeout=OPENAI_TIMEOUT)


async def generate_via_openai(text: str, tone: str, lang: str) -> List[Candidate]:
    """Call Responses API and normalize into Candidate objects."""
    client = _get_client()

    instructions = (
        "你是礼貌与语域转换专家。目标：不改变事实和立场的前提下，根据语气与语言改写。"
        "输出 JSON 对象，形如 {\"rewrites\":[{\"text\":\"...\",\"reason\":\"...\"},…]}；"
        "不要输出除 JSON 以外的任何内容。每个 text 1-2 句。reason 不超过 20 字。"
    )
    prompt = f"原文: {text}\n语气: {tone}\n语言: {lang}"

    response = client.with_options(timeout=OPENAI_TIMEOUT).responses.create(
        model="o3",
        instructions=instructions,
        input=prompt,
        service_tier="flex",
    )

    result_text = response.output_text.strip()
    try:
        data = json.loads(result_text)
        rewrites = [Candidate(**item) for item in data.get("rewrites", [])]
        while len(rewrites) < 3:
            rewrites.append(Candidate(text=text, reason="fallback"))
    except Exception:
        rewrites = mock_generate(text, tone, lang)
    return rewrites

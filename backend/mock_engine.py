"""Mock rewrite engine for offline experience."""

from __future__ import annotations

from typing import List

from .models import Candidate
from .text_utils import capitalize, lower_first, lower_first_es


def mock_generate(text: str, tone: str, lang: str) -> List[Candidate]:
    if lang == "zh":
        return mock_zh(text, tone)
    if lang == "es":
        return mock_es(text, tone)
    return mock_en(text, tone)


def mock_zh(text: str, tone: str) -> List[Candidate]:
    base = text
    if tone == "softer":
        opts = [
            (f"请{base}，谢谢理解。", "语气缓和"),
            (f"如果方便的话，{base}，感谢配合。", "保留边界"),
            (f"麻烦{base}，先行致谢。", "减少冲突"),
        ]
    elif tone == "colloquial":
        opts = [
            (f"嗨，{base}，可以吗？", "更口语"),
            (f"咱们{base}，行不行？", "更自然"),
            (f"要不就{base}，怎么样？", "更日常"),
        ]
    else:
        cleaned = _strip_polite_suffix(base)
        opts = [
            (f"{cleaned}。", "更简短"),
            (f"请{cleaned}。", "核心保留"),
            (f"麻烦{cleaned}。", "去冗余"),
        ]
    return [Candidate(text=a, reason=b) for a, b in opts]


def mock_en(text: str, tone: str) -> List[Candidate]:
    trimmed = text.rstrip(". ")
    if tone == "softer":
        opts = [
            (f"Could we {lower_first(trimmed)}? Thanks for understanding.", "softer tone"),
            (f"If possible, could we {lower_first(trimmed)}?", "hedging"),
            (f"I’d appreciate it if we could {lower_first(trimmed)}.", "polite request"),
        ]
    elif tone == "colloquial":
        opts = [
            (f"Hey, can we {lower_first(trimmed)}?", "casual"),
            (f"Mind if we {lower_first(trimmed)}?", "spoken"),
            (f"Let’s {lower_first(trimmed)}, ok?", "friendly"),
        ]
    else:
        opts = [
            (f"Please {lower_first(trimmed)}.", "concise"),
            (f"Let’s {lower_first(trimmed)}.", "brief"),
            (f"{capitalize(trimmed)}.", "shortened"),
        ]
    return [Candidate(text=a, reason=b) for a, b in opts]


def mock_es(text: str, tone: str) -> List[Candidate]:
    trimmed = text.rstrip(". ")
    if tone == "softer":
        opts = [
            (f"¿Podríamos {lower_first_es(trimmed)}? Gracias por la comprensión.", "tono suave"),
            (f"Si es posible, ¿podemos {lower_first_es(trimmed)}?", "condicional"),
            (f"Te agradecería si {lower_first_es(trimmed)}.", "cortesía"),
        ]
    elif tone == "colloquial":
        opts = [
            (f"Oye, ¿podemos {lower_first_es(trimmed)}?", "coloquial"),
            (f"¿Te va si {lower_first_es(trimmed)}?", "hablado"),
            (f"Mejor {lower_first_es(trimmed)}, ¿vale?", "directo amable"),
        ]
    else:
        opts = [
            (f"Por favor, {lower_first_es(trimmed)}.", "conciso"),
            (f"{capitalize(trimmed)}.", "breve"),
            (f"Procedamos a {lower_first_es(trimmed)}.", "formal breve"),
        ]
    return [Candidate(text=a, reason=b) for a, b in opts]


def _strip_polite_suffix(text: str) -> str:
    import re

    cleaned = re.sub(r"(请问|麻烦)", "请", text)
    cleaned = re.sub(r"，?谢谢(理解|配合)?。?$", "", cleaned)
    cleaned = re.sub(r"[。.!?]$", "", cleaned)
    return cleaned

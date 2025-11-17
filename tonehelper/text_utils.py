"""Utility helpers for text cleanup and inference."""

from __future__ import annotations

import re


def sanitize(value: str) -> str:
    """Strip control chars, collapse whitespace and clip to 300 chars."""
    value = re.sub(r"[\u0000-\u001f]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:300]


def detect_lang(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[ñáéíóúü¿¡]", text, re.I) or re.search(
        r"\b(gracias|hola|vale|por favor|perdón)\b", text, re.I
    ):
        return "es"
    return "en"


def lower_first(text: str) -> str:
    text = re.sub(r"^(to\s+)?", "", text, flags=re.I)
    return re.sub(r"^([A-Z])", lambda m: m.group(1).lower(), text)


def lower_first_es(text: str) -> str:
    return re.sub(r"^([A-ZÁÉÍÓÚÑ])", lambda m: m.group(1).lower(), text)


def capitalize(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    return text[0].upper() + text[1:]

"""Pydantic schemas for ToneHelper."""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


class RewriteIn(BaseModel):
    text: str = Field(min_length=20, max_length=300)
    tone: Literal["softer", "colloquial", "concise"]
    lang: Literal["auto", "zh", "en", "es"] = "auto"


class Candidate(BaseModel):
    text: str
    reason: str


class RewriteOut(BaseModel):
    rewrites: List[Candidate]

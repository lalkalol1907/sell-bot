"""Typed result for message processing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProcessResult:
    matched: bool
    reason: str = ""
    lead_id: int = 0
    product_id: int = 0
    product_title: str = ""
    score: float = 0.0
    level: str = ""

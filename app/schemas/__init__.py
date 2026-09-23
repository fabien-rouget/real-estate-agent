"""Schemas package."""

from app.schemas.ademe import AdemeDpeRecord
from app.schemas.listing import ExtractedCriteria, ImmoAnalysisResult, ProbableAddress

__all__ = [
    "AdemeDpeRecord",
    "ExtractedCriteria",
    "ImmoAnalysisResult",
    "ProbableAddress",
]

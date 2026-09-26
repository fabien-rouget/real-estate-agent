"""Domain-organized Pydantic schemas for the Real Estate Reconciliation Agent.

Structure by pipeline stage:
- listing.py         : Step 1 - ListingExtractedCriteria (Leboncoin / raw listing extraction)
- ademe.py           : Step 2 - AdemeDpeRecord & AdemeAddressCandidate (ADEME open data & scored matches)
- market.py          : Step 3 - DvfComparableSale & CadastralAndMarketValuation (Parcellai.re MCP enrichment)
- analysis_report.py : Step 4 - PropertyAnalysisReport (Final structured output of the ADK agent)
"""

from app.schemas.ademe import AdemeAddressCandidate, AdemeDpeRecord
from app.schemas.analysis_report import PropertyAnalysisReport
from app.schemas.listing import ListingExtractedCriteria
from app.schemas.market import CadastralAndMarketValuation, DvfComparableSale

__all__ = [
    "AdemeAddressCandidate",
    "AdemeDpeRecord",
    "CadastralAndMarketValuation",
    "DvfComparableSale",
    "ListingExtractedCriteria",
    "PropertyAnalysisReport",
]

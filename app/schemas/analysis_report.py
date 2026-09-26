"""Pydantic root schema for the final structured report returned by the ADK Agent (Step 4)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ademe import AdemeAddressCandidate
from app.schemas.listing import ListingExtractedCriteria
from app.schemas.market import CadastralAndMarketValuation


class PropertyAnalysisReport(BaseModel):
    """Final validated analysis report returned by the real estate AI agent."""

    model_config = ConfigDict(populate_by_name=True)

    property_title: str = Field(
        ...,
        alias="titre_bien",
        description="Normalized descriptive title of the property",
    )
    listed_price: float | None = Field(
        default=None,
        alias="prix_mentionne",
        description="Asking price in euros mentioned in the listing (or null)",
    )
    extracted_criteria: ListingExtractedCriteria = Field(
        ...,
        alias="criteres_extraits",
        description="Key technical criteria extracted from the listing (Step 1)",
    )
    probable_addresses: list[AdemeAddressCandidate] = Field(
        default_factory=list,
        alias="adresses_probables",
        description="Candidate physical addresses matching ADEME DPE records (Step 2)",
    )
    market_analysis: CadastralAndMarketValuation | None = Field(
        default=None,
        alias="analyse_marche_dvf",
        description="Cadastral parcel, DVF comparable sales, and price valuation analysis (Step 3)",
    )
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ...,
        alias="indice_confiance",
        description="Overall confidence rating for address identification",
    )
    summary: str = Field(
        ...,
        alias="synthese",
        description="Concise summary explaining match findings, certainty level, and market price positioning",
    )

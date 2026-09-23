"""Pydantic schemas for extracted listing criteria and structured agent output."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExtractedCriteria(BaseModel):
    """Key technical parameters extracted from the raw property listing."""

    model_config = ConfigDict(populate_by_name=True)

    city: str = Field(
        ...,
        alias="commune",
        description="City or municipality name (e.g., 'Bordeaux')",
    )
    postal_code: str | None = Field(
        default=None,
        alias="code_postal",
        description="5-digit French postal code if explicitly mentioned (or null)",
    )
    surface_sqm: float = Field(
        ...,
        alias="surface_m2",
        description="Living area in square meters (m²)",
    )
    dpe_kwh_sqm_year: float = Field(
        ...,
        alias="dpe_kwh_m2_an",
        description="Energy consumption from DPE rating in kWh/m²/year",
    )
    dpe_date: str | None = Field(
        default=None,
        alias="date_dpe",
        description="Date of DPE completion if stated in the listing (e.g., '24/04/2026' or '2026-04-24')",
    )
    construction_year: int | None = Field(
        default=None,
        alias="annee_construction",
        description="Year of building construction if stated",
    )
    ghg_kg_co2_sqm_year: float | None = Field(
        default=None,
        alias="ges_kg_co2_m2_an",
        description="Greenhouse gas emissions in kg CO2/m²/year",
    )
    energy_rating: str | None = Field(
        default=None,
        alias="etiquette_dpe",
        description="Energy efficiency letter grade (A to G)",
    )
    ghg_rating: str | None = Field(
        default=None,
        alias="etiquette_ges",
        description="Greenhouse gas letter grade (A to G)",
    )
    floor: int | None = Field(
        default=None,
        alias="etage",
        description="Floor number if mentioned in the listing",
    )


class ProbableAddress(BaseModel):
    """Candidate physical address identified via the official ADEME DPE registry."""

    model_config = ConfigDict(populate_by_name=True)

    address: str = Field(
        ...,
        alias="adresse",
        description="Physical street address (number and street name)",
    )
    postal_code: str = Field(
        ...,
        alias="code_postal",
        description="Postal code",
    )
    city: str = Field(
        ...,
        alias="commune",
        description="City name",
    )
    ademe_surface: float = Field(
        ...,
        alias="surface_ademe",
        description="Living area registered in the official DPE (m²)",
    )
    ademe_dpe_kwh: float = Field(
        ...,
        alias="dpe_kwh_ademe",
        description="Energy consumption registered in the official DPE (kWh/m²/year)",
    )
    dpe_date: str | None = Field(
        default=None,
        alias="date_dpe",
        description="Date of the official DPE inspection/certificate",
    )
    matching_level: str = Field(
        ...,
        alias="niveau_matching",
        description="Matching confidence: 'EXACT', 'CLOSE', or 'APPROXIMATE'",
    )
    dpe_id: str | None = Field(
        default=None,
        alias="numero_dpe",
        description="Official ADEME DPE certificate identifier",
    )
    surface_diff: float | None = Field(
        default=None,
        alias="distance_surface",
        description="Absolute difference in surface area (m²)",
    )
    kwh_diff: float | None = Field(
        default=None,
        alias="distance_kwh",
        description="Absolute difference in energy consumption (kWh/m²/year)",
    )
    days_diff: int | None = Field(
        default=None,
        alias="ecart_jours_dpe",
        description="Difference in days between listing DPE date and ADEME certificate date",
    )
    construction_period: str | None = Field(
        default=None,
        alias="periode_construction",
        description="Construction period recorded in ADEME (e.g. '2001-2005')",
    )


class ImmoAnalysisResult(BaseModel):
    """Final validated response returned by the real estate AI agent."""

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
    extracted_criteria: ExtractedCriteria = Field(
        ...,
        alias="criteres_extraits",
        description="Key technical criteria extracted from the listing",
    )
    probable_addresses: list[ProbableAddress] = Field(
        default_factory=list,
        alias="adresses_probables",
        description="Candidate physical addresses matching ADEME records",
    )
    confidence_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ...,
        alias="indice_confiance",
        description="Overall confidence rating for address identification",
    )
    summary: str = Field(
        ...,
        alias="synthese",
        description="Concise summary explaining match findings and certainty level",
    )

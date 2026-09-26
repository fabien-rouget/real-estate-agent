"""Pydantic schema for technical criteria extracted from a real estate listing (Step 1)."""

from pydantic import BaseModel, ConfigDict, Field


class ListingExtractedCriteria(BaseModel):
    """Key technical parameters extracted from the raw property listing (Leboncoin or text)."""

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

"""Pydantic schemas for Leboncoin API deserialization and extracted listing criteria (Step 1)."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LeboncoinLocation(BaseModel):
    """Location subset deserialized from the Leboncoin API (ignores heavy GeoJSON features)."""

    model_config = ConfigDict(extra="ignore")

    city: str | None = None
    zipcode: str | None = None
    district: str | None = None
    city_label: str | None = None
    lat: float | None = None
    lng: float | None = None


class LeboncoinAttribute(BaseModel):
    """Single technical attribute (surface, DPE, rooms, etc.) from a Leboncoin ad."""

    model_config = ConfigDict(extra="ignore")

    key: str
    key_label: str | None = None
    value: str | None = None
    value_label: str | None = None


class LeboncoinAdRecord(BaseModel):
    """Raw classified ad deserialized from the Leboncoin API.

    Uses `extra='ignore'` to automatically discard heavy fields (image URL galleries,
    seller tracking metadata, payment options, similar ads) and protect the LLM token budget.
    """

    model_config = ConfigDict(extra="ignore")

    list_id: int | str
    subject: str = ""
    body: str = ""
    price: list[float] | float | None = None
    first_publication_date: str | None = None
    index_date: str | None = None
    location: LeboncoinLocation | None = None
    attributes: list[LeboncoinAttribute] = Field(default_factory=list)

    @property
    def compact_attributes(self) -> dict[str, Any]:
        """Return a flat, readable dictionary of technical attributes for the LLM."""
        return {
            (attr.key_label or attr.key): (attr.value_label or attr.value)
            for attr in self.attributes
            if attr.value or attr.value_label
        }


class ListingExtractedCriteria(BaseModel):
    """Key technical parameters extracted by the agent from the property listing."""

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

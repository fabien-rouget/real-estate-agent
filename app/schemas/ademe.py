"""Pydantic model for deserializing raw records from the official ADEME DPE registry."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AdemeDpeRecord(BaseModel):
    """Strongly typed DTO representing an official DPE record from data.ademe.fr."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    dpe_id: str = Field(
        default="",
        alias="numero_dpe",
        description="Official unique DPE certificate identifier",
    )
    address: str | None = Field(
        default=None,
        alias="adresse_ban",
        description="Standardized BAN street address",
    )
    address_raw: str | None = Field(
        default=None,
        alias="adresse_brut",
        description="Raw address as entered by the certified inspector",
    )
    postal_code: str = Field(
        default="",
        alias="code_postal_ban",
        description="5-digit postal code",
    )
    city: str = Field(
        default="Unknown",
        alias="nom_commune_ban",
        description="Municipality name",
    )
    surface_sqm: float = Field(
        ...,
        alias="surface_habitable_logement",
        description="Certified living area in square meters",
    )
    dpe_kwh_sqm_year: float = Field(
        ...,
        alias="conso_5_usages_par_m2_ep",
        description="Primary energy consumption in kWh/m²/year",
    )
    ghg_kg_co2_sqm_year: float | None = Field(
        default=None,
        alias="emission_ges_5_usages_par_m2",
        description="Greenhouse gas emissions in kg CO2/m²/year",
    )
    dpe_date: str | None = Field(
        default=None,
        alias="date_etablissement_dpe",
        description="Official date of DPE issuance (YYYY-MM-DD)",
    )
    construction_period: str | None = Field(
        default=None,
        alias="periode_construction",
        description="Construction period (e.g. '2001-2005', 'avant 1948')",
    )
    energy_rating: str | None = Field(
        default=None,
        validation_alias=AliasChoices("etiquette_dpe", "classe_consommation_energie"),
        description="Energy rating letter (A to G)",
    )
    ghg_rating: str | None = Field(
        default=None,
        validation_alias=AliasChoices("etiquette_ges", "classe_estimation_ges"),
        description="GHG rating letter (A to G)",
    )

    @property
    def resolved_address(self) -> str:
        """Returns the best available street address string."""
        return (self.address or self.address_raw or "Address not specified").strip()

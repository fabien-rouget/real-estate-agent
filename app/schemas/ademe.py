"""Pydantic models for the French ADEME DPE registry (Step 2: Raw records & Scored candidates)."""

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AdemeDpeRecord(BaseModel):
    """Raw DPE certificate record deserialized from the official data.ademe.fr API."""

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
    address_complement: str | None = Field(
        default=None,
        alias="complement_adresse_logement",
        description="Address complement (building, apartment, floor)",
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
        """Returns the best available street address string, including complement if present."""
        base = (self.address or self.address_raw or "Address not specified").strip()
        if self.address_complement:
            return f"{base}, {self.address_complement.strip()}"
        return base


class AdemeAddressCandidate(BaseModel):
    """Candidate physical address identified and scored via the official ADEME DPE registry."""

    model_config = ConfigDict(populate_by_name=True)

    address: str = Field(
        ...,
        alias="adresse",
        description="Physical street address (including building/apartment complement if available)",
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
    parcel_id: str | None = Field(
        default=None,
        alias="idu_parcelle",
        description="14-character French cadastral parcel identifier (IDU, e.g. '33063000RC0104')",
    )

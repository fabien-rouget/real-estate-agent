"""Pydantic models for Cadastral, DVF Notarial Sales & Market Valuation (Step 3: Parcellai.re MCP)."""

from pydantic import BaseModel, ConfigDict, Field


class DvfComparableSale(BaseModel):
    """Comparable notarial property transaction (DVF) retrieved via Parcellai.re."""

    model_config = ConfigDict(populate_by_name=True)

    sale_date: str = Field(
        ...,
        alias="date_vente",
        description="Date of the notarial transaction (YYYY-MM-DD)",
    )
    price_eur: float = Field(
        ...,
        alias="prix_eur",
        description="Transaction price in euros",
    )
    surface_sqm: float | None = Field(
        default=None,
        alias="surface_m2",
        description="Built living surface area in m²",
    )
    rooms: int | None = Field(
        default=None,
        alias="pieces",
        description="Number of main rooms",
    )
    price_per_sqm: float | None = Field(
        default=None,
        alias="prix_m2",
        description="Price per square meter in euros",
    )
    property_type: str | None = Field(
        default=None,
        alias="type_bien",
        description="Type of property ('appartement', 'maison', etc.)",
    )
    parcel_id: str | None = Field(
        default=None,
        alias="idu_parcelle",
        description="14-character cadastral parcel IDU of the sale",
    )


class CadastralAndMarketValuation(BaseModel):
    """Cadastral parcel details, DVF notarial sales, and price valuation enrichment."""

    model_config = ConfigDict(populate_by_name=True)

    parcel_id: str | None = Field(
        default=None,
        alias="idu_parcelle",
        description="14-character French cadastral parcel identifier (IDU) of the primary candidate address",
    )
    parcel_surface_sqm: float | None = Field(
        default=None,
        alias="surface_parcelle_m2",
        description="Total land surface area of the cadastral parcel in m²",
    )
    estimated_price_eur: float | None = Field(
        default=None,
        alias="prix_estime_eur",
        description="Estimated market value of the property in euros",
    )
    estimated_price_low_eur: float | None = Field(
        default=None,
        alias="fourchette_basse_eur",
        description="Lower bound of the estimated market price range in euros",
    )
    estimated_price_high_eur: float | None = Field(
        default=None,
        alias="fourchette_haute_eur",
        description="Upper bound of the estimated market price range in euros",
    )
    estimated_price_per_sqm: float | None = Field(
        default=None,
        alias="prix_m2_estime_eur",
        description="Estimated market price per m² in euros",
    )
    sector_median_price_per_sqm: float | None = Field(
        default=None,
        alias="prix_m2_median_secteur_eur",
        description="Median price per m² from recent DVF transactions in the surrounding sector",
    )
    listed_vs_estimated_diff_pct: float | None = Field(
        default=None,
        alias="ecart_prix_annonce_estime_pct",
        description="Percentage difference between asking price and estimated market value ((listed - estimated) / estimated * 100)",
    )
    recent_dvf_sales: list[DvfComparableSale] = Field(
        default_factory=list,
        alias="ventes_dvf_comparables",
        description="Recent comparable notarial property sales (DVF) around the identified address",
    )

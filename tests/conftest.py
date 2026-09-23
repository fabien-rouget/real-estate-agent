"""Pytest fixtures and mock data for offline unit testing."""

import pytest

from app.schemas.ademe import AdemeDpeRecord


@pytest.fixture
def sample_ademe_raw_payload():
    """Returns a simulated raw JSON response from the ADEME DataFair API."""
    return {
        "total": 2,
        "results": [
            {
                "numero_dpe": "2133E0580146P",
                "adresse_ban": "101 Rue Prunier 33300 Bordeaux",
                "adresse_brut": "101 Rue Prunier",
                "code_postal_ban": "33300",
                "nom_commune_ban": "Bordeaux",
                "surface_habitable_logement": 79.9,
                "conso_5_usages_par_m2_ep": 159.9,
                "emission_ges_5_usages_par_m2": 24.5,
                "date_etablissement_dpe": "2021-10-27",
                "periode_construction": "2001-2005",
                "classe_consommation_energie": "C",
                "classe_estimation_ges": "C",
                # Simulating noisy extra fields returned by ADEME API
                "deperdition_baies": 123.4,
                "qualite_isolation_enveloppe": "bonne",
                "type_energie_principale_chauffage": "électricité",
            },
            {
                "numero_dpe": "2333E4135419Y",
                "adresse_ban": "17 Cours Balguerie Stuttenberg 33300 Bordeaux",
                "adresse_brut": "17 Cours Balguerie Stuttenberg",
                "code_postal_ban": "33300",
                "nom_commune_ban": "Bordeaux",
                "surface_habitable_logement": 89.1,
                "conso_5_usages_par_m2_ep": 204.1,
                "emission_ges_5_usages_par_m2": 6.2,
                "date_etablissement_dpe": "2023-12-01",
                "periode_construction": "1989-2000",
                "classe_consommation_energie": "D",
                "classe_estimation_ges": "B",
            },
        ],
    }


@pytest.fixture
def sample_parsed_record():
    """Returns a validated AdemeDpeRecord instance."""
    return AdemeDpeRecord(
        dpe_id="2333E4135419Y",
        address="17 Cours Balguerie Stuttenberg 33300 Bordeaux",
        postal_code="33300",
        city="Bordeaux",
        surface_sqm=89.1,
        dpe_kwh_sqm_year=204.1,
        ghg_kg_co2_sqm_year=6.2,
        dpe_date="2023-12-01",
        construction_period="1989-2000",
        energy_rating="D",
        ghg_rating="B",
    )

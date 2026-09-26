"""Business service layer for extracting ad IDs, fetching Leboncoin listings, and handling graceful failure."""

import logging
import re
from typing import Any

from app.clients.leboncoin_client import LeboncoinClient

logger = logging.getLogger(__name__)

_leboncoin_client = LeboncoinClient()


def _extract_ad_id(url_or_id: str) -> str:
    """Extract numeric ad ID from a Leboncoin URL or raw ID string."""
    clean_input = url_or_id.strip()
    if clean_input.isdigit():
        return clean_input

    match = re.search(r"/(\d+)(?:[/?#]|$)", clean_input)
    if match:
        return match.group(1)

    raise ValueError(f"Could not extract a valid Leboncoin ad ID from '{url_or_id}'.")


def fetch_leboncoin_listing(url_or_id: str) -> dict[str, Any]:
    """Télécharge et structure une annonce immobilière Leboncoin à partir de son URL ou de son identifiant.

    À utiliser dès que l'utilisateur fournit un lien Leboncoin (ex: https://www.leboncoin.fr/ad/ventes_immobilieres/...)
    ou un ID d'annonce pour en extraire les informations techniques.

    Args:
        url_or_id: URL complète ou identifiant numérique de l'annonce Leboncoin.

    Returns:
        Dictionnaire nettoyé de l'annonce (sans les photos/trackers grâce à LeboncoinAdRecord)
        ou un dictionnaire d'erreur explicite en cas d'indisponibilité (Graceful Failure).
    """
    try:
        ad_id = _extract_ad_id(url_or_id)
        ad_record = _leboncoin_client.fetch_ad(ad_id)
        return {
            "status": "OK",
            "list_id": ad_record.list_id,
            "subject": ad_record.subject,
            "body": ad_record.body,
            "price": ad_record.price,
            "location": ad_record.location.model_dump(exclude_none=True) if ad_record.location else None,
            "attributes": ad_record.compact_attributes,
            "first_publication_date": ad_record.first_publication_date,
        }
    except Exception as exc:
        logger.warning("Échec de la récupération de l'annonce Leboncoin '%s': %s", url_or_id, exc)
        return {
            "status": "ERROR",
            "error": (
                f"Impossible de récupérer l'annonce Leboncoin ({exc}). "
                "Indiquez un indice de confiance 'LOW' et demandez à l'utilisateur de vérifier l'URL "
                "ou de copier-coller le texte de l'annonce."
            ),
        }

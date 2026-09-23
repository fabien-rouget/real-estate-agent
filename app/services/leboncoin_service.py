"""Business service layer for retrieving and preparing Leboncoin listings for the AI agent."""

import logging

from app.clients.leboncoin_client import LeboncoinClient

logger = logging.getLogger(__name__)

_leboncoin_client = LeboncoinClient()


def fetch_leboncoin_listing(url_or_id: str) -> str:
    """Télécharge le contenu brut d'une annonce immobilière Leboncoin à partir de son URL ou de son identifiant.

    À utiliser dès que l'utilisateur fournit un lien Leboncoin (ex: https://www.leboncoin.fr/ad/ventes_immobilieres/...)
    ou un ID d'annonce pour en extraire les informations techniques.

    Args:
        url_or_id: URL complète ou identifiant numérique de l'annonce Leboncoin.

    Returns:
        Le texte brut ou payload JSON de l'annonce, ou un message d'erreur clair si l'annonce est inaccessible.
    """
    try:
        return _leboncoin_client.get_listing_raw(url_or_id)
    except Exception as exc:
        logger.warning("Échec de la récupération de l'annonce Leboncoin '%s': %s", url_or_id, exc)
        return (
            f"Erreur : Impossible de récupérer l'annonce ({exc}). "
            "Demandez à l'utilisateur de vérifier l'URL ou de copier-coller le texte directement."
        )

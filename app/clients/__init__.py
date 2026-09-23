"""Clients package."""

from app.clients.ademe_client import AdemeClient
from app.clients.leboncoin_client import LeboncoinClient

__all__ = ["AdemeClient", "LeboncoinClient"]

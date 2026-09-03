"""Credential-optional paid-media connector framework."""

from connectors.base import BaseMarketingConnector, ConnectorError
from connectors.google_ads import GoogleAdsConnector
from connectors.meta_ads import MetaAdsConnector
from connectors.tiktok_ads import TikTokAdsConnector

__all__ = [
    "BaseMarketingConnector",
    "ConnectorError",
    "GoogleAdsConnector",
    "MetaAdsConnector",
    "TikTokAdsConnector",
]

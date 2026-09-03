from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests


class OAuthError(RuntimeError):
    pass


@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    token_type: str = "Bearer"

    def is_expiring(self, skew_seconds: int = 60) -> bool:
        return self.expires_at is not None and self.expires_at <= datetime.now(timezone.utc) + timedelta(seconds=skew_seconds)


class OAuth2RefreshClient:
    def __init__(self, token_url: str, client_id: str, client_secret: str, session: object | None = None) -> None:
        self.token_url = token_url
        self.client_id = client_id
        self._client_secret = client_secret
        self.session = session or requests.Session()

    def refresh(self, token: OAuthToken) -> OAuthToken:
        if not token.refresh_token:
            raise OAuthError("OAuth refresh token is required but was not configured.")
        response = self.session.post(
            self.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": self.client_id,
                "client_secret": self._client_secret,
            },
            timeout=30,
        )
        try:
            response.raise_for_status()
            payload = response.json()
            access_token = payload["access_token"]
        except Exception as exc:
            raise OAuthError("OAuth token refresh failed; response details were redacted.") from exc
        expires_in = int(payload.get("expires_in", 3600))
        return OAuthToken(
            access_token=access_token,
            refresh_token=payload.get("refresh_token", token.refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            token_type=payload.get("token_type", token.token_type),
        )


def redacted_headers(token: OAuthToken) -> dict[str, str]:
    return {"Authorization": f"{token.token_type} {token.access_token}"}

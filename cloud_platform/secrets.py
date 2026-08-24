from __future__ import annotations

import os
from abc import ABC, abstractmethod


class SecretNotFoundError(KeyError):
    pass


class SecretProvider(ABC):
    @abstractmethod
    def get(self, name: str) -> str:
        raise NotImplementedError


class EnvironmentSecretProvider(SecretProvider):
    def get(self, name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise SecretNotFoundError(f"Required secret {name} is not set in the environment.")
        return value


class GoogleSecretManagerProvider(SecretProvider):
    def __init__(self, project_id: str, client: object | None = None) -> None:
        if not project_id:
            raise ValueError("GCP project ID is required for Google Secret Manager.")
        if client is None:
            try:
                from google.cloud import secretmanager
            except ImportError as exc:
                raise RuntimeError("Secret Manager support requires `pip install -r requirements-cloud.txt`.") from exc
            client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id
        self.client = client

    def get(self, name: str) -> str:
        resource = f"projects/{self.project_id}/secrets/{name}/versions/latest"
        try:
            response = self.client.access_secret_version(request={"name": resource})
        except Exception as exc:
            raise SecretNotFoundError(f"Unable to access configured secret {name}.") from exc
        return response.payload.data.decode("utf-8")

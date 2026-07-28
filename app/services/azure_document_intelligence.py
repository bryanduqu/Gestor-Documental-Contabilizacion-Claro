from __future__ import annotations

from io import BytesIO
from typing import Any

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceRequestError

from app.utils.errors import ApiProviderError, ModelTimeoutError


class AzureDocumentIntelligenceService:
    """Wrapper around the Azure Document Intelligence SDK."""

    def __init__(self, endpoint: str, key: str) -> None:
        self._client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
        )

    def classify_first_page(self, classifier_id: str, image_bytes: bytes) -> Any:
        try:
            poller = self._client.begin_classify_document(
                classifier_id=classifier_id,
                body=BytesIO(image_bytes),
                split="none",
            )
            return poller.result()
        except ServiceRequestError as exc:
            raise ModelTimeoutError(f"Azure classifier request failed: {exc}") from exc
        except HttpResponseError as exc:
            raise ApiProviderError(f"Azure classifier request failed: {exc}") from exc

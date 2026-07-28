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

    def analyze_document(self, model_id: str, document_bytes: bytes) -> Any:
        try:
            poller = self._client.begin_analyze_document(
                model_id=model_id,
                body=BytesIO(document_bytes),
            )
            return poller.result()
        except ServiceRequestError as exc:
            raise ModelTimeoutError(f"Azure extraction request failed: {exc}") from exc
        except HttpResponseError as exc:
            raise ApiProviderError(f"Azure extraction request failed: {exc}") from exc

    def analyze_layout(self, document_bytes: bytes) -> Any:
        """Run Azure prebuilt-layout to obtain table structure."""
        try:
            poller = self._client.begin_analyze_document(
                model_id="prebuilt-layout",
                body=BytesIO(document_bytes),
            )
            return poller.result()
        except ServiceRequestError as exc:
            raise ModelTimeoutError(f"Azure layout request failed: {exc}") from exc
        except HttpResponseError as exc:
            raise ApiProviderError(f"Azure layout request failed: {exc}") from exc

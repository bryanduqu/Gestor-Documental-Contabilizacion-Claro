from __future__ import annotations

from typing import Any

from app.utils.errors import ClassificationError


def get_classification_from_result(result: Any) -> tuple[str, float | None]:
    """Extract the top classification from an Azure analyze result."""
    documents = getattr(result, "documents", None) or []
    if not documents:
        raise ClassificationError("Azure classifier returned no document predictions.")

    best_document = max(documents, key=lambda item: getattr(item, "confidence", 0.0) or 0.0)
    raw_doc_type = getattr(best_document, "doc_type", "")
    if not raw_doc_type:
        raise ClassificationError("Azure classifier returned an empty document type.")

    return str(raw_doc_type).strip(), getattr(best_document, "confidence", None)

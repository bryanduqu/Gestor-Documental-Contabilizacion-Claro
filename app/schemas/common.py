from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    type: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ProcessedDocumentResponse(BaseModel):
    id: str
    document_type: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    data: dict[str, Any]
    processing_time_ms: int = Field(ge=0)
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.backend.dependencies.container import Container, get_container
from app.schemas.common import ErrorResponse, ProcessedDocumentResponse
from app.utils.errors import (
    ApiProviderError,
    ClassificationError,
    CorruptedPdfError,
    DocumentNotFoundError,
    EmptyPdfError,
    ExtractionError,
    ModelTimeoutError,
)


router = APIRouter(prefix="", tags=["documents"])


@router.post(
    "/upload",
    response_model=ProcessedDocumentResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def upload_document(
    file: UploadFile = File(...),
    container: Container = Depends(get_container),
) -> ProcessedDocumentResponse:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    try:
        return container.document_service.process(file)
    except (
        EmptyPdfError,
        CorruptedPdfError,
        ClassificationError,
        ExtractionError,
        ValueError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (ApiProviderError, ModelTimeoutError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get(
    "/document/{document_id}",
    response_model=ProcessedDocumentResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_document(
    document_id: str,
    container: Container = Depends(get_container),
) -> ProcessedDocumentResponse:
    try:
        return container.document_service.get_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

from __future__ import annotations

import io
from pathlib import Path

import fitz
from PIL import Image

from app.utils.errors import CorruptedPdfError, EmptyPdfError


def extract_first_page_image(pdf_path: Path, image_format: str = "PNG") -> bytes:
    """Render the first page of a PDF as image bytes."""
    try:
        document = fitz.open(pdf_path)
    except Exception as exc:  # pragma: no cover - fitz exceptions are varied
        raise CorruptedPdfError("The PDF file is corrupted or unreadable.") from exc

    try:
        if document.page_count == 0:
            raise EmptyPdfError("The PDF file has no pages.")

        page = document.load_page(0)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        buffer = io.BytesIO()
        image.save(buffer, format=image_format)
        return buffer.getvalue()
    finally:
        document.close()


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from every page in a PDF."""
    try:
        document = fitz.open(pdf_path)
    except Exception as exc:  # pragma: no cover - fitz exceptions are varied
        raise CorruptedPdfError("The PDF file is corrupted or unreadable.") from exc

    try:
        if document.page_count == 0:
            raise EmptyPdfError("The PDF file has no pages.")

        texts: list[str] = []
        for page_index in range(document.page_count):
            texts.append(document.load_page(page_index).get_text("text"))
        return "\n".join(texts).strip()
    finally:
        document.close()

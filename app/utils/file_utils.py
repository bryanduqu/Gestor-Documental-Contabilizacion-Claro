from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config.settings import Settings


def save_upload_temporarily(upload_file: UploadFile, settings: Settings) -> Path:
    """Persist an uploaded file in the temp storage directory."""
    suffix = Path(upload_file.filename or "document.pdf").suffix or ".pdf"
    file_path = settings.temp_dir / f"{uuid4()}{suffix}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path

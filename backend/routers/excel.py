"""
backend/routers/excel.py
------------------------
Excel ingestion router: Handles secure file upload, sheet inspection,
and schema discovery.
"""

from pathlib import Path
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

from backend.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES
from backend.models import User
from backend.schemas import ExcelInspectionResponse
from backend.security import get_current_user
from backend.services.excel_parser import ExcelParserService

router = APIRouter(prefix="/api/excel", tags=["Excel Processing"])


@router.post("/upload", response_model=ExcelInspectionResponse)
async def upload_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts an Excel file (.xlsx, .xls), validates size and format,
    stores it in private storage, and performs automatic schema classification.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only .xlsx and .xls Excel workbooks are supported."
        )

    file_id = str(uuid.uuid4())
    stored_path = UPLOAD_DIR / f"{file_id}{ext}"

    # Read and check size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of 25MB."
        )

    # Security: Verify binary magic bytes (ZIP PK\x03\x04 for .xlsx or OLE2 \xD0\xCF\x11\xE0 for .xls)
    if len(file_bytes) < 4 or (
        not file_bytes.startswith(b"PK\x03\x04")
        and not file_bytes.startswith(b"\xd0\xcf\x11\xe0")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Excel binary signature. Please upload a valid .xlsx or .xls workbook."
        )

    with open(stored_path, "wb") as f:
        f.write(file_bytes)

    try:
        parser = ExcelParserService(stored_path)
        inspection = parser.inspect_workbook()
    except Exception as e:
        # Clean up corrupted upload
        if stored_path.exists():
            stored_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse Excel workbook: {str(e)}"
        )

    total_rows = inspection.get(
        "total_rows",
        sum(s.get("row_count", 0) for s in inspection.get("sheets_info", {}).values())
    )

    return {
        "filename": file.filename,
        "file_id": file_id,
        "sheet_names": inspection["sheet_names"],
        "active_sheet": inspection["active_sheet"],
        "sheets_info": inspection["sheets_info"],
        "detected_title": inspection["detected_title"],
        "detected_period": inspection["detected_period"],
        "workbook_warnings": inspection.get("workbook_warnings", []),
        "total_rows": total_rows,
    }

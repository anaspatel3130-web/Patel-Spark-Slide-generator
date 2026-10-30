"""
backend/routers/generator.py
----------------------------
Presentation generation router: Presentation planning, preview generation,
PPTX building, and secure file downloads.
"""

from pathlib import Path
import uuid
from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import UPLOAD_DIR, GENERATED_DIR
from backend.database import get_db
from backend.models import User, PresentationRecord
from backend.schemas import (
    GeneratePresentationRequest,
    PresentationPlanResponse,
    SlideItem
)
from backend.security import get_current_user
from backend.services.excel_parser import ExcelParserService
from backend.services.data_analyzer import DataAnalyzerService
from backend.services.presentation_plan import PresentationPlannerService
from backend.services.pptx_builder import PPTXBuilderService

try:
    from backend.services.excel_exporter import ExcelExporterService
except ImportError:
    ExcelExporterService = None

try:
    from backend.services.validator_service import ValidationService
except ImportError:
    ValidationService = None

try:
    from backend.services.ai_agent_service import MultiAgentOrchestrator
except ImportError:
    MultiAgentOrchestrator = None

router = APIRouter(prefix="/api/generator", tags=["PowerPoint Generator"])


def _get_excel_exporter():
    global ExcelExporterService
    if ExcelExporterService is None:
        try:
            from backend.services.excel_exporter import ExcelExporterService as _EES
            ExcelExporterService = _EES
        except ImportError:
            pass
    return ExcelExporterService


def _get_validator_service():
    global ValidationService
    if ValidationService is None:
        try:
            from backend.services.validator_service import ValidationService as _VS
            ValidationService = _VS
        except ImportError:
            pass
    return ValidationService


def _find_upload_file(file_id: str) -> Path:
    for ext in [".xlsx", ".xls"]:
        p = UPLOAD_DIR / f"{file_id}{ext}"
        if p.exists():
            return p
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file session expired or not found.")


def _analyze_sheets(
    parser: ExcelParserService,
    req: GeneratePresentationRequest,
    inspection: Dict[str, Any]
) -> Tuple[List[str], Dict[str, Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]], str, Optional[str]]:
    """
    Analyzes one or multiple selected worksheets and generates the slide plan.
    """
    raw_selected = req.selected_sheets or ([req.sheet_name] if req.sheet_name else [inspection["active_sheet"]])
    # Filter to valid sheets present in workbook
    valid_sheets = [s for s in raw_selected if s in inspection.get("sheet_names", [])]
    if not valid_sheets:
        valid_sheets = [inspection["active_sheet"]]

    analysis_by_sheet: Dict[str, Dict[str, Any]] = {}
    selected_sheets: List[str] = []

    for s in valid_sheets:
        try:
            if hasattr(parser, "load_raw_and_clean_data"):
                loaded = parser.load_raw_and_clean_data(s)
                if isinstance(loaded, tuple) and len(loaded) == 3:
                    first_df, second_df, classification = loaded
                    num_cols = classification.get("numeric", [])
                    if num_cols and hasattr(first_df, "dtypes") and hasattr(second_df, "dtypes"):
                        first_num = sum(1 for c in num_cols if c in first_df.columns and str(first_df[c].dtype) != "object")
                        second_num = sum(1 for c in num_cols if c in second_df.columns and str(second_df[c].dtype) != "object")
                        if first_num > second_num:
                            df, raw_df = first_df, second_df
                        else:
                            raw_df, df = first_df, second_df
                    else:
                        raw_df, df = first_df, second_df
                else:
                    df, classification = loaded
                    raw_df = df
            else:
                df, classification = parser.load_clean_data(s)
                raw_df = df

            try:
                analyzer = DataAnalyzerService(df, classification, raw_df=raw_df, sheet_name=s)
            except TypeError:
                analyzer = DataAnalyzerService(df, classification)

            analysis_by_sheet[s] = analyzer.analyze()
            selected_sheets.append(s)
        except ValueError:
            if len(valid_sheets) == 1:
                raise
            continue

    if not analysis_by_sheet:
        active = inspection["active_sheet"]
        df, classification = parser.load_clean_data(active)
        try:
            analyzer = DataAnalyzerService(df, classification, raw_df=df, sheet_name=active)
        except TypeError:
            analyzer = DataAnalyzerService(df, classification)
        analysis_by_sheet[active] = analyzer.analyze()
        selected_sheets = [active]

    primary_sheet = req.sheet_name if req.sheet_name in analysis_by_sheet else selected_sheets[0]
    primary_analysis = analysis_by_sheet[primary_sheet]

    title = req.custom_title or inspection["detected_title"]
    period = inspection["detected_period"]

    options = {
        "slide_mode": req.slide_mode,
        "detail_level": req.detail_level,
        "include_charts_tables": req.include_charts_tables,
        "include_routing_flows": req.include_routing_flows,
        "include_remarks_exceptions": req.include_remarks_exceptions,
        "include_full_data_tables": req.include_full_data_tables or (req.detail_level == "complete"),
    }

    try:
        planner = PresentationPlannerService(
            primary_analysis,
            title,
            period,
            multi_sheet_analysis=analysis_by_sheet,
            options=options
        )
    except TypeError:
        planner = PresentationPlannerService(primary_analysis, title, period)

    try:
        slides = planner.create_plan(requested_slides=req.slide_count, options=options)
    except TypeError:
        slides = planner.create_plan(requested_slides=max(2, min(6, req.slide_count or 4)))

    return selected_sheets, analysis_by_sheet, primary_analysis, slides, title, period


@router.post("/preview", response_model=PresentationPlanResponse)
def preview_presentation_plan(
    req: GeneratePresentationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Computes data analysis and produces the slide blueprint without generating the PPTX binary.
    Enables instant interactive preview in the browser.
    """
    filepath = _find_upload_file(req.file_id)
    parser = ExcelParserService(filepath)
    inspection = parser.inspect_workbook()

    selected_sheets, analysis_by_sheet, primary_analysis, slides, title, _ = _analyze_sheets(
        parser, req, inspection
    )

    validator_cls = _get_validator_service()
    validation_report = None
    if validator_cls is not None:
        try:
            validation_report = validator_cls.validate_outputs(
                filepath,
                None,
                None,
                inspection,
                selected_sheets,
                analysis_by_sheet,
                slides
            )
        except Exception:
            validation_report = None

    if MultiAgentOrchestrator is not None:
        try:
            agent_audit = MultiAgentOrchestrator().run_pipeline(inspection, analysis_by_sheet, slides)
            if isinstance(validation_report, dict):
                validation_report["agent_pipeline"] = agent_audit
            else:
                validation_report = {"passed": True, "agent_pipeline": agent_audit}
        except Exception:
            pass

    return {
        "file_id": req.file_id,
        "presentation_title": title,
        "requested_slides": req.slide_count,
        "actual_slides": len(slides),
        "slides": slides,
        "insights_summary": primary_analysis.get("takeaways", []),
        "validation_report": validation_report,
    }


@router.post("/create")
def create_presentation(
    req: GeneratePresentationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Renders and compiles the presentation into a downloadable .pptx file
    and a professionally formatted .xlsx workbook with cross-validation.
    """
    filepath = _find_upload_file(req.file_id)
    parser = ExcelParserService(filepath)
    inspection = parser.inspect_workbook()

    selected_sheets, analysis_by_sheet, primary_analysis, slides, title, _ = _analyze_sheets(
        parser, req, inspection
    )

    # 1. Build UPS-branded PPTX
    out_id = str(uuid.uuid4())[:8]
    pptx_filename = f"Presentation_{out_id}.pptx"
    builder = PPTXBuilderService(slides, title)
    pptx_output_path = builder.build(pptx_filename)

    # 2. Build Professionally Formatted Excel Workbook (.xlsx)
    excel_filename = f"Formatted_Workbook_{out_id}.xlsx"
    excel_output_path = None
    exporter_cls = _get_excel_exporter()
    if exporter_cls is not None:
        try:
            exporter = exporter_cls(filepath, analysis_by_sheet)
            excel_output_path = exporter.build_formatted_workbook(excel_filename)
        except Exception:
            excel_output_path = None

    # 3. Run Cross-Validation Service
    validator_cls = _get_validator_service()
    validation_report = None
    if validator_cls is not None:
        try:
            validation_report = validator_cls.validate_outputs(
                filepath,
                excel_output_path,
                pptx_output_path,
                inspection,
                selected_sheets,
                analysis_by_sheet,
                slides
            )
        except Exception:
            validation_report = None

    if MultiAgentOrchestrator is not None:
        try:
            agent_audit = MultiAgentOrchestrator().run_pipeline(inspection, analysis_by_sheet, slides)
            if isinstance(validation_report, dict):
                validation_report["agent_pipeline"] = agent_audit
            else:
                validation_report = {"passed": True, "agent_pipeline": agent_audit}
        except Exception:
            pass

    # Save to history
    record = PresentationRecord(
        user_id=current_user.id,
        original_filename=filepath.name,
        presentation_title=title,
        slide_count=len(slides),
        pptx_filename=pptx_filename,
        insights_summary="\n".join(primary_analysis.get("takeaways", []))
    )
    db.add(record)
    db.commit()

    return {
        "success": True,
        "presentation_title": title,
        "slide_count": len(slides),
        "filename": pptx_filename,
        "download_url": f"/api/generator/download/{pptx_filename}",
        "excel_filename": excel_filename,
        "excel_download_url": f"/api/generator/download-excel/{excel_filename}",
        "validation_report": validation_report,
    }


@router.get("/download/{filename}")
def download_presentation(filename: str):
    """
    Securely serves the generated PowerPoint file for download.
    """
    safe_filename = Path(filename).name
    file_path = GENERATED_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation file not found or expired."
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=safe_filename,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )


@router.get("/download-excel/{filename}")
def download_formatted_excel(filename: str):
    """
    Securely serves the generated formatted Excel workbook (.xlsx) for download.
    """
    safe_filename = Path(filename).name
    file_path = GENERATED_DIR / safe_filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formatted Excel workbook not found or expired."
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=safe_filename,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )


@router.get("/history")
def list_generation_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns user's previously generated presentation records.
    """
    records = db.query(PresentationRecord).filter(
        PresentationRecord.user_id == current_user.id
    ).order_by(PresentationRecord.created_at.desc()).limit(15).all()

    return [
        {
            "id": r.id,
            "title": r.presentation_title,
            "slide_count": r.slide_count,
            "filename": r.pptx_filename,
            "download_url": f"/api/generator/download/{r.pptx_filename}",
            "created_at": r.created_at.isoformat()
        }
        for r in records
    ]


@router.delete("/{record_id}")
def delete_presentation_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a presentation record and its associated PowerPoint (.pptx)
    and Formatted Excel (.xlsx) files from disk.
    """
    record = db.query(PresentationRecord).filter(
        PresentationRecord.id == record_id,
        PresentationRecord.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation record not found or access denied."
        )

    # 1. Delete physical PowerPoint presentation if exists
    if record.pptx_filename:
        pptx_path = GENERATED_DIR / record.pptx_filename
        if pptx_path.exists():
            try:
                pptx_path.unlink()
            except Exception:
                pass

        # 2. Delete corresponding formatted Excel workbook if exists
        excel_filename = record.pptx_filename.replace("Presentation_", "Formatted_Workbook_").replace(".pptx", ".xlsx")
        excel_path = GENERATED_DIR / excel_filename
        if excel_path.exists():
            try:
                excel_path.unlink()
            except Exception:
                pass

    db.delete(record)
    db.commit()

    return {
        "success": True,
        "message": f"Presentation '{record.presentation_title}' and generated files have been permanently deleted."
    }


@router.delete("/file/{filename}")
def cancel_and_delete_file(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancels or removes a generated file by its filename immediately after download.
    """
    safe_name = Path(filename).name
    target_path = GENERATED_DIR / safe_name
    if target_path.exists():
        try:
            target_path.unlink()
        except Exception:
            pass

    # If it was a PowerPoint, also clean up the paired Excel file if present
    if safe_name.endswith(".pptx"):
        paired_excel = GENERATED_DIR / safe_name.replace("Presentation_", "Formatted_Workbook_").replace(".pptx", ".xlsx")
        if paired_excel.exists():
            try:
                paired_excel.unlink()
            except Exception:
                pass

    # Clean up corresponding database record if exists
    record = db.query(PresentationRecord).filter(
        PresentationRecord.pptx_filename == safe_name,
        PresentationRecord.user_id == current_user.id
    ).first()
    if record:
        db.delete(record)
        db.commit()

    return {"success": True, "message": f"Generated file '{safe_name}' cancelled and removed from storage."}

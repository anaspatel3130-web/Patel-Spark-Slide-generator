"""
backend/schemas.py
------------------
Pydantic models for data validation, serialization, and OpenAPI documentation schemas.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# ----------------- Authentication Schemas -----------------

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    email: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Access Request Schemas -----------------

class AccessRequestCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    department: Optional[str] = Field(None, max_length=100)
    reason: str = Field(..., min_length=10, max_length=1000)

class AccessRequestOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    department: Optional[str]
    reason: str
    status: str
    invite_token: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True

class AccessRequestAction(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")

class AccountActivate(BaseModel):
    invite_token: str
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

# ----------------- Excel & Presentation Schemas -----------------

class SheetSummary(BaseModel):
    name: str
    row_count: int
    col_count: int
    columns: List[str]
    numeric_columns: List[str]
    categorical_columns: List[str]
    date_columns: List[str]
    country_columns: List[str]
    route_columns: List[str]
    origin_columns: List[str] = []
    transit_columns: List[str] = []
    destination_columns: List[str] = []
    flight_columns: List[str] = []
    customer_columns: List[str] = []
    frequency_columns: List[str] = []
    remarks_columns: List[str] = []
    detected_categories: List[str] = []
    quality_warnings: List[str] = []
    missing_cells_count: int = 0
    duplicate_rows_count: int = 0

class ExcelInspectionResponse(BaseModel):
    filename: str
    file_id: str
    sheet_names: List[str]
    active_sheet: str
    sheets_info: Dict[str, SheetSummary]
    detected_title: str
    detected_period: Optional[str]
    workbook_warnings: List[str] = []
    total_rows: int = 0

class SlideItem(BaseModel):
    slide_number: int
    layout_type: str  # 'title', 'kpi_summary', 'country_analysis', 'route_performance', 'deep_dive', 'route_flow_diagram', 'exceptions_remarks', 'full_data_table', 'closing'
    title: str
    subtitle: Optional[str] = None
    kpis: Optional[List[Dict[str, Any]]] = None
    chart_config: Optional[Dict[str, Any]] = None
    table_data: Optional[Dict[str, Any]] = None
    takeaways: Optional[List[str]] = None
    source_badge: Optional[str] = None
    routing_flows: Optional[List[Dict[str, Any]]] = None
    exceptions_list: Optional[List[Dict[str, Any]]] = None
    exceptions_and_remarks: Optional[List[Dict[str, Any]]] = None
    sheet_name: Optional[str] = None
    row_range: Optional[str] = None
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None

class PresentationPlanResponse(BaseModel):
    file_id: str
    presentation_title: str
    requested_slides: int
    actual_slides: int
    slides: List[SlideItem]
    insights_summary: List[str]
    validation_report: Optional[Dict[str, Any]] = None

class GeneratePresentationRequest(BaseModel):
    file_id: str
    sheet_name: Optional[str] = None
    slide_count: int = Field(default=4, ge=0, le=6)
    custom_title: Optional[str] = None
    selected_sheets: Optional[List[str]] = None
    slide_mode: str = "manual"
    detail_level: str = "summary"
    include_charts_tables: bool = True
    include_routing_flows: bool = True
    include_remarks_exceptions: bool = True
    include_full_data_tables: bool = False

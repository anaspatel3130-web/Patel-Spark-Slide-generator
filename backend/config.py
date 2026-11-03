"""
backend/config.py
-----------------
Application settings, environment configurations, and separated design tokens:
- Website platform configuration (Patel'Spark)
- PowerPoint generation configuration (Approved UPS Corporate Design)
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = BACKEND_DIR / "assets"

# Detect Vercel / Cloud Serverless read-only environment and route writable paths to /tmp
IS_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
if IS_SERVERLESS:
    STORAGE_DIR = Path("/tmp/patelspark_storage")
    DEFAULT_DB_PATH = Path("/tmp/patelspark.db")
else:
    STORAGE_DIR = BACKEND_DIR / "storage"
    DEFAULT_DB_PATH = BACKEND_DIR / "patelspark.db"

UPLOAD_DIR = STORAGE_DIR / "uploads"
GENERATED_DIR = STORAGE_DIR / "generated"

# Ensure directories exist
for directory in [UPLOAD_DIR, GENERATED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
if not IS_SERVERLESS:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Authorised UPS PowerPoint Assets (Strictly for PowerPoint Generation)
UPS_LOGO_PATH = ASSETS_DIR / "ups_logo.png"
UPS_WATERMARK_PATH = ASSETS_DIR / "ups_watermark.png"
CUSTOM_TEMPLATE_PATH = Path("/tmp/custom_template.pptx") if IS_SERVERLESS else (ASSETS_DIR / "custom_template.pptx")

# Security Settings
SECRET_KEY = os.getenv("SECRET_KEY", "patelspark-super-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Database Configuration (SQLite default; can be overridden with PostgreSQL URL)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Default Administrator Credentials (Seeded on first startup)
DEFAULT_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@patelspark.internal")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "PatelSpark2026!Admin")
DEFAULT_ADMIN_NAME = "Patel'Spark Administrator"

# Email Notification Settings (Alerts sent when user requests access)
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "anaspatel3130@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes")
SMTP_SSL = os.getenv("SMTP_SSL", "false").lower() in ("true", "1", "yes")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

# File Upload Constraints
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 Megabytes
ALLOWED_EXTENSIONS = {".xlsx", ".xls"}

# Approved UPS Corporate Presentation Palette (Used ONLY by pptx_builder.py)
UPS_PPTX_COLORS = {
    "UPS_BROWN": (53, 28, 21),         # #351C15 - Official UPS Pullman Brown
    "UPS_DARK_BROWN": (36, 18, 13),    # #24120D - Deep Espresso Card Surface
    "UPS_GOLD": (255, 181, 0),         # #FFB500 - Official UPS Gold
    "UPS_GOLD_DARK": (217, 150, 0),    # #D99600 - Secondary Gold Accent
    "WARM_CREAM": (250, 248, 245),     # #FAF8F5 - Slide Canvas Warm Off-White
    "WARM_ROW_ALT": (245, 240, 235),   # #F5F0EB - Alternating Table Row Tint
    "CHARCOAL": (30, 27, 24),          # #1E1B18 - High-Contrast Body Text
    "SLATE_GRAY": (100, 116, 139),     # #64748B - Subtitles & Metadata
    "BORDER_LIGHT": (226, 217, 208),   # #E2D9D0 - Warm Card Border
    "WHITE": (255, 255, 255),          # #FFFFFF - Pure White
}

# PowerPoint Layout Standards (16:9 Widescreen)
PPTX_WIDTH_INCHES = 13.333
PPTX_HEIGHT_INCHES = 7.5

# ⚡ Patel'Spark — Universal Excel Analysis & PowerPoint Automation Engine

> **Author:** **Anas S Patel** (*Second-Year Software / Computer Engineering Student*)  
> **Repository:** [https://github.com/anaspatel3130-web/Patel-Spark-Slide-generator](https://github.com/anaspatel3130-web/Patel-Spark-Slide-generator)  
> **Tech Stack:** Python 3.11 • FastAPI • Pandas • OpenPyXL • python-pptx • SQLAlchemy • JWT RBAC • Vanilla ES6 SPA

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fanaspatel3130-web%2FPatel-Spark-Slide-generator&project-name=patel-spark&repository-name=Patel-Spark-Slide-generator)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/anaspatel3130-web/Patel-Spark-Slide-generator)

---

## 📌 GitHub Repository Description (For About Section)

> **Patel'Spark** is a full-stack Business Intelligence & Presentation Automation Platform that ingests multi-sheet Excel workbooks (`.xlsx`/`.xls`), performs zero-hallucination deterministic analytics via a multi-agent verification pipeline, and compiles both management-ready 16:9 widescreen PowerPoint presentations (`.pptx`) and formatted audit Excel workbooks (`.xlsx`). Built by **Anas S Patel**.

---

## 🌟 Executive Overview

**Patel'Spark** transforms raw, unstructured or multi-sheet operational Excel spreadsheets into executive-ready deliverables in seconds:

1. **Management-Ready 16:9 Widescreen PowerPoint Presentations (`.pptx`)**:
   - Strictly compiled in the **Approved UPS Corporate Presentation Design** (`13.333"` × `7.5"` widescreen, Pullman Brown `#351C15`, UPS Gold `#FFB500`, Warm Cream `#FAF8F5`).
   - Automatically embeds the authorised corporate shield logo on cover/header/closing slides and places a subtle, non-intrusive corporate watermark (`~8.5%` opacity) on **every single slide**.
   - Generates native editable PowerPoint charts (column, bar, line, doughnut), KPI summary cards, **Origin ➔ Transit ➔ Destination** visual routing flow diagrams, operational exceptions/remarks callouts, and **paginated 10-row source data tables**.
2. **Downloadable Formatted Excel Workbooks (`.xlsx`)**:
   - Preserves **100% of original worksheets and cell values** without alteration, deletion, or fabrication.
   - Enhances presentation with Dark Navy headers, consistent typography, auto-fitted column widths, frozen header rows, auto-filters, and an appended `Executive_Analysis_Summary` sheet with traceable formulas.

---

## 🏗️ System Architecture & Strict Brand Separation

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│                   PATEL'SPARK WEB PLATFORM (Frontend SPA)                     │
│  • Naturally Eye-Comfort UI + 1-Click Night Mode (variables.css / app.js)     │
│  • Gamified Analyst Command Center (XP, Ranks LVL 1-5, 6 Badges, Telemetry)   │
│  • Interactive 16:9 Slide Preview Carousel & Step-by-Step User Guide          │
│  • Signature Footer: "⚡ Made by Anas S Patel" (Radium Yellow Neon)            │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ REST API (JWT Bearer RBAC + Rate Limit
                                        │ + OWASP Security Headers)
┌───────────────────────────────────────▼───────────────────────────────────────┐
│                     FASTAPI BACKEND CORE (backend/main.py)                    │
├───────────────────────┬───────────────────────────┬───────────────────────────┤
│ 1. INGESTION ENGINE   │ 2. MULTI-AGENT BRAIN      │ 3. DUAL OUTPUT COMPILERS  │
│  (excel_parser.py)    │  (data_analyzer.py +      │  • pptx_builder.py:       │
│  • Magic-Byte Check   │   presentation_plan.py +  │    16:9 Approved UPS      │
│  • Merged-Cell Fix    │   ai_agent_service.py)    │    Corporate Design with  │
│  • 8-Row Header Scan  │  • 100% Deterministic     │    Logo & Watermark on    │
│  • Semantic Column    │    Pandas Aggregations    │    Every Slide            │
│    Classification     │  • Zero Hallucinations    │  • excel_exporter.py:     │
│  • Multi-Sheet Audit  │  • Auto Mode Capped at    │    100% Original Sheets   │
│                       │    5–6 Slides Max         │    + Executive Summary    │
└───────────────────────┴─────────────┬─────────────┴───────────────────────────┘
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────────┐
│             4. CROSS-VALIDATION & AUDIT ENGINE (validator_service.py)         │
│  • Verifies 100% of original Excel sheets & cell values are preserved         │
│  • Verifies corporate logo & watermark placement on every slide               │
│  • Supports instant 1-click Cancel & Delete of generated decks from storage   │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Engineering Features

### 1. Universal Schema-Agnostic Excel Ingestion (`backend/services/excel_parser.py`)
- Accepts `.xlsx` and `.xls` files up to 25 MB, verified via binary magic-byte signatures (`PK\x03\x04` and `\xD0\xCF\x11\xE0`).
- Automatically detects all worksheets, unmerges irregular cells, scans up to 8 header rows to locate the true table header, and classifies columns into semantic roles (`numeric`, `country`, `route`, `origin`, `transit`, `destination`, `flight`, `customer`, `frequency`, `remarks`, `date`).
- Surfaces pre-analysis **Data-Quality Warnings** (missing cells, duplicate records, sparse columns).

### 2. Zero-Hallucination Multi-Agent Pipeline (`backend/services/ai_agent_service.py` & `presentation_plan.py`)
- **100% Deterministic Accuracy**: Every KPI, chart category, numeric series, routing leg, and takeaway bullet is computed directly from the uploaded Excel DataFrame. Zero hardcoded fallback countries, routes, or fabricated metrics.
- **Strict 5–6 Slide Cap on Auto Mode**: Auto mode (`slide_mode="auto"`) intelligently synthesizes at most **5 to 6 slides** (`Cover`, `Executive KPI Summary`, `Primary Breakdown / Routing Flow`, `Secondary Breakdown / Exceptions`, `Verbatim Source Data Table`, and `Closing`), while manual mode supports **2, 3, 4, 5, or 6 slides**.
- **3-Stage Official Agent Verification**:
  1. `SchemaInspectorAgent`: Audits column classifications and worksheet structures.
  2. `DeterministicMathAgent`: Computes vectorized totals, shares, rankings, and calculation traces.
  3. `FactLockAuditorAgent`: Verifies zero unverified entities exist on any slide (with optional official `google-genai` SDK integration governed by a strict numeric regex fact-lock).

### 3. Naturally Eye-Comfort & Gamified UI/UX (`frontend/`)
- **Naturally Eye-Comfort Palette**: Designed with low-glare warm slate-stone (`#E9EEF4`) and soft paper (`#F4F6F9`) surfaces by default, plus a 1-click **🌙 Eye Comfort / ☀️ Day Comfort** toggle in the navigation bar.
- **Gamified Analyst Command Center**: Features real-time XP progression (`LVL 1 Data Trainee` ➔ `LVL 5 Chief Automation Architect`), live telemetry HUD counters, 6 unlockable achievement badges, and celebratory particle animations.
- **Interactive Step-by-Step User Guide**: Accessible both inline on the landing page and via the `📖 How-To Guide` modal from any screen.
- **Instant Cancel & Delete**: Users can permanently delete generated `.pptx` and `.xlsx` files from disk and database history with 1 click right after download or from the history table.

### 4. Enterprise Security Hardening & Admin Email Alerts (`backend/security.py`, `backend/services/email_service.py`)
- **Real-Time Admin Email Alerts**: When a prospective user fills out the "Request Access" form, an automated notification is dispatched to `anaspatel3130@gmail.com` containing the applicant's name, email, department, justification reason, and direct link to approve/reject in the admin dashboard.
- **Dual Delivery Engine**: Supports standard SMTP (e.g. Gmail App Passwords on `smtp.gmail.com:587`) and Resend REST API, running asynchronously in FastAPI `BackgroundTasks` so the user's signup is instant and never blocked by network latency.
- **Password Cryptography**: Salted `PBKDF2-HMAC-SHA256` with 100,000 iterations and constant-time verification (`secrets.compare_digest`).
- **Role-Based Access Control (RBAC)**: Signed JWT Bearer authentication with Administrator approval workflows and single-use invitation tokens.
- **Rate Limiting & OWASP Headers**: Sliding-window rate limiter on `/api/auth/login` and `/api/auth/request-access`, plus `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy`.

---

## 💻 Local Installation & Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/anaspatel3130-web/Patel-Spark-Slide-generator.git
cd Patel-Spark-Slide-generator

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the automated test suites (100% Pass Rate)
python tests/test_pipeline.py
python tests/test_api_endpoints.py

# 4. Start the FastAPI server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **`http://127.0.0.1:8000`** in your browser.

### Default Master Administrator Credentials
- **Email:** `admin@patelspark.internal`
- **Password:** `PatelSpark2026!Admin`
*(Tip: Click the **"Fill Master Admin Credentials"** button inside the Sign-In modal for instant 1-click login).*

---

## ☁️ Cloud Deployment (Render / Railway / Docker)

This repository includes `Dockerfile`, `render.yaml`, `Procfile`, and `.env.example` for 1-click cloud deployment:

1. **Render.com**: Connect this GitHub repository to Render as a **Blueprint** or **Web Service** (`Build Command: pip install -r requirements.txt`, `Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT`).
2. **Docker**:
   ```bash
   docker build -t patelspark-slide-generator .
   docker run -p 8000:8000 patelspark-slide-generator
   ```

### 📧 Email Notification Setup (Access Requests)
To receive real-time email notifications whenever a prospective user requests access:
1. Recipient defaults to **`anaspatel3130@gmail.com`** (configurable via `NOTIFICATION_EMAIL`).
2. To send live emails using **Gmail**:
   - Generate a 16-character [Google App Password](https://myaccount.google.com/apppasswords).
   - Set environment variables:
     ```env
     NOTIFICATION_EMAIL=anaspatel3130@gmail.com
     SMTP_HOST=smtp.gmail.com
     SMTP_PORT=587
     SMTP_USER=your_gmail_address@gmail.com
     SMTP_PASSWORD=your_16_char_app_password
     SMTP_TLS=true
     ```
3. Alternatively, set `RESEND_API_KEY=re_xxx` for serverless API-based delivery.

---

## 👨‍💻 Author

**Made by Anas S Patel**  
*Second-Year Software / Computer Engineering Student*

"""
backend/services/excel_parser.py
--------------------------------
Intelligent, schema-flexible Excel processing engine using Pandas and OpenPyXL.
Handles multi-sheet workbooks, merged cell resolution, irregular header normalization,
missing values, duplicate detection, and automated column semantic classification
(numerical, date, country, route, origin, transit, destination, flight, customer,
frequency, remarks).
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import re
import pandas as pd
import openpyxl

# Common country tokens and indicators
KNOWN_COUNTRIES = {
    "united states", "usa", "us", "canada", "mexico", "united kingdom", "uk",
    "germany", "france", "china", "japan", "netherlands", "singapore", "india",
    "brazil", "australia", "spain", "italy", "poland", "ireland", "belgium",
    "switzerland", "uae", "south korea", "hong kong", "taiwan", "vietnam",
    "thailand", "malaysia", "indonesia", "philippines", "saudi arabia", "turkey"
}

COUNTRY_HEADER_KEYWORDS = [
    "country", "destination", "origin", "dest_country", "orig_country",
    "destination country", "origin country", "nation", "state", "region",
    "geo", "territory", "hub_location", "market"
]

ROUTE_HEADER_KEYWORDS = [
    "route", "lane", "corridor", "origin_dest", "origin-destination",
    "from_to", "transit_lane", "flight_route", "corridor_id", "routing"
]

TEMPORAL_HEADER_KEYWORDS = [
    "date", "month", "quarter", "year", "week", "period", "timestamp",
    "ship_date", "delivery_date", "dispatch_date", "eta", "etd"
]

METRIC_HEADER_KEYWORDS = [
    "amount", "cost", "revenue", "volume", "packages", "units", "weight",
    "shipments", "transit_days", "transit_time", "ontime", "on_time",
    "delayed", "rate", "distance", "miles", "kg", "lbs", "spend", "charge"
]

ORIGIN_HEADER_KEYWORDS = [
    "origin", "from", "dep", "departure", "source", "export_country",
    "origin_hub", "orig_hub", "pickup", "shipper_country"
]

TRANSIT_HEADER_KEYWORDS = [
    "transit", "connection", "via", "hub", "stopover", "transfer",
    "relay", "intermediate", "gateway", "routing_hub"
]

DESTINATION_HEADER_KEYWORDS = [
    "destination", "dest", "to", "arr", "arrival", "import_country",
    "dest_hub", "delivery_hub", "consignee_country", "final_dest"
]

FLIGHT_HEADER_KEYWORDS = [
    "flight", "flt", "tail", "aircraft", "voyage", "vessel",
    "carrier_code", "airway", "flight_no", "flight_number", "awb"
]

CUSTOMER_HEADER_KEYWORDS = [
    "customer", "client", "account", "shipper", "consignee",
    "partner", "vendor", "company", "enterprise", "buyer"
]

FREQUENCY_HEADER_KEYWORDS = [
    "frequency", "freq", "schedule", "weekly", "daily",
    "cadence", "rotation", "operating_days", "service_days"
]

REMARKS_HEADER_KEYWORDS = [
    "remark", "note", "exception", "contingency", "special",
    "comment", "delay_reason", "status_note", "issue", "condition",
    "alert", "constraint", "handling", "instruction"
]


class ExcelParserService:
    """
    Schema-agnostic engine that ingests Excel workbooks and produces
    structured statistical and semantic profiles for presentation generation.
    """

    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"Excel file not found at: {self.filepath}")

    def inspect_workbook(self) -> Dict[str, Any]:
        """
        Scans all sheets in the workbook, inspects headers, row counts, data quality,
        and semantic categories, and identifies the richest sheet for initial analysis.
        """
        sheet_names = self._get_sheet_names()

        sheets_info: Dict[str, Any] = {}
        best_sheet = sheet_names[0] if sheet_names else "Sheet1"
        max_cells = -1
        total_rows = 0
        workbook_warnings: List[str] = []

        for name in sheet_names:
            raw_df, header_offset, merged_count = self._read_sheet_with_metadata(name)
            if raw_df is None or raw_df.empty:
                warning_msg = f"Sheet '{name}': Worksheet is empty or contains no structured tabular records."
                workbook_warnings.append(warning_msg)
                sheets_info[name] = {
                    "name": name,
                    "row_count": 0,
                    "col_count": 0,
                    "columns": [],
                    "numeric_columns": [],
                    "categorical_columns": [],
                    "date_columns": [],
                    "country_columns": [],
                    "route_columns": [],
                    "origin_columns": [],
                    "transit_columns": [],
                    "destination_columns": [],
                    "flight_columns": [],
                    "customer_columns": [],
                    "frequency_columns": [],
                    "remarks_columns": [],
                    "detected_categories": ["Empty / Non-Tabular"],
                    "quality_warnings": [warning_msg],
                    "missing_cells_count": 0,
                    "duplicate_rows_count": 0,
                }
                continue

            # Create cleaned copy for semantic classification
            clean_df = self._clean_dataframe_for_analysis(raw_df.copy())
            classification = self._classify_columns(clean_df)

            row_count = int(clean_df.shape[0])
            col_count = int(clean_df.shape[1])
            total_rows += row_count

            cell_count = row_count * col_count
            if cell_count > max_cells:
                max_cells = cell_count
                best_sheet = name

            # Compute data quality metrics
            missing_cells_count = int(raw_df.isna().sum().sum())
            duplicate_rows_count = int(raw_df.duplicated().sum())
            sheet_warnings: List[str] = []

            if header_offset > 0:
                sheet_warnings.append(
                    f"Sheet '{name}': Auto-detected table header at row {header_offset + 1} (skipped {header_offset} banner/title row(s))."
                )
            if merged_count > 0:
                sheet_warnings.append(
                    f"Sheet '{name}': Unmerged and normalized {merged_count} merged cell range(s) for accurate row alignment."
                )
            if missing_cells_count > 0:
                sheet_warnings.append(
                    f"Sheet '{name}': Detected {missing_cells_count} blank/missing cell value(s) across {row_count} records."
                )
            if duplicate_rows_count > 0:
                sheet_warnings.append(
                    f"Sheet '{name}': Detected {duplicate_rows_count} exact duplicate row(s)."
                )

            workbook_warnings.extend(sheet_warnings)
            detected_categories = self._derive_category_badges(classification, clean_df)

            sheets_info[name] = {
                "name": name,
                "row_count": row_count,
                "col_count": col_count,
                "columns": list(clean_df.columns),
                "numeric_columns": classification["numeric"],
                "categorical_columns": classification["categorical"],
                "date_columns": classification["date"],
                "country_columns": classification["country"],
                "route_columns": classification["route"],
                "origin_columns": classification["origin"],
                "transit_columns": classification["transit"],
                "destination_columns": classification["destination"],
                "flight_columns": classification["flight"],
                "customer_columns": classification["customer"],
                "frequency_columns": classification["frequency"],
                "remarks_columns": classification["remarks"],
                "detected_categories": detected_categories,
                "quality_warnings": sheet_warnings,
                "missing_cells_count": missing_cells_count,
                "duplicate_rows_count": duplicate_rows_count,
            }

        # Extract high-level metadata (detected title and date period)
        detected_title, detected_period = self._detect_presentation_context(sheets_info, best_sheet)

        return {
            "sheet_names": sheet_names,
            "active_sheet": best_sheet,
            "sheets_info": sheets_info,
            "detected_title": detected_title,
            "detected_period": detected_period,
            "workbook_warnings": workbook_warnings,
            "total_rows": total_rows,
        }

    def load_clean_data(self, sheet_name: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
        """
        Loads the chosen sheet into a cleaned DataFrame with type-coerced columns.
        Maintains 100% backwards compatibility with existing callers.
        """
        _, clean_df, classification = self.load_raw_and_clean_data(sheet_name=sheet_name)
        return clean_df, classification

    def load_raw_and_clean_data(
        self, sheet_name: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, List[str]]]:
        """
        Returns (raw_df_preserving_exact_display_strings, clean_numeric_df, classification)
        so complete data tables can display original strings (currencies, flight numbers,
        frequencies, remarks) while aggregations run on clean numeric columns.
        """
        raw_df, _, _ = self._read_sheet_with_metadata(sheet_name)
        if raw_df is None or raw_df.empty:
            raise ValueError(f"Sheet '{sheet_name}' is empty or contains no tabular data.")

        # Preserve display strings in raw_df
        display_df = raw_df.copy()
        for col in display_df.columns:
            display_df[col] = display_df[col].apply(
                lambda v: "" if pd.isna(v) or str(v).strip() in ("nan", "None", "NaT") else str(v).strip()
            )

        clean_df = self._clean_dataframe_for_analysis(raw_df.copy())
        classification = self._classify_columns(clean_df)
        return display_df, clean_df, classification

    def _get_sheet_names(self) -> List[str]:
        """
        Safely returns all worksheet names for both .xlsx and .xls files.
        """
        try:
            wb = openpyxl.load_workbook(self.filepath, data_only=True, read_only=True)
            names = list(wb.sheetnames)
            wb.close()
            return names
        except Exception:
            xls = pd.ExcelFile(self.filepath)
            return list(xls.sheet_names)

    def _clean_dataframe_for_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Strips whitespace from string columns and coerces numeric columns.
        """
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": None, "None": None, "NaT": None, "": None})

        for col in df.columns:
            cleaned_col = self._try_coerce_numeric(df[col], col_name=str(col))
            if cleaned_col is not None:
                df[col] = cleaned_col

        return df

    def _read_sheet_safely(self, sheet_name: Optional[str]) -> Optional[pd.DataFrame]:
        """
        Reads Excel sheet with automatic header row detection (up to first 8 rows)
        and merged cell handling.
        """
        df, _, _ = self._read_sheet_with_metadata(sheet_name)
        return df

    def _read_sheet_with_metadata(
        self, sheet_name: Optional[str]
    ) -> Tuple[Optional[pd.DataFrame], int, int]:
        """
        Reads an Excel sheet, resolving merged cells via OpenPyXL when possible,
        and scans the first 8 rows to locate the true table header row.
        Returns (DataFrame, header_row_index, merged_ranges_count).
        """
        merged_count = 0
        try:
            # Attempt OpenPyXL read to handle merged cells cleanly
            if self.filepath.suffix.lower() == ".xlsx":
                wb = openpyxl.load_workbook(self.filepath, data_only=True)
                target_name = sheet_name if sheet_name and sheet_name in wb.sheetnames else wb.sheetnames[0]
                ws = wb[target_name]

                merged_ranges = list(ws.merged_cells.ranges)
                merged_count = len(merged_ranges)
                for m_range in merged_ranges:
                    top_left_val = ws.cell(m_range.min_row, m_range.min_col).value
                    ws.unmerge_cells(str(m_range))
                    # Fill horizontal header merges or vertical category merges
                    for r in range(m_range.min_row, m_range.max_row + 1):
                        for c in range(m_range.min_col, m_range.max_col + 1):
                            ws.cell(r, c).value = top_left_val

                data_rows = list(ws.iter_rows(values_only=True))
                wb.close()

                if not data_rows:
                    return None, 0, merged_count

                raw_preview = pd.DataFrame(data_rows)
                raw_preview = raw_preview.dropna(how="all", axis=0).dropna(how="all", axis=1).reset_index(drop=True)
                if raw_preview.empty:
                    return None, 0, merged_count

                header_row = self._detect_header_row(raw_preview)
                headers = self._normalize_headers(raw_preview.iloc[header_row].tolist())
                df = raw_preview.iloc[header_row + 1:].copy()
                df.columns = headers
                df = df.dropna(how="all", axis=0).dropna(how="all", axis=1).reset_index(drop=True)
                return df, header_row, merged_count
        except Exception:
            pass

        # Fallback to standard Pandas reader
        try:
            preview = pd.read_excel(self.filepath, sheet_name=sheet_name or 0, header=None, nrows=8)
            if preview.empty:
                return None, 0, 0

            header_row = self._detect_header_row(preview)
            df = pd.read_excel(self.filepath, sheet_name=sheet_name or 0, header=header_row)
            df = df.dropna(how="all", axis=0).dropna(how="all", axis=1).reset_index(drop=True)
            df.columns = self._normalize_headers(list(df.columns))
            return df, header_row, merged_count
        except Exception:
            return None, 0, 0

    def _detect_header_row(self, preview_df: pd.DataFrame) -> int:
        """
        Scans the first 8 rows to locate the true table header row based on
        non-null density and text/header likelihood.
        """
        max_scan = min(8, len(preview_df))
        best_row = 0
        best_score = -1.0

        for idx in range(max_scan):
            row_vals = preview_df.iloc[idx].dropna().tolist()
            non_null_count = len(row_vals)
            if non_null_count < 2:
                continue

            # Count how many cells in this row are non-numeric strings (typical headers)
            string_cells = sum(
                1 for v in row_vals
                if isinstance(v, str) and not v.strip().replace(".", "").replace("-", "").isdigit()
            )
            unique_ratio = len({str(v).strip().lower() for v in row_vals}) / max(1, non_null_count)
            score = (non_null_count * 2.0) + (string_cells * 1.5) + (unique_ratio * 2.0)

            if score > best_score:
                best_score = score
                best_row = idx

        return best_row

    def _normalize_headers(self, raw_headers: List[Any]) -> List[str]:
        """
        Ensures every column header is a clean, non-empty, unique string.
        """
        cleaned: List[str] = []
        seen: Dict[str, int] = {}
        for idx, h in enumerate(raw_headers):
            name = str(h).strip() if h is not None and not pd.isna(h) else ""
            if not name or name.lower().startswith("unnamed"):
                name = f"Column_{idx + 1}"
            if name in seen:
                seen[name] += 1
                name = f"{name}_{seen[name]}"
            else:
                seen[name] = 1
            cleaned.append(name)
        return cleaned

    def _try_coerce_numeric(self, series: pd.Series, col_name: str = "") -> Optional[pd.Series]:
        """
        Attempts to clean currency symbols, commas, and percentage signs to parse as floats.
        Skips flight numbers, codes, or remarks columns that should remain text.
        """
        col_lower = col_name.lower()
        if any(k in col_lower for k in FLIGHT_HEADER_KEYWORDS + REMARKS_HEADER_KEYWORDS + FREQUENCY_HEADER_KEYWORDS):
            return None

        if pd.api.types.is_numeric_dtype(series):
            return series

        try:
            non_null = series.dropna()
            if non_null.empty:
                return None

            cleaned = (
                series.astype(str)
                .str.replace("$", "", regex=False)
                .str.replace("€", "", regex=False)
                .str.replace("£", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            converted = pd.to_numeric(cleaned, errors="coerce")
            valid_ratio = converted.notna().sum() / max(1, non_null.count())
            if valid_ratio >= 0.7:
                return converted
        except Exception:
            pass
        return None

    def _classify_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Analyzes column headers and content samples to assign both core and extended
        semantic roles (numeric, date, country, route, categorical + origin, transit,
        destination, flight, customer, frequency, remarks).
        """
        numeric_cols: List[str] = []
        date_cols: List[str] = []
        country_cols: List[str] = []
        route_cols: List[str] = []
        categorical_cols: List[str] = []

        origin_cols: List[str] = []
        transit_cols: List[str] = []
        destination_cols: List[str] = []
        flight_cols: List[str] = []
        customer_cols: List[str] = []
        frequency_cols: List[str] = []
        remarks_cols: List[str] = []

        for col in df.columns:
            col_lower = str(col).lower().strip()
            series = df[col]
            sample_vals = series.dropna().astype(str).head(30).tolist()

            # Extended semantic classifications (can overlap with categorical/country/route)
            if any(k in col_lower for k in ORIGIN_HEADER_KEYWORDS):
                origin_cols.append(col)
            if any(k in col_lower for k in TRANSIT_HEADER_KEYWORDS):
                transit_cols.append(col)
            if any(k in col_lower for k in DESTINATION_HEADER_KEYWORDS):
                destination_cols.append(col)
            if any(k in col_lower for k in FLIGHT_HEADER_KEYWORDS):
                flight_cols.append(col)
            if any(k in col_lower for k in CUSTOMER_HEADER_KEYWORDS):
                customer_cols.append(col)
            if any(k in col_lower for k in FREQUENCY_HEADER_KEYWORDS):
                frequency_cols.append(col)
            if any(k in col_lower for k in REMARKS_HEADER_KEYWORDS):
                remarks_cols.append(col)

            # Content heuristic for flight numbers (e.g. "5X204", "UPS102", "LH400")
            if col not in flight_cols and sample_vals:
                flight_matches = sum(
                    1 for v in sample_vals
                    if re.match(r"^(UPS|5X|FX|LH|BA|EK|QR|CX|SQ|AA|UA|DL)\s?[-]?\s?\d{2,4}$", v.strip(), re.I)
                )
                if flight_matches >= max(2, len(sample_vals) // 3):
                    flight_cols.append(col)

            # Primary mutually-aware buckets for existing chart engines
            # 1. Date Detection
            if any(k in col_lower for k in TEMPORAL_HEADER_KEYWORDS) or pd.api.types.is_datetime64_any_dtype(series):
                if col not in frequency_cols:
                    date_cols.append(col)
                    continue

            # 2. Numeric Detection
            if pd.api.types.is_numeric_dtype(series):
                if any(k in col_lower for k in ["id", "code", "zip", "flight", "flt", "awb"]):
                    categorical_cols.append(col)
                else:
                    numeric_cols.append(col)
                continue

            # 3. Route Detection
            if any(k in col_lower for k in ROUTE_HEADER_KEYWORDS):
                route_cols.append(col)
                continue

            has_route_pattern = any(
                bool(re.search(r"\b[A-Z]{3}\s*(?:-|->|–|/|>|to)\s*[A-Z]{3}\b", v))
                or ("->" in v)
                or (" to " in v.lower() and len(v) < 35)
                for v in sample_vals
            )
            if has_route_pattern and not any(k in col_lower for k in ["date", "time", "id", "remark", "note"]):
                route_cols.append(col)
                continue

            # 4. Country Detection
            if any(k in col_lower for k in COUNTRY_HEADER_KEYWORDS):
                country_cols.append(col)
                continue

            lower_sample = {str(v).lower().strip() for v in sample_vals}
            if len(lower_sample.intersection(KNOWN_COUNTRIES)) >= 2:
                country_cols.append(col)
                continue

            # 5. Default Categorical
            categorical_cols.append(col)

        # If origin or destination columns exist and country_cols is empty, include them in country_cols
        if not country_cols:
            for c in destination_cols + origin_cols:
                if c not in country_cols:
                    country_cols.append(c)

        return {
            "numeric": numeric_cols,
            "date": date_cols,
            "country": country_cols,
            "route": route_cols,
            "categorical": categorical_cols,
            "origin": origin_cols,
            "transit": transit_cols,
            "destination": destination_cols,
            "flight": flight_cols,
            "customer": customer_cols,
            "frequency": frequency_cols,
            "remarks": remarks_cols,
        }

    def _derive_category_badges(self, classification: Dict[str, List[str]], df: pd.DataFrame) -> List[str]:
        """
        Generates human-readable category badges summarizing what data a sheet contains.
        """
        badges: List[str] = []
        num_cols_lower = " ".join(c.lower() for c in classification["numeric"])

        if any(k in num_cols_lower for k in ["volume", "package", "shipment", "unit", "weight", "qty"]):
            badges.append("Shipments & Volume")
        if any(k in num_cols_lower for k in ["amount", "cost", "revenue", "spend", "rate", "price", "charge"]):
            badges.append("Financial / Currency")
        if classification["country"]:
            badges.append("Geographic / Countries")
        if classification["route"] or (classification["origin"] and classification["destination"]):
            badges.append("Routes & Transit")
        if classification["flight"] or classification["frequency"]:
            badges.append("Flight / Carrier Schedule")
        if classification["customer"]:
            badges.append("Customer Accounts")
        if classification["remarks"]:
            badges.append("Operational Remarks & Exceptions")
        if classification["date"]:
            badges.append("Time Series / Dates")

        if not badges:
            badges.append("General Operational Data")

        return badges

    def _detect_presentation_context(self, sheets_info: Dict[str, Any], best_sheet: str) -> Tuple[str, Optional[str]]:
        """
        Infers an appropriate corporate executive presentation title and reporting timeframe.
        """
        filename_clean = self.filepath.stem.replace("_", " ").replace("-", " ").title()
        title = f"Executive Business Review: {filename_clean}"
        detected_period = None

        match_period = re.search(
            r"\b(Q[1-4]|20[2-3][0-9]|FY[0-9]{2,4}|[A-Za-z]+ 20[2-3][0-9])\b",
            filename_clean,
            re.I
        )
        if match_period:
            detected_period = match_period.group(0).upper()

        return title, detected_period

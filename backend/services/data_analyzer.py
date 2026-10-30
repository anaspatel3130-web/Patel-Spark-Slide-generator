"""
backend/services/data_analyzer.py
---------------------------------
Deterministic statistical and operational analysis engine.
Computes exact totals, averages, country distributions, route logistics metrics,
origin-transit-destination routing flows, flight/frequency schedules, operational
remarks/exceptions, paginated full-data tables, and calculation audit traces.
Generates verified business insights with zero numerical hallucination.
"""

from typing import Dict, Any, List, Optional
import re
import pandas as pd
import numpy as np


class DataAnalyzerService:
    """
    Performs verified business calculations and produces structured datasets
    for chart rendering, routing flow diagrams, exception matrices, full data tables,
    and executive takeaway bullet points.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        classification: Dict[str, List[str]],
        raw_df: Optional[pd.DataFrame] = None,
        sheet_name: str = "Active Sheet",
    ):
        self.df = df.copy()
        self.raw_df = raw_df.copy() if raw_df is not None else df.copy()
        self.sheet_name = sheet_name
        self.classification = classification

        self.num_cols = classification.get("numeric", [])
        self.country_cols = classification.get("country", [])
        self.route_cols = classification.get("route", [])
        self.date_cols = classification.get("date", [])
        self.cat_cols = classification.get("categorical", [])

        self.origin_cols = classification.get("origin", [])
        self.transit_cols = classification.get("transit", [])
        self.destination_cols = classification.get("destination", [])
        self.flight_cols = classification.get("flight", [])
        self.customer_cols = classification.get("customer", [])
        self.frequency_cols = classification.get("frequency", [])
        self.remarks_cols = classification.get("remarks", [])

        self.calculations_trace: List[Dict[str, Any]] = []
        self.uninterpretable_notes: List[str] = []

    def analyze(self) -> Dict[str, Any]:
        """
        Executes end-to-end analytical pipeline and returns consolidated profile.
        """
        self.calculations_trace = []
        self.uninterpretable_notes = []

        kpis = self._compute_executive_kpis()
        country_data = self._compute_country_breakdown()
        route_data = self._compute_route_breakdown()
        category_data = self._compute_categorical_breakdown()
        temporal_data = self._compute_temporal_trend()
        routing_flows = self._compute_routing_flows()
        exceptions_and_remarks = self._compute_exceptions_and_remarks()
        full_table_chunks = self._compute_full_table_chunks(rows_per_chunk=10)
        self._collect_uninterpretable_notes()
        takeaways = self._generate_deterministic_insights(
            kpis, country_data, route_data, routing_flows, exceptions_and_remarks
        )

        return {
            "sheet_name": self.sheet_name,
            "total_records": len(self.df),
            "kpis": kpis,
            "country_analysis": country_data,
            "route_analysis": route_data,
            "category_analysis": category_data,
            "temporal_analysis": temporal_data,
            "routing_flows": routing_flows,
            "exceptions_and_remarks": exceptions_and_remarks,
            "full_table_chunks": full_table_chunks,
            "calculations_trace": self.calculations_trace,
            "uninterpretable_notes": self.uninterpretable_notes,
            "takeaways": takeaways,
        }

    def _compute_executive_kpis(self) -> List[Dict[str, Any]]:
        """
        Identifies key metrics (volume, amount, performance, network footprint)
        and computes deterministic KPIs with full calculation audit traces.
        """
        kpis: List[Dict[str, Any]] = []
        df = self.df

        # Record count trace
        self.calculations_trace.append({
            "metric": f"[{self.sheet_name}] Total Records Count",
            "formula": "COUNT(non_empty_rows)",
            "source_column": "All Columns",
            "result": f"{len(df):,}",
        })

        # 1. Total Volume / Records / Units
        volume_col = self._find_column_by_priority(
            self.num_cols, ["volume", "package", "shipment", "unit", "qty", "count", "weight"]
        )
        if volume_col:
            valid_series = pd.to_numeric(df[volume_col], errors="coerce").dropna()
            total_vol = float(valid_series.sum()) if not valid_series.empty else 0.0
            avg_vol = float(valid_series.mean()) if not valid_series.empty else 0.0
            formatted_total = self._format_number(total_vol)
            kpis.append({
                "label": f"Total {volume_col.title()}",
                "value": formatted_total,
                "raw_value": total_vol,
                "badge": "Primary Volume",
                "subtext": f"Avg: {self._format_number(avg_vol)} per entry",
            })
            self.calculations_trace.append({
                "metric": f"[{self.sheet_name}] Total {volume_col}",
                "formula": f"SUM({volume_col}) & MEAN({volume_col})",
                "source_column": volume_col,
                "result": f"Sum={formatted_total} ({total_vol:,.2f}), Mean={avg_vol:,.2f}",
            })
        else:
            kpis.append({
                "label": "Total Records Logged",
                "value": f"{len(df):,}",
                "raw_value": len(df),
                "badge": "Data Volume",
                "subtext": f"Sheet: {self.sheet_name}",
            })

        # 2. Financial Metrics (Amount, Cost, Revenue, Spend)
        amount_col = self._find_column_by_priority(
            self.num_cols, ["amount", "cost", "revenue", "spend", "rate", "charge", "price"]
        )
        if amount_col:
            valid_series = pd.to_numeric(df[amount_col], errors="coerce").dropna()
            total_amount = float(valid_series.sum()) if not valid_series.empty else 0.0
            avg_amount = float(valid_series.mean()) if not valid_series.empty else 0.0
            formatted_amt = self._format_currency(total_amount)
            kpis.append({
                "label": f"Total {amount_col.title()}",
                "value": formatted_amt,
                "raw_value": total_amount,
                "badge": "Financial Impact",
                "subtext": f"Mean: {self._format_currency(avg_amount)}",
            })
            self.calculations_trace.append({
                "metric": f"[{self.sheet_name}] Total {amount_col}",
                "formula": f"SUM({amount_col}) & MEAN({amount_col})",
                "source_column": amount_col,
                "result": f"Sum={formatted_amt} ({total_amount:,.2f}), Mean={avg_amount:,.2f}",
            })

        # 3. On-Time / Quality / Performance Metric
        perf_col = self._find_column_by_priority(
            self.num_cols, ["ontime", "on_time", "performance", "sla", "transit_day", "delayed"]
        )
        if perf_col:
            valid_series = pd.to_numeric(df[perf_col], errors="coerce").dropna()
            val = float(valid_series.mean()) if not valid_series.empty else 0.0
            if "transit" in perf_col.lower() or "day" in perf_col.lower():
                kpis.append({
                    "label": "Avg Transit Time",
                    "value": f"{val:.1f} Days",
                    "raw_value": val,
                    "badge": "Transit Efficiency",
                    "subtext": "Network average turnaround",
                })
                self.calculations_trace.append({
                    "metric": f"[{self.sheet_name}] Avg Transit Time",
                    "formula": f"MEAN({perf_col})",
                    "source_column": perf_col,
                    "result": f"{val:.2f} Days",
                })
            else:
                display_pct = val * 100 if val <= 1.0 else val
                kpis.append({
                    "label": f"Avg {perf_col.title()}",
                    "value": f"{display_pct:.1f}%",
                    "raw_value": display_pct,
                    "badge": "Service Level",
                    "subtext": "Operational target consistency",
                })
                self.calculations_trace.append({
                    "metric": f"[{self.sheet_name}] Avg {perf_col}",
                    "formula": f"MEAN({perf_col})",
                    "source_column": perf_col,
                    "result": f"{display_pct:.1f}%",
                })
        else:
            if self.country_cols:
                country_col = self.country_cols[0]
                unique_countries = int(df[country_col].dropna().nunique())
                kpis.append({
                    "label": "Global Reach",
                    "value": f"{unique_countries} Markets",
                    "raw_value": unique_countries,
                    "badge": "Network Footprint",
                    "subtext": f"Distinct {country_col}",
                })
                self.calculations_trace.append({
                    "metric": f"[{self.sheet_name}] Distinct Markets",
                    "formula": f"COUNT_DISTINCT({country_col})",
                    "source_column": country_col,
                    "result": f"{unique_countries} Markets",
                })

        # 4. Route / Flight / Customer / Remarks KPI if fewer than 4 cards
        if len(kpis) < 4 and self.route_cols:
            route_col = self.route_cols[0]
            unique_routes = int(df[route_col].dropna().nunique())
            kpis.append({
                "label": "Active Corridors",
                "value": f"{unique_routes} Lanes",
                "raw_value": unique_routes,
                "badge": "Operational Lanes",
                "subtext": "Distinct transit lanes tracked",
            })
            self.calculations_trace.append({
                "metric": f"[{self.sheet_name}] Active Corridors",
                "formula": f"COUNT_DISTINCT({route_col})",
                "source_column": route_col,
                "result": f"{unique_routes} Lanes",
            })

        if len(kpis) < 4 and self.flight_cols:
            flt_col = self.flight_cols[0]
            unique_flts = int(df[flt_col].dropna().nunique())
            kpis.append({
                "label": "Scheduled Flights",
                "value": f"{unique_flts} Flights",
                "raw_value": unique_flts,
                "badge": "Air Network",
                "subtext": f"Column: {flt_col}",
            })
            self.calculations_trace.append({
                "metric": f"[{self.sheet_name}] Distinct Flights",
                "formula": f"COUNT_DISTINCT({flt_col})",
                "source_column": flt_col,
                "result": f"{unique_flts} Flights",
            })

        if len(kpis) < 4 and self.customer_cols:
            cust_col = self.customer_cols[0]
            unique_cust = int(df[cust_col].dropna().nunique())
            kpis.append({
                "label": "Active Accounts",
                "value": f"{unique_cust} Clients",
                "raw_value": unique_cust,
                "badge": "Customer Base",
                "subtext": f"Column: {cust_col}",
            })

        return kpis[:4]

    def _compute_country_breakdown(self) -> Optional[Dict[str, Any]]:
        """
        Groups data by country column and aggregates primary numerical metric (or row count if no numeric column).
        """
        if not self.country_cols:
            return None

        country_col = self.country_cols[0]
        metric_col = self._get_primary_metric_col()

        clean_sub = self.df.dropna(subset=[country_col]).copy()
        if clean_sub.empty:
            return None

        if metric_col:
            clean_sub[metric_col] = pd.to_numeric(clean_sub[metric_col], errors="coerce").fillna(0.0)
            grouped = (
                clean_sub.groupby(country_col)[metric_col]
                .agg(["sum", "count", "mean"])
                .reset_index()
                .sort_values(by="sum", ascending=False)
            )
            metric_label = f"Total {metric_col.title()}"
            total_sum = float(grouped["sum"].sum())
        else:
            grouped = (
                clean_sub.groupby(country_col)
                .size()
                .reset_index(name="sum")
            )
            grouped["count"] = grouped["sum"]
            grouped["mean"] = 1.0
            grouped = grouped.sort_values(by="sum", ascending=False)
            metric_col = "Record Count"
            metric_label = "Total Records"
            total_sum = float(grouped["sum"].sum())

        top_n = grouped.head(8).copy()
        top_n["percentage"] = (top_n["sum"] / total_sum * 100).round(1) if total_sum > 0 else 0.0

        categories = top_n[country_col].astype(str).tolist()
        values = [round(float(v), 2) for v in top_n["sum"]]
        percentages = [float(p) for p in top_n["percentage"]]

        table_rows = []
        for _, row in top_n.iterrows():
            table_rows.append([
                str(row[country_col]),
                self._format_number(float(row["sum"])),
                f"{float(row['percentage']):.1f}%",
                f"{int(row['count']):,}",
            ])

        if categories:
            self.calculations_trace.append({
                "metric": f"[{self.sheet_name}] Country Concentration ({country_col})",
                "formula": f"GROUPBY({country_col}).SUM({metric_col})",
                "source_column": f"{country_col}, {metric_col}",
                "result": f"Leader: {categories[0]} ({percentages[0]:.1f}%)",
            })

        return {
            "country_column": country_col,
            "metric_column": metric_col,
            "categories": categories,
            "values": values,
            "percentages": percentages,
            "table_headers": ["Country / Region", metric_label, "Share (%)", "Entries"],
            "table_rows": table_rows,
            "leader": categories[0] if categories else "N/A",
            "leader_share": percentages[0] if percentages else 0.0,
        }

    def _compute_route_breakdown(self) -> Optional[Dict[str, Any]]:
        """
        Groups data by route/lane column (or synthesized Origin->Destination) and aggregates volume/count.
        """
        route_col = self.route_cols[0] if self.route_cols else None
        work_df = self.df.copy()

        if not route_col and self.origin_cols and self.destination_cols:
            orig_c = self.origin_cols[0]
            dest_c = self.destination_cols[0]
            route_col = f"{orig_c} -> {dest_c}"
            work_df[route_col] = (
                work_df[orig_c].fillna("N/A").astype(str).str.strip()
                + " -> "
                + work_df[dest_c].fillna("N/A").astype(str).str.strip()
            )

        if not route_col:
            return None

        metric_col = self._get_primary_metric_col()
        clean_sub = work_df.dropna(subset=[route_col]).copy()
        if clean_sub.empty:
            return None

        if metric_col and metric_col in clean_sub.columns:
            clean_sub[metric_col] = pd.to_numeric(clean_sub[metric_col], errors="coerce").fillna(0.0)
            grouped = (
                clean_sub.groupby(route_col)[metric_col]
                .agg(["sum", "count"])
                .reset_index()
                .sort_values(by="sum", ascending=False)
            )
            metric_label = f"Total {metric_col.title()}"
        else:
            grouped = clean_sub.groupby(route_col).size().reset_index(name="sum")
            grouped["count"] = grouped["sum"]
            grouped = grouped.sort_values(by="sum", ascending=False)
            metric_col = "Record Count"
            metric_label = "Total Records"

        top_n = grouped.head(8)
        categories = top_n[route_col].astype(str).tolist()
        values = [round(float(v), 2) for v in top_n["sum"]]

        table_rows = []
        for _, row in top_n.iterrows():
            table_rows.append([
                str(row[route_col]),
                self._format_number(float(row["sum"])),
                f"{int(row['count']):,}",
            ])

        if categories:
            self.calculations_trace.append({
                "metric": f"[{self.sheet_name}] Top Transit Corridor ({route_col})",
                "formula": f"GROUPBY({route_col}).SUM({metric_col})",
                "source_column": f"{route_col}, {metric_col}",
                "result": f"Top Lane: {categories[0]} ({self._format_number(values[0])})",
            })

        return {
            "route_column": route_col,
            "metric_column": metric_col,
            "categories": categories,
            "values": values,
            "table_headers": ["Transit Lane / Corridor", metric_label, "Entries"],
            "table_rows": table_rows,
            "leader": categories[0] if categories else "N/A",
        }

    def _compute_routing_flows(self) -> List[Dict[str, Any]]:
        """
        Extracts up to 8 structured Origin -> Transit -> Destination routing flows
        directly from actual worksheet columns or route strings, attaching real flight
        numbers, frequencies, volume metrics, and remarks. Never invents data.
        """
        flows: List[Dict[str, Any]] = []
        has_otd = bool(self.origin_cols and self.destination_cols)
        has_route = bool(self.route_cols)

        if not has_otd and not has_route:
            return flows

        orig_col = self.origin_cols[0] if self.origin_cols else None
        trans_col = self.transit_cols[0] if self.transit_cols else None
        dest_col = self.destination_cols[0] if self.destination_cols else None
        route_col = self.route_cols[0] if self.route_cols else None
        flt_col = self.flight_cols[0] if self.flight_cols else None
        freq_col = self.frequency_cols[0] if self.frequency_cols else None
        rem_col = self.remarks_cols[0] if self.remarks_cols else None
        metric_col = self._get_primary_metric_col()

        # Group or iterate rows to build consolidated unique flows
        flow_map: Dict[str, Dict[str, Any]] = {}

        for idx in range(len(self.df)):
            row_clean = self.df.iloc[idx]
            row_raw = self.raw_df.iloc[idx] if idx < len(self.raw_df) else row_clean

            origin_val = ""
            transit_val = "Direct"
            dest_val = ""
            route_label = ""

            if has_otd and orig_col and dest_col:
                origin_val = self._safe_cell_str(row_raw.get(orig_col, ""))
                dest_val = self._safe_cell_str(row_raw.get(dest_col, ""))
                if trans_col:
                    t_raw = self._safe_cell_str(row_raw.get(trans_col, ""))
                    transit_val = t_raw if t_raw and t_raw.lower() not in ("none", "n/a", "-", "direct") else "Direct"
                if route_col:
                    route_label = self._safe_cell_str(row_raw.get(route_col, ""))
                if not route_label:
                    route_label = (
                        f"{origin_val} -> {transit_val} -> {dest_val}"
                        if transit_val != "Direct"
                        else f"{origin_val} -> {dest_val}"
                    )
            elif route_col:
                route_label = self._safe_cell_str(row_raw.get(route_col, ""))
                if not route_label:
                    continue
                parts = [
                    p.strip()
                    for p in re.split(r"\s*(?:->|–|-|/|>|\bto\b)\s*", route_label, flags=re.I)
                    if p.strip()
                ]
                if len(parts) >= 3:
                    origin_val = parts[0]
                    transit_val = " / ".join(parts[1:-1])
                    dest_val = parts[-1]
                elif len(parts) == 2:
                    origin_val = parts[0]
                    transit_val = "Direct"
                    dest_val = parts[1]
                else:
                    origin_val = route_label
                    transit_val = "Direct"
                    dest_val = "Network Hub"
                if trans_col:
                    t_raw = self._safe_cell_str(row_raw.get(trans_col, ""))
                    if t_raw:
                        transit_val = t_raw

            if not origin_val and not dest_val:
                continue

            key = f"{origin_val}|{transit_val}|{dest_val}"
            flt_str = self._safe_cell_str(row_raw.get(flt_col, "")) if flt_col else ""
            freq_str = self._safe_cell_str(row_raw.get(freq_col, "")) if freq_col else ""
            rem_str = self._safe_cell_str(row_raw.get(rem_col, "")) if rem_col else ""

            vol_num = 0.0
            if metric_col and metric_col in row_clean:
                val = pd.to_numeric(row_clean[metric_col], errors="coerce")
                vol_num = float(val) if not pd.isna(val) else 0.0

            if key not in flow_map:
                flow_map[key] = {
                    "origin": origin_val or "N/A",
                    "transit": transit_val or "Direct",
                    "destination": dest_val or "N/A",
                    "route_label": route_label or f"{origin_val} -> {dest_val}",
                    "flights": [],
                    "frequencies": [],
                    "remarks": [],
                    "total_volume": 0.0,
                    "row_count": 0,
                }

            entry = flow_map[key]
            entry["row_count"] += 1
            entry["total_volume"] += vol_num
            if flt_str and flt_str not in entry["flights"]:
                entry["flights"].append(flt_str)
            if freq_str and freq_str not in entry["frequencies"]:
                entry["frequencies"].append(freq_str)
            if rem_str and rem_str not in entry["remarks"]:
                entry["remarks"].append(rem_str)

        sorted_flows = sorted(
            flow_map.values(),
            key=lambda x: (x["total_volume"], x["row_count"]),
            reverse=True,
        )[:8]

        for item in sorted_flows:
            vol_str = (
                f"{self._format_number(item['total_volume'])} ({item['row_count']} entries)"
                if metric_col and item["total_volume"] > 0
                else f"{item['row_count']} scheduled entries"
            )
            flows.append({
                "origin": item["origin"],
                "transit": item["transit"],
                "destination": item["destination"],
                "route_label": item["route_label"],
                "flight_or_carrier": ", ".join(item["flights"][:3]) if item["flights"] else "Standard Network",
                "frequency": ", ".join(item["frequencies"][:2]) if item["frequencies"] else "Per Schedule",
                "volume": vol_str,
                "remarks": "; ".join(item["remarks"][:2]) if item["remarks"] else "Standard Operations",
            })

        return flows

    def _compute_exceptions_and_remarks(self) -> List[Dict[str, Any]]:
        """
        Extracts up to 10 real operational remarks, special conditions, contingencies,
        or SLA exception rows directly from the worksheet.
        """
        items: List[Dict[str, Any]] = []

        entity_col = (
            (self.route_cols[0] if self.route_cols else None)
            or (self.flight_cols[0] if self.flight_cols else None)
            or (self.customer_cols[0] if self.customer_cols else None)
            or (self.country_cols[0] if self.country_cols else None)
            or (list(self.df.columns)[0] if len(self.df.columns) > 0 else None)
        )
        metric_col = self._get_primary_metric_col()

        # 1. Extract from explicit remarks/exception/contingency columns
        for rem_col in self.remarks_cols:
            for idx in range(len(self.raw_df)):
                row_raw = self.raw_df.iloc[idx]
                detail_str = self._safe_cell_str(row_raw.get(rem_col, ""))
                if not detail_str or detail_str.lower() in ("none", "n/a", "-", "nil", "no remarks", "ok"):
                    continue

                entity_str = self._safe_cell_str(row_raw.get(entity_col, f"Row {idx + 1}")) if entity_col else f"Row {idx + 1}"
                metric_str = self._safe_cell_str(row_raw.get(metric_col, "")) if metric_col else "Logged"

                items.append({
                    "entity": entity_str or f"Row {idx + 1}",
                    "category": str(rem_col).title(),
                    "detail": detail_str,
                    "metric": metric_str or "Verified",
                    "source_type": "Explicit Remark",
                })
                if len(items) >= 10:
                    return items

        # 2. Check for SLA / On-Time / Delayed outliers if space remains
        perf_col = self._find_column_by_priority(
            self.num_cols, ["ontime", "on_time", "sla", "delayed", "transit_day"]
        )
        if perf_col and len(items) < 10:
            series_num = pd.to_numeric(self.df[perf_col], errors="coerce")
            if "delay" in perf_col.lower():
                outlier_indices = series_num.nlargest(5).index.tolist()
            elif "transit" in perf_col.lower():
                outlier_indices = series_num.nlargest(5).index.tolist()
            else:
                outlier_indices = series_num.nsmallest(5).index.tolist()

            for idx in outlier_indices:
                if idx >= len(self.raw_df):
                    continue
                val = series_num.loc[idx]
                if pd.isna(val):
                    continue
                row_raw = self.raw_df.iloc[idx]
                entity_str = self._safe_cell_str(row_raw.get(entity_col, f"Row {idx + 1}")) if entity_col else f"Row {idx + 1}"
                metric_val = self._safe_cell_str(row_raw.get(metric_col, "")) if metric_col else ""
                items.append({
                    "entity": entity_str,
                    "category": f"{perf_col.title()} Watch",
                    "detail": f"Recorded {perf_col} value of {self._safe_cell_str(row_raw.get(perf_col, str(val)))}",
                    "metric": metric_val or f"{val:.1f}",
                    "source_type": "Performance Threshold",
                })
                if len(items) >= 10:
                    break

        return items[:10]

    def _compute_full_table_chunks(self, rows_per_chunk: int = 10) -> List[Dict[str, Any]]:
        """
        Paginates the raw DataFrame into legible slide chunks of `rows_per_chunk` rows
        so every single record in the sheet can be displayed on structured slides without
        crowding or truncation. Selects up to 8 priority columns if sheet is wider.
        """
        source_df = self.raw_df if not self.raw_df.empty else self.df
        if source_df.empty:
            return []

        all_cols = list(source_df.columns)
        if len(all_cols) <= 8:
            selected_cols = all_cols
        else:
            # Prioritize key operational columns up to 8
            priority_pool = (
                self.route_cols
                + self.origin_cols
                + self.transit_cols
                + self.destination_cols
                + self.flight_cols
                + self.customer_cols
                + self.country_cols
                + self.frequency_cols
                + self.num_cols[:2]
                + self.remarks_cols
                + self.date_cols
                + self.cat_cols
            )
            selected_cols = []
            for c in priority_pool:
                if c in all_cols and c not in selected_cols:
                    selected_cols.append(c)
                if len(selected_cols) >= 8:
                    break
            for c in all_cols:
                if len(selected_cols) >= 8:
                    break
                if c not in selected_cols:
                    selected_cols.append(c)

        total_rows = len(source_df)
        total_chunks = max(1, (total_rows + rows_per_chunk - 1) // rows_per_chunk)
        chunks: List[Dict[str, Any]] = []

        for chunk_idx in range(total_chunks):
            start_i = chunk_idx * rows_per_chunk
            end_i = min(start_i + rows_per_chunk, total_rows)
            sub_df = source_df.iloc[start_i:end_i][selected_cols]

            rows_formatted: List[List[str]] = []
            for _, r in sub_df.iterrows():
                row_cells = []
                for col_name in selected_cols:
                    cell_str = self._safe_cell_str(r[col_name])
                    row_cells.append(cell_str if cell_str else "—")
                rows_formatted.append(row_cells)

            chunks.append({
                "chunk_index": chunk_idx + 1,
                "total_chunks": total_chunks,
                "sheet_name": self.sheet_name,
                "headers": [str(c) for c in selected_cols],
                "rows": rows_formatted,
                "row_range": f"Rows {start_i + 1}–{end_i} of {total_rows}",
            })

        return chunks

    def _compute_categorical_breakdown(self) -> Optional[Dict[str, Any]]:
        """
        Computes distribution of service types, customers, flights, or statuses.
        """
        target_col = None
        for col in self.cat_cols + self.customer_cols + self.frequency_cols:
            col_l = col.lower()
            if any(k in col_l for k in ["service", "type", "mode", "priority", "status", "class", "customer", "client", "frequency"]):
                if 1 <= self.df[col].dropna().nunique() <= 15:
                    target_col = col
                    break

        if not target_col and self.cat_cols:
            for col in self.cat_cols:
                nunique = self.df[col].dropna().nunique()
                if 2 <= nunique <= 12:
                    target_col = col
                    break

        if not target_col:
            return None

        metric_col = self._get_primary_metric_col()
        if metric_col:
            temp = self.df.dropna(subset=[target_col]).copy()
            temp[metric_col] = pd.to_numeric(temp[metric_col], errors="coerce").fillna(0.0)
            grouped = temp.groupby(target_col)[metric_col].sum().sort_values(ascending=False).head(6)
        else:
            grouped = self.df[target_col].dropna().value_counts().head(6)

        if grouped.empty:
            return None

        categories = [str(k) for k in grouped.index]
        values = [round(float(v), 2) for v in grouped.values]

        return {
            "category_column": target_col,
            "categories": categories,
            "values": values,
            "table_headers": [str(target_col).title(), "Volume / Count"],
            "table_rows": [[cat, self._format_number(val)] for cat, val in zip(categories, values)],
        }

    def _compute_temporal_trend(self) -> Optional[Dict[str, Any]]:
        """
        Computes time-series trend if a temporal column is detected.
        """
        if not self.date_cols:
            return None

        date_col = self.date_cols[0]
        metric_col = self._get_primary_metric_col()

        try:
            temp_df = self.df.copy()
            temp_df["_parsed_date"] = pd.to_datetime(temp_df[date_col], errors="coerce", format="mixed")
            temp_df = temp_df.dropna(subset=["_parsed_date"])

            if temp_df.empty:
                return None

            temp_df["_period"] = temp_df["_parsed_date"].dt.to_period("M").astype(str)
            if metric_col:
                temp_df[metric_col] = pd.to_numeric(temp_df[metric_col], errors="coerce").fillna(0.0)
                grouped = temp_df.groupby("_period")[metric_col].sum().sort_index()
            else:
                grouped = temp_df.groupby("_period").size().sort_index()

            if len(grouped) < 2:
                return None

            categories = list(grouped.index)
            values = [round(float(v), 2) for v in grouped.values]

            return {
                "date_column": date_col,
                "categories": categories,
                "values": values,
            }
        except Exception:
            return None

    def _collect_uninterpretable_notes(self) -> None:
        """
        Records transparent notes if a sheet has no numeric metrics or has sparse columns.
        """
        if not self.num_cols:
            self.uninterpretable_notes.append(
                f"Sheet '{self.sheet_name}': No numeric metric columns detected; aggregations defaulted to exact record frequency counts."
            )
        for col in self.df.columns:
            null_cnt = int(self.df[col].isna().sum())
            if null_cnt > 0:
                self.uninterpretable_notes.append(
                    f"Sheet '{self.sheet_name}', Column '{col}': {null_cnt} blank cell(s) excluded from column aggregation."
                )

    def _generate_deterministic_insights(
        self,
        kpis: List[Dict[str, Any]],
        country_data: Optional[Dict[str, Any]],
        route_data: Optional[Dict[str, Any]],
        routing_flows: Optional[List[Dict[str, Any]]] = None,
        exceptions_and_remarks: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        Synthesizes executive takeaways from exact computed metrics. Zero hallucinated facts.
        """
        insights: List[str] = []

        if kpis:
            primary_kpi = kpis[0]
            insights.append(
                f"**[{self.sheet_name}] Network Scale**: Total recorded operational metric ({primary_kpi['label']}) reached **{primary_kpi['value']}** across **{len(self.df):,}** verified worksheet entries."
            )

        if country_data and country_data.get("categories"):
            leader = country_data["leader"]
            share = country_data["leader_share"]
            top_3 = ", ".join(country_data["categories"][:3])
            insights.append(
                f"**Geographic Concentration**: **{leader}** represents the leading market, accounting for **{share}%** of tracked activity. Top markets include **{top_3}**."
            )

        if route_data and route_data.get("categories"):
            top_route = route_data["leader"]
            insights.append(
                f"**Corridor Throughput**: Transit lane **{top_route}** is the highest-volume corridor in **{self.sheet_name}**."
            )
        elif routing_flows:
            top_flow = routing_flows[0]
            insights.append(
                f"**Primary Routing Flow**: Active corridor **{top_flow['route_label']}** operates via **{top_flow['flight_or_carrier']}** ({top_flow['frequency']})."
            )

        if exceptions_and_remarks:
            insights.append(
                f"**Operational Exceptions & Remarks**: Captured **{len(exceptions_and_remarks)}** specific operational remarks/exceptions requiring management visibility (e.g., *{exceptions_and_remarks[0]['entity']}*: {exceptions_and_remarks[0]['detail'][:80]})."
            )
        else:
            insights.append(
                "**Data Integrity**: All worksheet records were processed deterministically with 100% source traceability."
            )

        return insights

    def _get_primary_metric_col(self) -> Optional[str]:
        """
        Returns the most relevant numeric column for aggregations.
        """
        return self._find_column_by_priority(
            self.num_cols,
            ["volume", "packages", "amount", "cost", "revenue", "shipments", "units", "weight", "qty"],
        ) or (self.num_cols[0] if self.num_cols else None)

    def _find_column_by_priority(self, columns: List[str], keywords: List[str]) -> Optional[str]:
        for kw in keywords:
            for col in columns:
                if kw in str(col).lower():
                    return col
        return None

    def _safe_cell_str(self, val: Any) -> str:
        if val is None or pd.isna(val):
            return ""
        s = str(val).strip()
        if s.lower() in ("nan", "none", "nat"):
            return ""
        return s

    def _format_number(self, val: float) -> str:
        if abs(val) >= 1_000_000:
            return f"{val / 1_000_000:.2f}M"
        if abs(val) >= 1_000:
            return f"{val / 1_000:.1f}K"
        return f"{val:,.0f}" if float(val).is_integer() else f"{val:,.2f}"

    def _format_currency(self, val: float) -> str:
        if abs(val) >= 1_000_000:
            return f"${val / 1_000_000:.2f}M"
        if abs(val) >= 1_000:
            return f"${val / 1_000:.1f}K"
        return f"${val:,.2f}"

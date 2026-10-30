"""
backend/services/pptx_builder.py
--------------------------------
Approved UPS Corporate PowerPoint Generator using python-pptx.
Independent from the Patel'Spark website theme.

Renders 16:9 widescreen presentations with the approved UPS corporate design:
- Authorised UPS Shield logo on the cover slide, content headers, and closing slide.
- Subtle UPS watermark on EVERY slide (non-interfering opacity and placement).
- Official UPS corporate colours (Pullman Brown #351C15, UPS Gold #FFB500, Warm Cream #FAF8F5).
- Source distinction pill badges ("Original Source Data", "Deterministic Calculation", "Executive Summary").
- Editable native PowerPoint charts, tables, KPI cards, Origin->Transit->Destination routing
  flow diagrams, operational exceptions/remarks matrices, and paginated source data tables.
"""

from pathlib import Path
from typing import Dict, Any, List

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

from backend.config import (
    UPS_LOGO_PATH,
    UPS_WATERMARK_PATH,
    CUSTOM_TEMPLATE_PATH,
    UPS_PPTX_COLORS,
    PPTX_WIDTH_INCHES,
    PPTX_HEIGHT_INCHES,
    GENERATED_DIR,
)


class PPTXBuilderService:
    """
    Renders structured presentation plans into 16:9 PowerPoint files
    strictly following the approved UPS corporate presentation design.
    """

    def __init__(self, plan: List[Dict[str, Any]], presentation_title: str):
        self.plan = plan
        self.title = presentation_title
        self.total_slides = len(plan)

        # Verify required authorised UPS brand assets exist
        if not UPS_LOGO_PATH.exists():
            raise FileNotFoundError(
                f"Required authorised UPS logo asset is missing at: {UPS_LOGO_PATH}. "
                "Please provide the approved UPS logo before generating presentations."
            )
        if not UPS_WATERMARK_PATH.exists():
            raise FileNotFoundError(
                f"Required authorised UPS watermark asset is missing at: {UPS_WATERMARK_PATH}. "
                "Please provide the approved UPS watermark before generating presentations."
            )

        # Initialize Presentation (use custom template if uploaded, else 16:9 widescreen master)
        if CUSTOM_TEMPLATE_PATH.exists():
            try:
                self.prs = Presentation(str(CUSTOM_TEMPLATE_PATH))
            except Exception:
                self.prs = Presentation()
        else:
            self.prs = Presentation()

        self.prs.slide_width = Inches(PPTX_WIDTH_INCHES)
        self.prs.slide_height = Inches(PPTX_HEIGHT_INCHES)
        self.blank_layout = (
            self.prs.slide_layouts[6]
            if len(self.prs.slide_layouts) > 6
            else self.prs.slide_layouts[0]
        )

        # Approved UPS Corporate Color Palette
        self.c_brown = RGBColor(*UPS_PPTX_COLORS["UPS_BROWN"])
        self.c_dark_brown = RGBColor(*UPS_PPTX_COLORS["UPS_DARK_BROWN"])
        self.c_gold = RGBColor(*UPS_PPTX_COLORS["UPS_GOLD"])
        self.c_gold_dark = RGBColor(*UPS_PPTX_COLORS["UPS_GOLD_DARK"])
        self.c_cream = RGBColor(*UPS_PPTX_COLORS["WARM_CREAM"])
        self.c_row_alt = RGBColor(*UPS_PPTX_COLORS["WARM_ROW_ALT"])
        self.c_charcoal = RGBColor(*UPS_PPTX_COLORS["CHARCOAL"])
        self.c_slate = RGBColor(*UPS_PPTX_COLORS["SLATE_GRAY"])
        self.c_border = RGBColor(*UPS_PPTX_COLORS["BORDER_LIGHT"])
        self.c_white = RGBColor(*UPS_PPTX_COLORS["WHITE"])

    def build(self, output_filename: str) -> Path:
        """
        Builds the complete UPS-branded PowerPoint presentation and saves it to disk.
        """
        for slide_data in self.plan:
            layout_type = slide_data.get("layout_type")
            slide = self.prs.slides.add_slide(self.blank_layout)

            if layout_type == "title":
                self._render_title_slide(slide, slide_data)
            elif layout_type == "closing":
                self._render_closing_slide(slide, slide_data)
            elif layout_type == "kpi_summary":
                self._render_kpi_summary_slide(slide, slide_data)
            elif layout_type == "consolidated_dashboard":
                self._render_consolidated_dashboard(slide, slide_data)
            elif layout_type in ["country_analysis", "route_performance"]:
                self._render_analysis_slide(slide, slide_data)
            elif layout_type in ["trend_analysis", "distribution_analysis"]:
                self._render_trend_distribution_slide(slide, slide_data)
            elif layout_type == "route_flow_diagram":
                self._render_route_flow_slide(slide, slide_data)
            elif layout_type == "exceptions_remarks":
                self._render_exceptions_remarks_slide(slide, slide_data)
            elif layout_type == "full_data_table":
                self._render_full_data_table_slide(slide, slide_data)
            else:
                self._render_generic_slide(slide, slide_data)

        output_path = GENERATED_DIR / output_filename
        self.prs.save(str(output_path))
        return output_path

    # =========================================================================
    # SLIDE LAYOUTS (UPS CORPORATE DESIGN SYSTEM)
    # =========================================================================

    def _render_title_slide(self, slide, data: Dict[str, Any]):
        """
        Opening Cover Slide:
        - Deep UPS Brown corporate background & Gold structural accents.
        - Subtle UPS watermark in background.
        - Prominent authorised UPS Shield logo.
        - Presentation title, reporting period, sheets included, and operational metadata.
        """
        # 1. Full Slide Background: UPS Corporate Brown
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.c_brown
        bg.line.fill.background()

        # 2. Left UPS Gold Structural Accent Bar
        gold_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.42), Inches(7.5))
        gold_bar.fill.solid()
        gold_bar.fill.fore_color.rgb = self.c_gold
        gold_bar.line.fill.background()

        # 3. Inner Executive Frame Card
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(0.95), Inches(0.75), Inches(11.6), Inches(6.0),
        )
        card.fill.solid()
        card.fill.fore_color.rgb = self.c_dark_brown
        card.line.color.rgb = self.c_gold
        card.line.width = Pt(1.75)

        # 4. UPS Watermark on Cover Slide (right side, subtle behind content)
        slide.shapes.add_picture(
            str(UPS_WATERMARK_PATH),
            Inches(8.5), Inches(1.2), height=Inches(5.0),
        )

        # 5. Prominent Authorised UPS Shield Logo on Cover Slide
        slide.shapes.add_picture(
            str(UPS_LOGO_PATH),
            Inches(1.65), Inches(1.25), height=Inches(1.45),
        )

        # 6. Corporate Category Pill Badge
        badge = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(3.25), Inches(1.65), Inches(3.8), Inches(0.45),
        )
        badge.fill.solid()
        badge.fill.fore_color.rgb = self.c_gold
        badge.line.fill.background()
        tf_b = badge.text_frame
        tf_b.word_wrap = True
        p_b = tf_b.paragraphs[0]
        p_b.text = "UPS OPERATIONS & LOGISTICS REVIEW"
        p_b.font.name = "Segoe UI"
        p_b.font.size = Pt(10)
        p_b.font.bold = True
        p_b.font.color.rgb = self.c_brown
        p_b.alignment = PP_ALIGN.CENTER

        # 7. Main Presentation Title
        tx_box = slide.shapes.add_textbox(Inches(1.65), Inches(2.9), Inches(10.0), Inches(2.1))
        tf = tx_box.text_frame
        tf.word_wrap = True
        p_title = tf.paragraphs[0]
        p_title.text = data.get("title", self.title)
        p_title.font.name = "Segoe UI"
        p_title.font.size = Pt(32)
        p_title.font.bold = True
        p_title.font.color.rgb = self.c_white

        # Subtitle / Extracted Context
        p_sub = tf.add_paragraph()
        p_sub.text = data.get("subtitle", "Executive Operations & Performance Analysis")
        p_sub.font.name = "Segoe UI"
        p_sub.font.size = Pt(15)
        p_sub.font.color.rgb = RGBColor(235, 225, 215)
        p_sub.space_before = Pt(10)

        # 8. Bottom Gold Metadata Divider
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(1.65), Inches(5.35), Inches(10.1), Inches(0.03)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = self.c_gold
        line.line.fill.background()

        # 9. Extracted Reporting Period & Slide Count Metadata
        meta_box = slide.shapes.add_textbox(Inches(1.65), Inches(5.5), Inches(10.1), Inches(0.8))
        tf_m = meta_box.text_frame
        p_m = tf_m.paragraphs[0]
        dept = data.get("department", "Global Logistics & Operations Analytics")
        period = data.get("period", "Current Operational Period")
        p_m.text = f"{dept}   |   Reporting Period: {period}   |   Slide 1 of {self.total_slides}"
        p_m.font.name = "Segoe UI"
        p_m.font.size = Pt(11)
        p_m.font.bold = True
        p_m.font.color.rgb = self.c_gold

    def _render_closing_slide(self, slide, data: Dict[str, Any]):
        """
        Closing Slide:
        - UPS Corporate Brown background & Gold bottom accent bar.
        - Subtle UPS watermark.
        - Prominent centered UPS Shield logo.
        - Closing thank-you message & confidentiality footer.
        """
        # 1. Background: Deep UPS Corporate Brown
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.c_brown
        bg.line.fill.background()

        # 2. Top & Bottom UPS Gold Accent Bars
        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.15))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = self.c_gold
        top_bar.line.fill.background()

        bottom_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, Inches(7.2), Inches(13.333), Inches(0.3)
        )
        bottom_bar.fill.solid()
        bottom_bar.fill.fore_color.rgb = self.c_gold
        bottom_bar.line.fill.background()

        # 3. UPS Watermark on Closing Slide
        slide.shapes.add_picture(
            str(UPS_WATERMARK_PATH),
            Inches(9.0), Inches(1.4), height=Inches(4.8),
        )

        # 4. Prominent Centered UPS Shield Logo
        slide.shapes.add_picture(
            str(UPS_LOGO_PATH),
            Inches(5.95), Inches(1.35), height=Inches(1.65),
        )

        # 5. Closing Message Box
        tx_box = slide.shapes.add_textbox(Inches(1.5), Inches(3.25), Inches(10.333), Inches(2.8))
        tf = tx_box.text_frame
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = "Thank You"
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(38)
        p1.font.bold = True
        p1.font.color.rgb = self.c_white
        p1.alignment = PP_ALIGN.CENTER

        p2 = tf.add_paragraph()
        p2.text = f"{self.title}  •  Executive Operations Summary"
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(16)
        p2.font.bold = True
        p2.font.color.rgb = self.c_gold
        p2.alignment = PP_ALIGN.CENTER
        p2.space_before = Pt(10)

        p3 = tf.add_paragraph()
        confidentiality = data.get(
            "confidentiality",
            f"UPS Corporate Presentation  |  Verified Excel Data Analysis  |  Slide {data.get('slide_number', self.total_slides)} of {self.total_slides}",
        )
        p3.text = confidentiality
        p3.font.name = "Segoe UI"
        p3.font.size = Pt(10.5)
        p3.font.color.rgb = RGBColor(215, 205, 195)
        p3.alignment = PP_ALIGN.CENTER
        p3.space_before = Pt(28)

    def _render_kpi_summary_slide(self, slide, data: Dict[str, Any]):
        """
        Executive Summary Slide with 3-4 KPI Cards and strategic takeaway cards.
        """
        self._add_slide_chrome(slide, data)

        kpis = data.get("kpis", [])
        card_count = min(4, len(kpis))
        if card_count > 0:
            card_width = (Inches(11.8) - Inches(0.25) * (card_count - 1)) / card_count
            start_x = Inches(0.75)
            y = Inches(1.55)

            for i, kpi in enumerate(kpis[:card_count]):
                x = start_x + i * (card_width + Inches(0.25))
                self._add_kpi_card(slide, x, y, card_width, Inches(1.95), kpi)

        takeaways = data.get("takeaways", [])
        if takeaways:
            self._add_takeaways_card(
                slide, Inches(0.75), Inches(3.8), Inches(11.8), Inches(2.85), takeaways
            )

    def _render_consolidated_dashboard(self, slide, data: Dict[str, Any]):
        """
        Consolidated 2-slide executive dashboard: 3 KPI cards on top, chart + takeaways below.
        """
        self._add_slide_chrome(slide, data)

        kpis = data.get("kpis", [])
        card_count = min(3, len(kpis))
        if card_count > 0:
            card_width = (Inches(11.8) - Inches(0.3) * (card_count - 1)) / card_count
            start_x = Inches(0.75)
            y = Inches(1.45)

            for i, kpi in enumerate(kpis[:card_count]):
                x = start_x + i * (card_width + Inches(0.3))
                self._add_kpi_card(slide, x, y, card_width, Inches(1.5), kpi)

        chart_cfg = data.get("chart_config")
        if chart_cfg:
            self._add_chart(slide, Inches(0.75), Inches(3.15), Inches(6.8), Inches(3.5), chart_cfg)

        takeaways = data.get("takeaways", [])
        if takeaways:
            self._add_takeaways_card(
                slide, Inches(7.8), Inches(3.15), Inches(4.75), Inches(3.5), takeaways
            )

    def _render_analysis_slide(self, slide, data: Dict[str, Any]):
        """
        Country or Route analysis slide: Native Chart on left, Native Table on right, Takeaways bottom.
        """
        self._add_slide_chrome(slide, data)

        chart_cfg = data.get("chart_config")
        table_data = data.get("table_data")

        if chart_cfg:
            self._add_chart(slide, Inches(0.75), Inches(1.55), Inches(6.0), Inches(3.65), chart_cfg)

        if table_data:
            self._add_table(slide, Inches(7.0), Inches(1.55), Inches(5.55), Inches(3.65), table_data)

        takeaways = data.get("takeaways", [])
        if takeaways:
            self._add_takeaways_card(
                slide, Inches(0.75), Inches(5.4), Inches(11.8), Inches(1.3), takeaways
            )

    def _render_trend_distribution_slide(self, slide, data: Dict[str, Any]):
        """
        Time series trend or service distribution slide.
        """
        self._add_slide_chrome(slide, data)

        chart_cfg = data.get("chart_config")
        if chart_cfg:
            self._add_chart(slide, Inches(0.75), Inches(1.55), Inches(7.5), Inches(5.05), chart_cfg)

        takeaways = data.get("takeaways", [])
        if takeaways:
            self._add_takeaways_card(
                slide, Inches(8.5), Inches(1.55), Inches(4.05), Inches(5.05), takeaways
            )

    def _render_route_flow_slide(self, slide, data: Dict[str, Any]):
        """
        Origin -> Transit / Connection -> Destination Visual Routing & Flight Flow Slide.
        Displays up to 5 visual routing flow lanes horizontally across the slide with:
        - Origin Node Box (UPS Brown rounded rectangle with white bold text + Carrier/Flight badge)
        - RIGHT_ARROW Connector in UPS Gold
        - Transit / Connection Node Box (Warm white card with Gold border showing Transit Hub & Frequency)
        - RIGHT_ARROW Connector in UPS Gold
        - Destination Node Box (UPS Brown rounded rectangle with UPS Gold text)
        - Volume & Remarks Summary Box on the right showing exact volume/metric and operational remarks.
        """
        data.setdefault("source_badge", "Original Source Data")
        self._add_slide_chrome(slide, data)

        flows = data.get("routing_flows") or [
            {
                "origin": "Origin Gateway",
                "transit": "Primary Air/Ground Hub",
                "destination": "Destination Market",
                "flight_or_carrier": "UPS Worldwide Express",
                "frequency": "Daily Scheduled",
                "volume": "Verified Throughput",
                "remarks": "Active international freight corridor",
            }
        ]
        flows = flows[:5]

        # Column Header Labels Bar
        col_specs = [
            (Inches(0.65), Inches(2.35), "ORIGIN HUB / GATEWAY"),
            (Inches(3.45), Inches(2.75), "TRANSIT HUB & FREQUENCY"),
            (Inches(6.65), Inches(2.35), "DESTINATION MARKET"),
            (Inches(9.20), Inches(3.48), "VOLUME & SOURCE REMARKS"),
        ]
        for col_x, col_w, col_label in col_specs:
            hdr = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, col_x, Inches(1.26), col_w, Inches(0.32)
            )
            hdr.fill.solid()
            hdr.fill.fore_color.rgb = self.c_dark_brown
            hdr.line.color.rgb = self.c_gold
            hdr.line.width = Pt(0.75)
            tf_h = hdr.text_frame
            tf_h.word_wrap = True
            tf_h.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_h = tf_h.paragraphs[0]
            p_h.text = col_label
            p_h.font.name = "Segoe UI"
            p_h.font.size = Pt(8.5)
            p_h.font.bold = True
            p_h.font.color.rgb = self.c_gold
            p_h.alignment = PP_ALIGN.CENTER

        # Flow Rows
        num_rows = max(1, len(flows))
        avail_height = Inches(4.65)
        slot_h = avail_height / max(num_rows, 3)
        row_h = min(Inches(0.84), slot_h - Inches(0.10))
        start_y = Inches(1.68)

        for idx, flow in enumerate(flows):
            row_y = start_y + idx * slot_h
            arrow_y = row_y + (row_h - Inches(0.28)) / 2

            origin_txt = str(flow.get("origin", "Origin Hub"))
            carrier_txt = str(flow.get("flight_or_carrier", "UPS Network"))
            transit_txt = str(flow.get("transit", "Direct Connection"))
            freq_txt = str(flow.get("frequency", "Scheduled"))
            dest_txt = str(flow.get("destination", "Destination Hub"))
            vol_txt = str(flow.get("volume", "Verified Metric"))
            rem_txt = str(flow.get("remarks", "Standard operational routing"))

            # 1. Origin Node Box (UPS Brown rounded rectangle with white bold text + Carrier/Flight badge)
            orig_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.65), row_y, Inches(2.35), row_h
            )
            orig_box.fill.solid()
            orig_box.fill.fore_color.rgb = self.c_brown
            orig_box.line.color.rgb = self.c_gold
            orig_box.line.width = Pt(1)
            tf_o = orig_box.text_frame
            tf_o.word_wrap = True
            tf_o.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_o1 = tf_o.paragraphs[0]
            p_o1.text = origin_txt
            p_o1.font.name = "Segoe UI"
            p_o1.font.size = Pt(10.5)
            p_o1.font.bold = True
            p_o1.font.color.rgb = self.c_white
            p_o1.alignment = PP_ALIGN.CENTER

            p_o2 = tf_o.add_paragraph()
            p_o2.text = f"✈ {carrier_txt}"
            p_o2.font.name = "Segoe UI"
            p_o2.font.size = Pt(8.5)
            p_o2.font.bold = True
            p_o2.font.color.rgb = self.c_gold
            p_o2.alignment = PP_ALIGN.CENTER

            # 2. First Arrow Connector (RIGHT_ARROW in UPS Gold)
            arr1 = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW, Inches(3.06), arrow_y, Inches(0.33), Inches(0.28)
            )
            arr1.fill.solid()
            arr1.fill.fore_color.rgb = self.c_gold
            arr1.line.fill.background()

            # 3. Transit / Connection Node Box (Warm white card with Gold border)
            trans_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.45), row_y, Inches(2.75), row_h
            )
            trans_box.fill.solid()
            trans_box.fill.fore_color.rgb = self.c_white
            trans_box.line.color.rgb = self.c_gold
            trans_box.line.width = Pt(1.5)
            tf_tr = trans_box.text_frame
            tf_tr.word_wrap = True
            tf_tr.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_tr1 = tf_tr.paragraphs[0]
            p_tr1.text = transit_txt
            p_tr1.font.name = "Segoe UI"
            p_tr1.font.size = Pt(10)
            p_tr1.font.bold = True
            p_tr1.font.color.rgb = self.c_brown
            p_tr1.alignment = PP_ALIGN.CENTER

            p_tr2 = tf_tr.add_paragraph()
            p_tr2.text = freq_txt
            p_tr2.font.name = "Segoe UI"
            p_tr2.font.size = Pt(8.5)
            p_tr2.font.color.rgb = self.c_slate
            p_tr2.alignment = PP_ALIGN.CENTER

            # 4. Second Arrow Connector (RIGHT_ARROW in UPS Gold)
            arr2 = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW, Inches(6.26), arrow_y, Inches(0.33), Inches(0.28)
            )
            arr2.fill.solid()
            arr2.fill.fore_color.rgb = self.c_gold
            arr2.line.fill.background()

            # 5. Destination Node Box (UPS Brown rounded rectangle with UPS Gold text)
            dest_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.65), row_y, Inches(2.35), row_h
            )
            dest_box.fill.solid()
            dest_box.fill.fore_color.rgb = self.c_brown
            dest_box.line.color.rgb = self.c_gold_dark
            dest_box.line.width = Pt(1)
            tf_d = dest_box.text_frame
            tf_d.word_wrap = True
            tf_d.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_d1 = tf_d.paragraphs[0]
            p_d1.text = dest_txt
            p_d1.font.name = "Segoe UI"
            p_d1.font.size = Pt(10.5)
            p_d1.font.bold = True
            p_d1.font.color.rgb = self.c_gold
            p_d1.alignment = PP_ALIGN.CENTER

            # 6. Volume & Remarks Summary Box on the right
            rem_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.20), row_y, Inches(3.48), row_h
            )
            rem_box.fill.solid()
            rem_box.fill.fore_color.rgb = self.c_white
            rem_box.line.color.rgb = self.c_border
            rem_box.line.width = Pt(1)
            tf_r = rem_box.text_frame
            tf_r.word_wrap = True
            tf_r.vertical_anchor = MSO_ANCHOR.MIDDLE
            p_r1 = tf_r.paragraphs[0]
            p_r1.text = f"Volume / Metric: {vol_txt}"
            p_r1.font.name = "Segoe UI"
            p_r1.font.size = Pt(9.5)
            p_r1.font.bold = True
            p_r1.font.color.rgb = self.c_brown

            p_r2 = tf_r.add_paragraph()
            p_r2.text = rem_txt[:95]
            p_r2.font.name = "Segoe UI"
            p_r2.font.size = Pt(8.5)
            p_r2.font.color.rgb = self.c_charcoal

        # Bottom Traceability Banner
        banner = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.65), Inches(6.42), Inches(12.033), Inches(0.42)
        )
        banner.fill.solid()
        banner.fill.fore_color.rgb = self.c_row_alt
        banner.line.color.rgb = self.c_gold_dark
        banner.line.width = Pt(1)
        tf_bn = banner.text_frame
        tf_bn.word_wrap = True
        tf_bn.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_bn = tf_bn.paragraphs[0]
        p_bn.text = (
            "SOURCE TRACEABILITY: Origin, transit hub connections, carrier schedules, "
            "and lane remarks are extracted directly from workbook records."
        )
        p_bn.font.name = "Segoe UI"
        p_bn.font.size = Pt(9.5)
        p_bn.font.bold = True
        p_bn.font.color.rgb = self.c_brown

    def _render_exceptions_remarks_slide(self, slide, data: Dict[str, Any]):
        """
        Operational Exceptions, Remarks & Special Conditions Slide.
        Renders a structured native PowerPoint table showing every extracted Exception /
        Operational Remark / Special Condition (Entity / Route, Condition / Category,
        Original Excel Remark / Detail, Impact / Metric) plus a bottom summary bar
        distinguishing original source remarks from calculated analytical flags.
        """
        data.setdefault("source_badge", "Original Source Data")
        self._add_slide_chrome(slide, data)

        table_data = data.get("table_data")
        if not table_data or not table_data.get("rows"):
            items = data.get("exceptions_and_remarks", [])
            rows = []
            for idx, item in enumerate(items[:8], start=1):
                if isinstance(item, dict):
                    rows.append([
                        str(item.get("entity") or item.get("route") or f"Record #{idx}"),
                        str(item.get("condition") or item.get("category") or "Operational Remark"),
                        str(item.get("remark") or item.get("detail") or "Workbook operational note"),
                        str(item.get("impact") or item.get("metric") or "Source Note"),
                    ])
                else:
                    rows.append([f"Entry #{idx}", "Operational Note", str(item), "Source Text"])
            if not rows:
                rows = [
                    [
                        "All Monitored Lanes",
                        "Standard Operations",
                        "No critical operational exceptions or remarks flagged in source worksheet.",
                        "Nominal SLA",
                    ]
                ]
            table_data = {
                "headers": [
                    "Entity / Route",
                    "Condition / Category",
                    "Original Excel Remark / Detail",
                    "Impact / Metric",
                ],
                "rows": rows,
            }

        headers = table_data.get(
            "headers",
            [
                "Entity / Route",
                "Condition / Category",
                "Original Excel Remark / Detail",
                "Impact / Metric",
            ],
        )
        rows = table_data.get("rows", [])[:8]

        total_rows = len(rows) + 1
        cols_count = len(headers)

        table_shape = slide.shapes.add_table(
            total_rows, cols_count, Inches(0.65), Inches(1.38), Inches(12.033), Inches(4.78)
        )
        table = table_shape.table

        # Set proportional column widths for 4-column exception matrix
        if cols_count == 4:
            table.columns[0].width = Inches(2.35)
            table.columns[1].width = Inches(2.25)
            table.columns[2].width = Inches(5.333)
            table.columns[3].width = Inches(2.10)

        for col_idx, h_text in enumerate(headers):
            cell = table.cell(0, col_idx)
            cell.text = str(h_text)
            cell.fill.solid()
            cell.fill.fore_color.rgb = self.c_brown
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT if col_idx < 3 else PP_ALIGN.RIGHT
                p.font.name = "Segoe UI"
                p.font.size = Pt(10)
                p.font.bold = True
                p.font.color.rgb = self.c_gold

        for row_idx, row in enumerate(rows):
            is_even = row_idx % 2 == 0
            fill_color = self.c_white if is_even else self.c_row_alt
            for col_idx, val in enumerate(row):
                if col_idx < cols_count:
                    cell = table.cell(row_idx + 1, col_idx)
                    cell.text = str(val)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = fill_color
                    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                    for p in cell.text_frame.paragraphs:
                        p.alignment = PP_ALIGN.LEFT if col_idx < 3 else PP_ALIGN.RIGHT
                        p.font.name = "Segoe UI"
                        p.font.size = Pt(9.5)
                        p.font.bold = col_idx in (0, 1)
                        p.font.color.rgb = (
                            self.c_brown if col_idx == 1 else self.c_charcoal
                        )

        # Bottom Summary Bar distinguishing Original Source Remarks from Calculated Flags
        summary_bar = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.65), Inches(6.30), Inches(12.033), Inches(0.52)
        )
        summary_bar.fill.solid()
        summary_bar.fill.fore_color.rgb = self.c_white
        summary_bar.line.color.rgb = self.c_gold
        summary_bar.line.width = Pt(1.25)

        left_accent = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.65), Inches(6.30), Inches(0.10), Inches(0.52)
        )
        left_accent.fill.solid()
        left_accent.fill.fore_color.rgb = self.c_gold
        left_accent.line.fill.background()

        tf_s = summary_bar.text_frame
        tf_s.word_wrap = True
        tf_s.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_s = tf_s.paragraphs[0]
        p_s.text = (
            "   DATA PROVENANCE DISTINCTION:  [Original Excel Remark] = Verbatim notes, comments & conditions "
            "from source cells   |   [Calculated Flag] = Deterministic threshold or anomaly detection."
        )
        p_s.font.name = "Segoe UI"
        p_s.font.size = Pt(9.5)
        p_s.font.bold = True
        p_s.font.color.rgb = self.c_brown

    def _render_full_data_table_slide(self, slide, data: Dict[str, Any]):
        """
        Complete Source Data Preservation Slide (Paginated 10-Row Table).
        Renders a full-width, high-legibility native PowerPoint table
        (Inches(0.6) left, Inches(1.35) top, Inches(12.133) width, Inches(5.35) height)
        using Pt(9.5) font size for cells and Pt(10) bold UPS Gold on UPS Brown for headers.
        """
        data["source_badge"] = data.get("source_badge") or "ORIGINAL EXCEL SOURCE DATA"
        self._add_slide_chrome(slide, data)

        table_data = data.get("table_data") or {"headers": ["Record", "Value"], "rows": []}
        headers = list(table_data.get("headers") or ["Column", "Value"])
        rows = list(table_data.get("rows") or [])[:10]

        if not rows:
            rows = [["—"] * len(headers)]

        total_rows = len(rows) + 1
        cols_count = max(1, len(headers))

        table_shape = slide.shapes.add_table(
            total_rows,
            cols_count,
            Inches(0.6),
            Inches(1.35),
            Inches(12.133),
            Inches(5.35),
        )
        table = table_shape.table

        # Format Header Row (UPS Brown background, Pt(10) bold UPS Gold text)
        for col_idx, h_text in enumerate(headers):
            cell = table.cell(0, col_idx)
            cell.text = str(h_text)
            cell.fill.solid()
            cell.fill.fore_color.rgb = self.c_brown
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.05)
            cell.margin_right = Inches(0.05)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)

            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT if col_idx == 0 else PP_ALIGN.CENTER
                p.font.name = "Segoe UI"
                p.font.size = Pt(10)
                p.font.bold = True
                p.font.color.rgb = self.c_gold

        # Format Paginated Data Rows (Pt(9.5) high-legibility Segoe UI)
        for row_idx, row in enumerate(rows):
            is_even = row_idx % 2 == 0
            fill_color = self.c_white if is_even else self.c_row_alt

            for col_idx in range(cols_count):
                val = row[col_idx] if col_idx < len(row) else ""
                cell = table.cell(row_idx + 1, col_idx)
                cell.text = "" if val is None else str(val)
                cell.fill.solid()
                cell.fill.fore_color.rgb = fill_color
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left = Inches(0.05)
                cell.margin_right = Inches(0.05)
                cell.margin_top = Inches(0.02)
                cell.margin_bottom = Inches(0.02)

                for p in cell.text_frame.paragraphs:
                    p.alignment = PP_ALIGN.LEFT if col_idx == 0 else PP_ALIGN.LEFT
                    p.font.name = "Segoe UI"
                    p.font.size = Pt(9.5)
                    p.font.bold = col_idx == 0
                    p.font.color.rgb = self.c_charcoal

    def _render_generic_slide(self, slide, data: Dict[str, Any]):
        """Fallback content slide with UPS corporate chrome and watermark."""
        self._add_slide_chrome(slide, data)
        takeaways = data.get(
            "takeaways", ["Operational analysis derived from uploaded Excel workbook."]
        )
        self._add_takeaways_card(
            slide, Inches(0.75), Inches(1.75), Inches(11.8), Inches(4.75), takeaways
        )

    # =========================================================================
    # REUSABLE UPS CORPORATE CHROME (HEADER, WATERMARK, SOURCE BADGE, FOOTER)
    # =========================================================================

    def _add_slide_chrome(self, slide, data: Dict[str, Any]):
        """
        Applies the approved UPS corporate master design to every content slide:
        - Warm Cream canvas (#FAF8F5)
        - Subtle UPS Shield Watermark on EVERY slide (non-overlapping readability)
        - UPS Brown header banner (#351C15) with UPS Gold accent bar (#FFB500)
        - Source Distinction Pill Badge in top-right next to UPS Shield Logo
        - Consistent UPS Shield Logo in top-right header
        - Footer with slide number and report metadata
        """
        # 1. Slide Canvas Background: Warm Cream
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.c_cream
        bg.line.fill.background()

        # 2. UPS Watermark on EVERY Slide (placed before content shapes so it stays in background)
        slide.shapes.add_picture(
            str(UPS_WATERMARK_PATH),
            Inches(8.65), Inches(1.75), height=Inches(4.75),
        )

        # 3. Top UPS Corporate Brown Header Banner
        header_bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(1.1)
        )
        header_bg.fill.solid()
        header_bg.fill.fore_color.rgb = self.c_brown
        header_bg.line.fill.background()

        # 4. UPS Gold Accent Stripe under Header
        gold_line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, Inches(1.1), Inches(13.333), Inches(0.06)
        )
        gold_line.fill.solid()
        gold_line.fill.fore_color.rgb = self.c_gold
        gold_line.line.fill.background()

        # 5. Source Distinction Pill Badge (next to UPS Shield Logo in Header)
        source_badge_text = str(data.get("source_badge", "Verified Excel Data")).upper()
        badge_shape = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(9.10),
            Inches(0.32),
            Inches(2.75),
            Inches(0.42),
        )
        badge_shape.fill.solid()
        if "ORIGINAL" in source_badge_text or "SOURCE" in source_badge_text:
            badge_shape.fill.fore_color.rgb = self.c_gold
            badge_shape.line.fill.background()
            badge_text_color = self.c_brown
        else:
            badge_shape.fill.fore_color.rgb = self.c_dark_brown
            badge_shape.line.color.rgb = self.c_gold
            badge_shape.line.width = Pt(1)
            badge_text_color = self.c_gold

        tf_badge = badge_shape.text_frame
        tf_badge.word_wrap = True
        tf_badge.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_badge = tf_badge.paragraphs[0]
        p_badge.text = source_badge_text
        p_badge.font.name = "Segoe UI"
        p_badge.font.size = Pt(8.5)
        p_badge.font.bold = True
        p_badge.font.color.rgb = badge_text_color
        p_badge.alignment = PP_ALIGN.CENTER

        # 6. Consistent UPS Shield Logo in Top-Right Header
        slide.shapes.add_picture(
            str(UPS_LOGO_PATH),
            Inches(12.05), Inches(0.14), height=Inches(0.82),
        )

        # 7. Slide Title & Subtitle in Header Banner
        title_box = slide.shapes.add_textbox(
            Inches(0.75), Inches(0.14), Inches(8.25), Inches(0.88)
        )
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_top = 0
        tf.margin_bottom = 0
        tf.margin_left = 0
        tf.margin_right = 0

        p_t = tf.paragraphs[0]
        p_t.text = data.get("title", "Operational Analysis")
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(20)
        p_t.font.bold = True
        p_t.font.color.rgb = self.c_white

        p_s = tf.add_paragraph()
        p_s.text = data.get("subtitle", "Verified Excel Operational Metrics")
        p_s.font.name = "Segoe UI"
        p_s.font.size = Pt(10.5)
        p_s.font.color.rgb = self.c_gold
        p_s.space_before = Pt(2)

        # 8. Bottom Corporate Footer Bar & Slide Number
        footer_line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.75), Inches(6.95), Inches(11.833), Inches(0.02)
        )
        footer_line.fill.solid()
        footer_line.fill.fore_color.rgb = self.c_border
        footer_line.line.fill.background()

        slide_num = data.get("slide_number", 1)
        footer_box = slide.shapes.add_textbox(
            Inches(0.75), Inches(7.02), Inches(11.833), Inches(0.35)
        )
        tf_f = footer_box.text_frame
        p_f = tf_f.paragraphs[0]
        p_f.text = f"{self.title}   |   UPS Operations Analytics   •   Slide {slide_num} of {self.total_slides}"
        p_f.font.name = "Segoe UI"
        p_f.font.size = Pt(9.5)
        p_f.font.bold = True
        p_f.font.color.rgb = self.c_brown

    def _add_kpi_card(self, slide, x, y, width, height, kpi: Dict[str, Any]):
        """
        Renders a UPS-styled KPI metric card with UPS Gold top accent and UPS Brown figures.
        """
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = self.c_white
        card.line.color.rgb = self.c_border
        card.line.width = Pt(1)

        # Top UPS Gold Accent Strip
        accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, width, Inches(0.08))
        accent.fill.solid()
        accent.fill.fore_color.rgb = self.c_gold
        accent.line.fill.background()

        tx = slide.shapes.add_textbox(
            x + Inches(0.15), y + Inches(0.14), width - Inches(0.3), height - Inches(0.24)
        )
        tf = tx.text_frame
        tf.word_wrap = True

        # Badge / Category
        p_b = tf.paragraphs[0]
        p_b.text = kpi.get("badge", "VERIFIED METRIC").upper()
        p_b.font.name = "Segoe UI"
        p_b.font.size = Pt(8.5)
        p_b.font.bold = True
        p_b.font.color.rgb = self.c_gold_dark

        # Main Value
        p_val = tf.add_paragraph()
        p_val.text = str(kpi.get("value", "—"))
        p_val.font.name = "Segoe UI"
        p_val.font.size = Pt(26)
        p_val.font.bold = True
        p_val.font.color.rgb = self.c_brown
        p_val.space_before = Pt(2)

        # Metric Label
        p_lbl = tf.add_paragraph()
        p_lbl.text = kpi.get("label", "Metric Label")
        p_lbl.font.name = "Segoe UI"
        p_lbl.font.size = Pt(10.5)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = self.c_charcoal
        p_lbl.space_before = Pt(1)

        # Subtext / Context
        subtext = kpi.get("subtext")
        if subtext:
            p_sub = tf.add_paragraph()
            p_sub.text = subtext
            p_sub.font.name = "Segoe UI"
            p_sub.font.size = Pt(8.5)
            p_sub.font.color.rgb = self.c_slate
            p_sub.space_before = Pt(1)

    def _add_takeaways_card(self, slide, x, y, width, height, takeaways: List[str]):
        """
        Renders an executive takeaways card with UPS Brown header and Gold left accent.
        """
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = self.c_white
        card.line.color.rgb = self.c_border
        card.line.width = Pt(1)

        # Left UPS Gold Vertical Accent Bar
        left_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(0.08), height)
        left_bar.fill.solid()
        left_bar.fill.fore_color.rgb = self.c_gold
        left_bar.line.fill.background()

        tx = slide.shapes.add_textbox(
            x + Inches(0.22), y + Inches(0.14), width - Inches(0.38), height - Inches(0.28)
        )
        tf = tx.text_frame
        tf.word_wrap = True

        p_h = tf.paragraphs[0]
        p_h.text = "KEY OPERATIONAL INSIGHTS & VERIFIED FINDINGS"
        p_h.font.name = "Segoe UI"
        p_h.font.size = Pt(9.5)
        p_h.font.bold = True
        p_h.font.color.rgb = self.c_brown

        for item in takeaways:
            p = tf.add_paragraph()
            clean_item = item.replace("**", "")
            p.text = f"▸  {clean_item}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(10.5)
            p.font.color.rgb = self.c_charcoal
            p.space_before = Pt(5)

    def _add_chart(self, slide, x, y, width, height, chart_cfg: Dict[str, Any]):
        """
        Embeds a native, editable PowerPoint chart styled with UPS Brown and UPS Gold.
        """
        chart_data = CategoryChartData()
        categories = chart_cfg.get("categories", ["A", "B", "C"])
        values = chart_cfg.get("values", [10, 20, 30])
        series_name = chart_cfg.get("series_name", "Volume")

        chart_data.categories = categories
        chart_data.add_series(series_name, tuple(values))

        ctype = chart_cfg.get("chart_type", "column")
        if ctype == "bar":
            xl_type = XL_CHART_TYPE.BAR_CLUSTERED
        elif ctype == "line":
            xl_type = XL_CHART_TYPE.LINE
        elif ctype == "doughnut":
            xl_type = XL_CHART_TYPE.DOUGHNUT
        else:
            xl_type = XL_CHART_TYPE.COLUMN_CLUSTERED

        chart_shape = slide.shapes.add_chart(xl_type, x, y, width, height, chart_data)
        chart = chart_shape.chart

        chart.has_legend = ctype == "doughnut" or len(categories) > 6
        if chart.has_legend:
            chart.legend.position = XL_LEGEND_POSITION.RIGHT
            chart.legend.font.size = Pt(9.5)
            chart.legend.font.name = "Segoe UI"

        # Style primary series with UPS Corporate Brown / Gold
        try:
            series = chart.series[0]
            if ctype != "doughnut":
                series.format.fill.solid()
                series.format.fill.fore_color.rgb = self.c_brown
                if ctype == "line":
                    series.format.line.color.rgb = self.c_brown
                    series.format.line.width = Pt(2.5)
        except Exception:
            pass

    def _add_table(self, slide, x, y, width, height, table_data: Dict[str, Any]):
        """
        Embeds a native editable PowerPoint table with UPS Brown header row and warm alternating rows.
        """
        headers = table_data.get("headers", ["Category", "Value"])
        rows = table_data.get("rows", [])
        total_rows = len(rows) + 1
        cols_count = len(headers)

        table_shape = slide.shapes.add_table(total_rows, cols_count, x, y, width, height)
        table = table_shape.table

        # Format Header Row (UPS Brown background, UPS Gold / White text)
        for col_idx, h_text in enumerate(headers):
            cell = table.cell(0, col_idx)
            cell.text = str(h_text)
            cell.fill.solid()
            cell.fill.fore_color.rgb = self.c_brown
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE

            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT if col_idx == 0 else PP_ALIGN.RIGHT
                p.font.name = "Segoe UI"
                p.font.size = Pt(10)
                p.font.bold = True
                p.font.color.rgb = self.c_gold

        # Format Data Rows
        for row_idx, row in enumerate(rows):
            is_even = row_idx % 2 == 0
            fill_color = self.c_white if is_even else self.c_row_alt

            for col_idx, val in enumerate(row):
                if col_idx < cols_count:
                    cell = table.cell(row_idx + 1, col_idx)
                    cell.text = str(val)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = fill_color
                    cell.vertical_anchor = MSO_ANCHOR.MIDDLE

                    for p in cell.text_frame.paragraphs:
                        p.alignment = PP_ALIGN.LEFT if col_idx == 0 else PP_ALIGN.RIGHT
                        p.font.name = "Segoe UI"
                        p.font.size = Pt(9.5)
                        p.font.bold = col_idx == 0
                        p.font.color.rgb = self.c_charcoal

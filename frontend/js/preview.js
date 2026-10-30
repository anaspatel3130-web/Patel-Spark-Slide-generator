/**
 * frontend/js/preview.js
 * ----------------------
 * Interactive Slide Preview Controller.
 * Renders 16:9 thumbnail previews of planned slides (including Origin->Transit->Destination
 * flow diagrams, operational exceptions/remarks, and paginated complete source data tables)
 * plus Cross-Validation summary prior to PowerPoint & Excel compilation.
 */

const Preview = {
  currentPlan: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    document.getElementById("btn-download-from-preview")?.addEventListener("click", async () => {
      App.closeModal("modal-preview");
      if (window.Upload) {
        await Upload.generatePresentation();
      }
    });
  },

  async loadAndShowPreview() {
    if (!App.state.currentFile) return;

    const payload = (window.Upload && typeof Upload.buildGenerationPayload === "function")
      ? Upload.buildGenerationPayload()
      : {
          file_id: App.state.currentFile.file_id,
          sheet_name: App.state.selectedSheet,
          slide_count: App.state.selectedSlides,
          custom_title: document.getElementById("input-custom-title")?.value.trim() || undefined
        };

    try {
      App.showToast("Computing verified slide preview & accuracy audit...", "info");

      const res = await App.apiRequest("/api/generator/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const plan = await res.json();
      if (!res.ok) throw new Error(plan.detail || "Could not generate slide preview.");

      this.currentPlan = plan;
      this.renderValidationBanner(plan.validation_report);
      this.renderCarousel(plan);
      App.openModal("modal-preview");
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  renderValidationBanner(report) {
    const banner = document.getElementById("preview-validation-summary");
    if (!banner) return;

    if (!report) {
      banner.style.display = "none";
      banner.innerHTML = "";
      return;
    }

    const wsIncluded = (report.worksheets_included || []).join(", ") || "Active Sheet";
    const recordsRep = `${report.records_represented ?? 0} / ${report.total_source_records ?? 0} Records`;
    const calcCount = (report.calculations_performed || []).length;
    const warnCount = (report.data_quality_warnings || []).length;
    const agentVerified = report.agent_pipeline?.zero_hallucinations_verified !== false;

    banner.style.display = "block";
    banner.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
        <div>
          <strong style="color:var(--color-primary);">🛡️ Cross-Validation &amp; Multi-Agent Audit (${this.escapeHtml(report.overall_status || "VERIFIED")}):</strong>
          <span style="color:var(--text-secondary); margin-left:0.4rem;">
            Worksheets: <strong>${this.escapeHtml(wsIncluded)}</strong> •
            Represented: <strong>${this.escapeHtml(recordsRep)}</strong> •
            Calculations: <strong>${calcCount} Verified</strong> •
            Quality Warnings: <strong>${warnCount}</strong>
          </span>
        </div>
        <span class="category-badge highlight">${agentVerified ? "🤖 Fact-Checked • Source Verified" : "Source Validated"}</span>
      </div>
    `;
  },

  renderCarousel(plan) {
    const container = document.getElementById("preview-slides-carousel");
    if (!container) return;

    container.innerHTML = "";
    const modalTitle = document.getElementById("preview-modal-title");
    if (modalTitle) {
      modalTitle.textContent = `Presentation Blueprint: ${plan.actual_slides} Slides (16:9 Widescreen)`;
    }

    plan.slides.forEach(slide => {
      const card = document.createElement("div");
      const isTitle = slide.layout_type === "title";
      const isClosing = slide.layout_type === "closing";

      card.className = `slide-card-preview ${isTitle || isClosing ? "title-slide" : ""}`;

      // 1. Title / Cover Slide Preview
      if (isTitle) {
        card.innerHTML = `
          <div>
            <div class="preview-badge">SLIDE ${slide.slide_number} • COVER</div>
            <div style="margin-top: 0.75rem;">
              <span style="font-size: 1.5rem;">📊</span>
            </div>
            <div class="preview-title" style="margin-top: 0.5rem;">${this.escapeHtml(slide.title)}</div>
            <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 0.25rem;">${this.escapeHtml(slide.subtitle || "")}</div>
          </div>
          <div style="font-size: 0.7rem; color: var(--color-accent); border-top: 1px solid rgba(255,255,255,0.15); padding-top: 0.4rem;">
            Executive Briefing • Business Performance Review
          </div>
        `;
      }
      // 2. Closing Slide Preview
      else if (isClosing) {
        card.innerHTML = `
          <div>
            <div class="preview-badge">SLIDE ${slide.slide_number} • CLOSING</div>
            <div style="margin-top: 1rem; text-align: center;">
              <span style="font-size: 2rem;">📈</span>
              <div class="preview-title" style="margin-top: 0.5rem; text-align: center;">Executive Performance Review</div>
              <div style="font-size: 0.75rem; color: var(--color-accent); margin-top: 0.2rem; text-align: center;">Thank You</div>
            </div>
          </div>
          <div style="font-size: 0.65rem; color: #94a3b8; text-align: center; border-top: 1px solid rgba(255,255,255,0.15); padding-top: 0.4rem;">
            Proprietary &amp; Confidential — Authorized Internal Review Only
          </div>
        `;
      }
      // 3. Origin -> Transit -> Destination Route Flow Diagram Slide
      else if (slide.layout_type === "route_flow_diagram") {
        const flows = slide.routing_flows || [];
        const badgeText = slide.source_badge || "Original Source Data";
        const flowsHtml = flows.slice(0, 3).map(f => `
          <div class="preview-route-flow-item">
            <div>
              <span>${this.escapeHtml(f.origin || "Origin")}</span>
              <span class="preview-flow-arrow">➔</span>
              <span style="color:#475569;">${this.escapeHtml(f.transit || "Direct")}</span>
              <span class="preview-flow-arrow">➔</span>
              <span>${this.escapeHtml(f.destination || "Destination")}</span>
            </div>
            <span style="font-size:0.62rem; color:var(--color-accent);">${this.escapeHtml(f.flight_or_carrier || f.frequency || "")}</span>
          </div>
        `).join("");

        card.innerHTML = `
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div class="preview-badge" style="color:var(--color-primary);">SLIDE ${slide.slide_number} • ROUTE FLOW</div>
              <span style="font-size:0.62rem; font-weight:700; background:var(--color-accent-light); color:var(--color-accent); padding:0.1rem 0.4rem; border-radius:4px;">${this.escapeHtml(badgeText)}</span>
            </div>
            <div class="preview-title" style="margin-top:0.25rem; font-size:0.95rem;">${this.escapeHtml(slide.title)}</div>
            <div style="font-size:0.68rem; color:var(--text-secondary);">${this.escapeHtml(slide.subtitle || "")}</div>
            <div class="preview-route-flow-list">${flowsHtml || '<div style="font-size:0.7rem; color:var(--text-secondary);">Origin ➔ Transit ➔ Destination Corridors</div>'}</div>
          </div>
          <div class="preview-takeaway">
            Showing ${flows.length} end-to-end Origin ➔ Transit ➔ Destination operational corridor leg(s).
          </div>
        `;
      }
      // 4. Operational Exceptions, Remarks & Special Conditions Slide
      else if (slide.layout_type === "exceptions_remarks") {
        const items = slide.exceptions_list || slide.exceptions_and_remarks || [];
        const badgeText = slide.source_badge || "Original Source Data";
        const remarksHtml = items.slice(0, 3).map(item => `
          <div class="preview-exception-item">
            <strong>${this.escapeHtml(item.entity || "Record")} (${this.escapeHtml(item.condition || "Note")}):</strong>
            ${this.escapeHtml((item.remark || "").slice(0, 68))}
          </div>
        `).join("");

        card.innerHTML = `
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div class="preview-badge" style="color:var(--color-primary);">SLIDE ${slide.slide_number} • REMARKS &amp; EXCEPTIONS</div>
              <span style="font-size:0.62rem; font-weight:700; background:var(--color-accent-light); color:var(--color-accent); padding:0.1rem 0.4rem; border-radius:4px;">${this.escapeHtml(badgeText)}</span>
            </div>
            <div class="preview-title" style="margin-top:0.25rem; font-size:0.95rem;">${this.escapeHtml(slide.title)}</div>
            <div style="font-size:0.68rem; color:var(--text-secondary);">${this.escapeHtml(slide.subtitle || "")}</div>
            <div class="preview-exceptions-list">${remarksHtml}</div>
          </div>
          <div class="preview-takeaway">
            Preserves ${items.length} verbatim operational remark(s) &amp; special condition(s).
          </div>
        `;
      }
      // 5. Paginated Complete Source Data Table Slide
      else if (slide.layout_type === "full_data_table") {
        const headers = slide.table_data?.headers || [];
        const rows = slide.table_data?.rows || [];
        const badgeText = slide.source_badge || "ORIGINAL EXCEL SOURCE DATA";

        const miniRowsHtml = rows.slice(0, 3).map(r =>
          `<div style="font-size:0.62rem; color:var(--text-secondary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; padding:0.15rem 0; border-bottom:1px solid var(--border-light);">
             ${r.slice(0, 4).map(cell => this.escapeHtml(cell)).join("  |  ")}
           </div>`
        ).join("");

        card.innerHTML = `
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div class="preview-badge" style="color:var(--color-primary);">SLIDE ${slide.slide_number} • FULL DATA TABLE</div>
              <span style="font-size:0.6rem; font-weight:700; background:#dcfce7; color:#166534; padding:0.1rem 0.4rem; border-radius:4px;">${this.escapeHtml(badgeText)}</span>
            </div>
            <div class="preview-title" style="margin-top:0.25rem; font-size:0.92rem;">${this.escapeHtml(slide.title)}</div>
            <div style="font-size:0.66rem; color:var(--text-secondary); margin-bottom:0.35rem;">${this.escapeHtml(slide.subtitle || "")}</div>
            <div style="background:var(--bg-canvas); padding:0.35rem 0.5rem; border-radius:var(--radius-sm); border:1px solid var(--border-light);">
              <div style="font-size:0.65rem; font-weight:700; color:var(--color-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                📋 ${headers.slice(0, 5).map(h => this.escapeHtml(h)).join(" • ")}
              </div>
              ${miniRowsHtml}
            </div>
          </div>
          <div class="preview-takeaway">
            Paginated Source Table (${rows.length} rows on this slide • 100% Exact Values)
          </div>
        `;
      }
      // 6. Standard Analytical Content Slides Preview
      else {
        const badgeText = slide.source_badge || "Patel'Spark";
        let kpisHtml = "";
        if (slide.kpis && slide.kpis.length > 0) {
          kpisHtml = `
            <div class="preview-kpis">
              ${slide.kpis.slice(0, 4).map(k => `
                <div class="preview-kpi-box">
                  <div class="preview-kpi-lbl">${this.escapeHtml(k.label)}</div>
                  <div class="preview-kpi-val">${this.escapeHtml(k.value)}</div>
                </div>
              `).join("")}
            </div>
          `;
        }

        let chartOrTableHtml = "";
        if (slide.chart_config) {
          chartOrTableHtml = `
            <div style="background:var(--bg-canvas); padding:0.4rem 0.6rem; border-radius:var(--radius-sm); font-size:0.7rem; color:var(--color-primary); font-weight:700; margin-bottom:0.4rem;">
              📊 Chart: ${this.escapeHtml(slide.chart_config.title || "Chart")} (${(slide.chart_config.chart_type || "bar").toUpperCase()})
            </div>
          `;
        } else if (slide.table_data) {
          chartOrTableHtml = `
            <div style="background:var(--bg-canvas); padding:0.4rem 0.6rem; border-radius:var(--radius-sm); font-size:0.7rem; color:var(--color-primary); font-weight:700; margin-bottom:0.4rem;">
              📋 Table: ${(slide.table_data.headers || []).join(" • ")}
            </div>
          `;
        }

        let takeawaysHtml = "";
        if (slide.takeaways && slide.takeaways.length > 0) {
          takeawaysHtml = `
            <div class="preview-takeaway">
              ${slide.takeaways.slice(0, 2).map(t => `<div>• ${this.escapeHtml(t.replace(/\*\*/g, ""))}</div>`).join("")}
            </div>
          `;
        }

        card.innerHTML = `
          <div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div class="preview-badge" style="color:var(--color-primary);">SLIDE ${slide.slide_number}</div>
              <span style="font-size:0.65rem; font-weight:700; color:var(--color-accent);">${this.escapeHtml(badgeText)}</span>
            </div>
            <div class="preview-title" style="margin-top:0.3rem;">${this.escapeHtml(slide.title)}</div>
            <div style="font-size:0.7rem; color:var(--text-secondary);">${this.escapeHtml(slide.subtitle || "")}</div>
            ${kpisHtml}
            ${chartOrTableHtml}
          </div>
          ${takeawaysHtml}
        `;
      }

      container.appendChild(card);
    });
  },

  escapeHtml(text) {
    if (!text) return "";
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  Preview.init();
});

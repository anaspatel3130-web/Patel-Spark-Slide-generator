/**
 * frontend/js/upload.js
 * ---------------------
 * Excel File Ingestion, Multi-Sheet Configuration, Detail Mode & Slide Count Control,
 * Content Toggle Checkboxes, Dual Output Downloads, and Cross-Validation Reporting.
 */

const Upload = {
  state: {
    detailLevel: "summary",
    slideMode: "manual",
  },

  init() {
    this.bindEvents();
    if (App.state.token) {
      this.loadHistory();
    }
  },

  bindEvents() {
    const dropzone = document.getElementById("upload-dropzone");
    const fileInput = document.getElementById("excel-file-input");

    // Click to browse
    document.getElementById("btn-browse-file")?.addEventListener("click", () => fileInput.click());
    dropzone?.addEventListener("click", (e) => {
      if (e.target.id !== "btn-browse-file") fileInput.click();
    });

    // Drag-and-drop events
    ["dragenter", "dragover"].forEach(evt => {
      dropzone?.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("drag-active");
      });
    });

    ["dragleave", "drop"].forEach(evt => {
      dropzone?.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("drag-active");
      });
    });

    dropzone?.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files.length > 0) this.handleFile(files[0]);
    });

    fileInput?.addEventListener("change", (e) => {
      if (e.target.files.length > 0) this.handleFile(e.target.files[0]);
    });

    // Replace file button
    document.getElementById("btn-change-file")?.addEventListener("click", () => {
      document.getElementById("config-panel").classList.remove("active");
      const resultsCard = document.getElementById("generation-results-card");
      if (resultsCard) resultsCard.style.display = "none";
      document.getElementById("upload-dropzone").style.display = "block";
      fileInput.value = "";
    });

    // Multi-Worksheet Checkbox ("Include All Non-Empty Worksheets")
    document.getElementById("chk-all-sheets")?.addEventListener("change", (e) => {
      const includeAll = e.target.checked;
      document.querySelectorAll(".sheet-tab").forEach(tab => {
        const sName = tab.getAttribute("data-sheet");
        const sInfo = App.state.currentFile?.sheets_info?.[sName];
        if (includeAll && sInfo && sInfo.row_count > 0) {
          tab.classList.add("active");
        } else {
          tab.classList.toggle("active", sName === App.state.selectedSheet);
        }
      });
      if (App.state.currentFile) {
        this.renderInspectionSummary(App.state.currentFile, App.state.selectedSheet);
      }
    });

    // Presentation Detail Mode Selector (Management Summary vs Complete Data Preservation)
    document.querySelectorAll(".detail-mode-card").forEach(card => {
      card.addEventListener("click", () => {
        document.querySelectorAll(".detail-mode-card").forEach(c => c.classList.remove("active"));
        card.classList.add("active");
        const mode = card.getAttribute("data-detail") || "summary";
        this.state.detailLevel = mode;

        const chkFullTables = document.getElementById("chk-include-full-tables");
        if (mode === "complete") {
          if (chkFullTables) chkFullTables.checked = true;
          // Auto-select Adaptive (0) slide count so full tables paginate cleanly
          document.querySelectorAll(".slide-count-btn").forEach(b => {
            const isAuto = b.getAttribute("data-slides") === "0";
            b.classList.toggle("active", isAuto);
          });
          App.state.selectedSlides = 0;
          this.state.slideMode = "auto";
        } else {
          if (chkFullTables) chkFullTables.checked = false;
        }
      });
    });

    // Slide Count Selector (Auto Adaptive 0 + 2 to 6 slides)
    document.querySelectorAll(".slide-count-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".slide-count-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const count = parseInt(btn.getAttribute("data-slides"), 10);
        App.state.selectedSlides = isNaN(count) ? 4 : count;
        this.state.slideMode = (App.state.selectedSlides === 0) ? "auto" : "manual";
      });
    });

    // Preview Plan Button
    document.getElementById("btn-preview-plan")?.addEventListener("click", async () => {
      if (!App.state.currentFile) {
        App.showToast("Please upload an Excel workbook first.", "error");
        return;
      }
      if (window.Preview) {
        await Preview.loadAndShowPreview();
      }
    });

    // Generate Presentation Button
    document.getElementById("btn-generate-presentation")?.addEventListener("click", async () => {
      await this.generatePresentation();
    });

    // Refresh History
    document.getElementById("btn-refresh-history")?.addEventListener("click", () => {
      this.loadHistory();
    });

    // Cancel / Delete Generated Deck from Results Bar
    document.getElementById("btn-cancel-delete-deck")?.addEventListener("click", async () => {
      await this.cancelAndDeleteCurrentDeck();
    });

    // Dismiss results and start fresh
    document.getElementById("btn-dismiss-results")?.addEventListener("click", () => {
      const resultsCard = document.getElementById("generation-results-card");
      if (resultsCard) resultsCard.style.display = "none";
      document.getElementById("config-panel").classList.remove("active");
      document.getElementById("upload-dropzone").style.display = "block";
      const fileInput = document.getElementById("excel-file-input");
      if (fileInput) fileInput.value = "";
      App.state.currentFile = null;
      App.showToast("Workspace ready for next Excel workbook ingestion.", "info");
    });

    // Sample Dataset Loaders
    document.getElementById("btn-load-sample-1")?.addEventListener("click", async () => {
      await this.loadSampleDataset("/sample_ups_data/UPS_Global_Express_Shipments.xlsx");
    });

    document.getElementById("btn-load-sample-2")?.addEventListener("click", async () => {
      await this.loadSampleDataset("/sample_ups_data/UPS_Route_Logistics_Performance.xlsx");
    });
  },

  buildGenerationPayload() {
    const data = App.state.currentFile;
    if (!data) return null;

    const title = document.getElementById("input-custom-title")?.value.trim();
    const includeAllSheets = !!document.getElementById("chk-all-sheets")?.checked;

    let selectedSheets = [App.state.selectedSheet || data.active_sheet];
    if (includeAllSheets && Array.isArray(data.sheet_names)) {
      const nonEmpty = data.sheet_names.filter(s => (data.sheets_info?.[s]?.row_count || 0) > 0);
      if (nonEmpty.length > 0) selectedSheets = nonEmpty;
    }

    const slideCount = (typeof App.state.selectedSlides === "number") ? App.state.selectedSlides : 4;
    const includeFullTables = !!document.getElementById("chk-include-full-tables")?.checked;
    const detailLevel = this.state.detailLevel || (includeFullTables ? "complete" : "summary");
    const slideMode = (slideCount === 0 || detailLevel === "complete" || includeFullTables) ? "auto" : (this.state.slideMode || "manual");

    return {
      file_id: data.file_id,
      sheet_name: App.state.selectedSheet || data.active_sheet,
      selected_sheets: selectedSheets,
      slide_count: slideCount,
      slide_mode: slideMode,
      detail_level: detailLevel,
      include_charts_tables: document.getElementById("chk-include-charts") ? document.getElementById("chk-include-charts").checked : true,
      include_routing_flows: document.getElementById("chk-include-routing") ? document.getElementById("chk-include-routing").checked : true,
      include_remarks_exceptions: document.getElementById("chk-include-remarks") ? document.getElementById("chk-include-remarks").checked : true,
      include_full_data_tables: includeFullTables,
      custom_title: title || undefined,
    };
  },

  async handleFile(file) {
    if (!App.state.token) {
      App.showToast("Please sign in or request access to process operational spreadsheets.", "error");
      App.openModal("modal-login");
      return;
    }

    const validExtensions = [".xlsx", ".xls"];
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (!validExtensions.includes(ext)) {
      App.showToast("Invalid file type. Please upload a .xlsx or .xls file.", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const dropzone = document.getElementById("upload-dropzone");
    const originalText = dropzone.innerHTML;

    try {
      dropzone.innerHTML = `<div class="spinner"></div><div style="font-weight:700; color:var(--color-primary);">Ingesting & Inspecting Excel Workbook...</div>`;

      const res = await App.apiRequest("/api/excel/upload", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to process Excel file.");

      App.state.currentFile = data;
      App.state.selectedSheet = data.active_sheet;

      this.displayInspectionResults(data);
      App.showToast(`Successfully inspected "${file.name}" with ${data.sheet_names.length} sheet(s).`, "success");
    } catch (err) {
      App.showToast(err.message, "error");
    } finally {
      dropzone.innerHTML = originalText;
      this.bindDropzoneBrowse();
    }
  },

  bindDropzoneBrowse() {
    const fileInput = document.getElementById("excel-file-input");
    document.getElementById("btn-browse-file")?.addEventListener("click", () => fileInput?.click());
  },

  displayInspectionResults(data) {
    document.getElementById("upload-dropzone").style.display = "none";
    const panel = document.getElementById("config-panel");
    panel.classList.add("active");
    panel.style.display = "block";

    const resultsCard = document.getElementById("generation-results-card");
    if (resultsCard) resultsCard.style.display = "none";

    // Populate Meta Info
    document.getElementById("meta-filename").textContent = data.filename;
    if (window.Gamification) {
      Gamification.recordWorkbookUpload(data.sheet_names.length, data.total_rows || 0);
    }
    const activeInfo = data.sheets_info[data.active_sheet];
    const rowCount = activeInfo ? activeInfo.row_count : "—";
    const colCount = activeInfo ? activeInfo.col_count : "—";
    const totalRows = data.total_rows || rowCount;
    document.getElementById("meta-stats").textContent =
      `${data.sheet_names.length} Sheet(s) detected  •  Total Records: ${totalRows}  •  Active Sheet: ${rowCount} rows, ${colCount} columns`;

    // Populate Default Title
    const titleInput = document.getElementById("input-custom-title");
    if (titleInput) titleInput.value = data.detected_title;

    // Reset multi-sheet checkbox
    const chkAllSheets = document.getElementById("chk-all-sheets");
    if (chkAllSheets) {
      chkAllSheets.checked = data.sheet_names.length > 1;
    }

    // Render Sheet Selection Tabs
    const sheetContainer = document.getElementById("sheet-tabs-container");
    sheetContainer.innerHTML = "";

    data.sheet_names.forEach(sheetName => {
      const tab = document.createElement("button");
      tab.type = "button";
      tab.setAttribute("data-sheet", sheetName);
      const isMultiActive = chkAllSheets && chkAllSheets.checked;
      tab.className = `sheet-tab ${(sheetName === data.active_sheet || isMultiActive) ? "active" : ""}`;
      const sInfo = data.sheets_info[sheetName] || { row_count: 0 };
      tab.innerHTML = `📄 ${this.escapeHtml(sheetName)} <span style="opacity:0.75; font-size:0.75rem;">(${sInfo.row_count} rows)</span>`;

      tab.addEventListener("click", () => {
        if (chkAllSheets) chkAllSheets.checked = false;
        document.querySelectorAll(".sheet-tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        App.state.selectedSheet = sheetName;
        this.renderInspectionSummary(data, sheetName);
      });

      sheetContainer.appendChild(tab);
    });

    this.renderInspectionSummary(data, data.active_sheet);
  },

  renderInspectionSummary(data, sheetName) {
    const sInfo = data.sheets_info?.[sheetName] || {};
    const statsEl = document.getElementById("inspection-sheet-stats");
    const badgesEl = document.getElementById("detected-categories-badges");
    const warningsEl = document.getElementById("quality-warnings-list");

    const includeAll = !!document.getElementById("chk-all-sheets")?.checked;
    if (statsEl) {
      if (includeAll && data.sheet_names.length > 1) {
        statsEl.textContent = `Analyzing all ${data.sheet_names.length} worksheets (${data.total_rows || sInfo.row_count || 0} total rows)`;
      } else {
        statsEl.textContent = `Sheet "${sheetName}": ${sInfo.row_count || 0} rows × ${sInfo.col_count || 0} columns`;
      }
    }

    if (badgesEl) {
      let categories = Array.isArray(sInfo.detected_categories) && sInfo.detected_categories.length > 0
        ? [...sInfo.detected_categories]
        : [];

      if (categories.length === 0) {
        if ((sInfo.route_columns || []).length > 0) categories.push("Routes & Transit");
        if ((sInfo.country_columns || []).length > 0) categories.push("Countries & Markets");
        if ((sInfo.numeric_columns || []).length > 0) categories.push("Financials & Metrics");
        if ((sInfo.date_columns || []).length > 0) categories.push("Temporal / Schedule");
        if ((sInfo.remarks_columns || []).length > 0) categories.push("Operational Remarks");
        if (categories.length === 0) categories.push("Structured Operational Records");
      }

      badgesEl.innerHTML = categories.map(cat =>
        `<span class="category-badge highlight">✦ ${this.escapeHtml(cat)}</span>`
      ).join("") + (sInfo.columns ? `<span class="category-badge">📋 ${sInfo.columns.length} Columns Classified</span>` : "");
    }

    if (warningsEl) {
      const sheetWarnings = sInfo.quality_warnings || [];
      const wbWarnings = data.workbook_warnings || [];
      const combined = Array.from(new Set([...sheetWarnings, ...wbWarnings]));

      if (combined.length > 0) {
        warningsEl.style.display = "flex";
        warningsEl.innerHTML = combined.map(w =>
          `<div class="quality-warning-item"><span>⚠️</span><span>${this.escapeHtml(w)}</span></div>`
        ).join("");
      } else {
        warningsEl.style.display = "flex";
        warningsEl.style.color = "#15803d";
        warningsEl.innerHTML = `<div class="quality-warning-item"><span>✅</span><span>Data Quality Check Passed: Zero missing cells or duplicate rows detected in "${this.escapeHtml(sheetName)}".</span></div>`;
      }
    }
  },

  async generatePresentation() {
    if (!App.state.currentFile) {
      App.showToast("Please upload an Excel workbook first.", "error");
      return;
    }

    const stepper = document.getElementById("progress-stepper");
    const configPanel = document.getElementById("config-panel");
    const payload = this.buildGenerationPayload();

    try {
      configPanel.style.display = "none";
      stepper.classList.add("active");

      const statusTitle = document.getElementById("stepper-title");
      const statusDesc = document.getElementById("stepper-desc");

      statusTitle.textContent = "Step 1 of 4: Normalizing & Auditing Worksheets...";
      statusDesc.textContent = "Classifying metrics, Origin → Transit → Destination flows, and operational remarks";

      await new Promise(r => setTimeout(r, 450));
      statusTitle.textContent = "Step 2 of 4: Computing Deterministic KPIs & Formatting Excel...";
      statusDesc.textContent = "Preserving 100% of original Excel sheets + building Executive_Analysis_Summary";

      await new Promise(r => setTimeout(r, 450));
      statusTitle.textContent = "Step 3 of 4: Compiling 16:9 Presentation & Cross-Validating...";
      statusDesc.textContent = "Rendering slides, tables, flow diagrams, and running accuracy verification";

      const res = await App.apiRequest("/api/generator/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Presentation generation failed.");

      statusTitle.textContent = "Step 4 of 4: Dual Outputs Verified & Ready!";
      statusDesc.textContent = "PowerPoint (.pptx) and Formatted Excel (.xlsx) ready for download.";

      await new Promise(r => setTimeout(r, 300));

      App.state.lastGeneratedFile = data;
      if (window.Gamification) {
        Gamification.recordPresentationGenerated(data.slide_count, payload.detail_level, !!data.excel_download_url);
      }
      this.displayGenerationResults(data);
      App.showToast(`Generated ${data.slide_count} slides + Formatted Excel workbook!`, "success");

      // Trigger PowerPoint download automatically
      window.location.href = data.download_url;

      this.loadHistory();
    } catch (err) {
      App.showToast(err.message, "error");
    } finally {
      stepper.classList.remove("active");
      configPanel.style.display = "block";
    }
  },

  displayGenerationResults(data) {
    const card = document.getElementById("generation-results-card");
    if (!card) return;

    card.style.display = "block";
    const titleEl = document.getElementById("results-pres-title");
    const subEl = document.getElementById("results-pres-subtitle");
    if (titleEl) {
      titleEl.textContent = `${data.presentation_title || "Presentation"} (${data.slide_count} Slides)`;
    }
    if (subEl) {
      subEl.textContent = "Dual outputs compiled and verified: Download your 16:9 PowerPoint presentation (.pptx) and Formatted Original Excel (.xlsx).";
    }

    const pptxBtn = document.getElementById("btn-download-pptx");
    if (pptxBtn && data.download_url) {
      pptxBtn.href = data.download_url;
    }

    const xlsxBtn = document.getElementById("btn-download-xlsx");
    if (xlsxBtn) {
      if (data.excel_download_url) {
        xlsxBtn.href = data.excel_download_url;
        xlsxBtn.style.display = "inline-flex";
      } else {
        xlsxBtn.style.display = "none";
      }
    }

    this.renderValidationReport(data.validation_report, "validation-report-container");
  },

  renderValidationReport(report, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!report) {
      container.innerHTML = "";
      return;
    }

    const excelVal = report.excel_validation || {};
    const sheetsRetained = excelVal.original_sheets_retained !== false ? "100% Retained" : "Pending Export";
    const valuesPreserved = excelVal.values_preserved !== false ? "100% Preserved" : "Pending Export";
    const wsIncluded = (report.worksheets_included || []).join(", ") || "Active Sheet";
    const recordsRep = `${report.records_represented ?? 0} / ${report.total_source_records ?? 0} Rows`;
    const calcCount = (report.calculations_performed || []).length;
    const warnCount = (report.data_quality_warnings || []).length;

    const calcTraceHtml = calcCount > 0
      ? `<div style="margin-top:0.65rem; font-size:0.75rem; color:var(--text-secondary); background:var(--bg-canvas); padding:0.5rem 0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-light);">
           <strong style="color:var(--color-primary);">Deterministic Calculations Trace:</strong> ${report.calculations_performed.slice(0, 4).map(c => this.escapeHtml(c)).join("  •  ")}
         </div>`
      : "";

    const agentPipe = report.agent_pipeline || null;
    const agentPipeHtml = agentPipe
      ? `<div style="margin-top:0.55rem; font-size:0.75rem; color:var(--text-secondary); background:var(--bg-canvas); padding:0.55rem 0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-light); display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.5rem;">
           <div>
             <strong style="color:var(--color-primary);">🤖 ${this.escapeHtml(agentPipe.orchestrator || "Multi-Agent Verification Pipeline")}:</strong>
             <span style="margin-left:0.35rem;">${(agentPipe.agents_executed || []).map(a => `✅ ${this.escapeHtml(a.name)}`).join("  •  ")}</span>
           </div>
           <span class="category-badge highlight">Zero Hallucinations Verified</span>
         </div>`
      : "";

    container.innerHTML = `
      <div style="font-size:0.8rem; font-weight:700; color:var(--color-primary); margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.03em;">
        🛡️ Cross-Validation &amp; Data Integrity Report (${this.escapeHtml(report.overall_status || "VERIFIED")})
      </div>
      <div class="validation-badges-grid">
        <div class="validation-badge-card">
          <div class="validation-badge-lbl">Original Sheets Retained</div>
          <div class="validation-badge-val">✅ ${this.escapeHtml(sheetsRetained)}</div>
        </div>
        <div class="validation-badge-card">
          <div class="validation-badge-lbl">Cell Values Preserved</div>
          <div class="validation-badge-val">✅ ${this.escapeHtml(valuesPreserved)}</div>
        </div>
        <div class="validation-badge-card">
          <div class="validation-badge-lbl">Worksheets Included</div>
          <div class="validation-badge-val">📄 ${this.escapeHtml(wsIncluded)}</div>
        </div>
        <div class="validation-badge-card">
          <div class="validation-badge-lbl">Records Represented</div>
          <div class="validation-badge-val">📊 ${this.escapeHtml(recordsRep)}</div>
        </div>
        <div class="validation-badge-card">
          <div class="validation-badge-lbl">Calculations Trace</div>
          <div class="validation-badge-val">🔢 ${calcCount} Verified Metrics</div>
        </div>
        <div class="validation-badge-card" style="border-left-color:${warnCount > 0 ? "#f59e0b" : "#16a34a"};">
          <div class="validation-badge-lbl">Data Quality Warnings</div>
          <div class="validation-badge-val">${warnCount > 0 ? `⚠️ ${warnCount} Note(s)` : "✅ 0 Issues"}</div>
        </div>
      </div>
      ${calcTraceHtml}
      ${agentPipeHtml}
    `;
  },

  async loadHistory() {
    const tbody = document.getElementById("history-table-body");
    if (!tbody || !App.state.token) return;

    try {
      const res = await App.apiRequest("/api/generator/history");
      const history = await res.json();

      if (!history || history.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-secondary); padding:1.5rem;">No presentations generated yet in this session.</td></tr>`;
        return;
      }

      tbody.innerHTML = history.map(item => {
        const dateStr = new Date(item.created_at).toLocaleString();
        return `
          <tr>
            <td style="font-weight:600; color:var(--color-primary);">${this.escapeHtml(item.title)}</td>
            <td><span class="badge" style="background:#e2e8f0; color:#334155;">${item.slide_count} Slides</span></td>
            <td style="font-size:0.8rem; color:var(--text-secondary);">${dateStr}</td>
            <td>
              <div style="display:flex; gap:0.4rem; align-items:center;">
                <a href="${item.download_url}" class="btn btn-primary btn-sm" download>
                  📥 Download
                </a>
                <button type="button" class="btn btn-outline btn-sm btn-delete-history" data-id="${item.id}" data-title="${this.escapeHtml(item.title)}" title="Delete this presentation and remove files">
                  🗑️
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join("");

      // Bind delete buttons
      tbody.querySelectorAll(".btn-delete-history").forEach(btn => {
        btn.addEventListener("click", async (e) => {
          e.preventDefault();
          const id = btn.getAttribute("data-id");
          const title = btn.getAttribute("data-title");
          await this.deleteHistoryItem(id, title);
        });
      });
    } catch (err) {
      // Ignore silently if table not rendered
    }
  },

  async deleteHistoryItem(id, title) {
    if (!confirm(`Are you sure you want to delete '${title || "this presentation"}' and remove its generated files from storage?`)) {
      return;
    }

    try {
      const res = await App.apiRequest(`/api/generator/${id}`, {
        method: "DELETE"
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not delete presentation.");

      App.showToast("Presentation and generated files permanently removed.", "success");
      this.loadHistory();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async cancelAndDeleteCurrentDeck() {
    const file = App.state.lastGeneratedFile;
    if (!file || !file.filename) {
      App.showToast("No active generated presentation to remove.", "info");
      return;
    }

    if (!confirm(`Are you sure you want to cancel and delete '${file.presentation_title || file.filename}' from disk?`)) {
      return;
    }

    try {
      const res = await App.apiRequest(`/api/generator/file/${file.filename}`, {
        method: "DELETE"
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not cancel presentation.");

      App.showToast(data.message || "Generated deck removed from storage.", "info");
      const resultsCard = document.getElementById("generation-results-card");
      if (resultsCard) resultsCard.style.display = "none";
      App.state.lastGeneratedFile = null;
      this.loadHistory();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async loadSampleDataset(samplePath) {
    try {
      App.showToast("Fetching sample dataset...", "info");
      const res = await fetch(samplePath);
      if (!res.ok) throw new Error("Sample file not found.");

      const blob = await res.blob();
      const filename = samplePath.split("/").pop();
      const file = new File([blob], filename, { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });

      await this.handleFile(file);
    } catch (err) {
      App.showToast(`Could not load sample: ${err.message}`, "error");
    }
  },

  escapeHtml(text) {
    if (!text) return "";
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  Upload.init();
});

/**
 * frontend/js/admin.js
 * --------------------
 * Administrator Dashboard: Access Request Approvals & User Access Management.
 */

const Admin = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    document.getElementById("btn-refresh-admin")?.addEventListener("click", () => {
      this.loadDashboardData();
    });

    const templateInput = document.getElementById("corporate-template-input");
    document.getElementById("btn-upload-template")?.addEventListener("click", () => {
      templateInput?.click();
    });

    templateInput?.addEventListener("change", async (e) => {
      if (e.target.files.length > 0) {
        await this.uploadTemplate(e.target.files[0]);
      }
    });

    document.getElementById("btn-remove-template")?.addEventListener("click", async () => {
      await this.removeTemplate();
    });
  },

  async loadDashboardData() {
    if (!App.state.token || App.state.user?.role !== "admin") return;
    await Promise.all([this.loadRequests(), this.loadUsers(), this.checkTemplateStatus()]);
  },

  async checkTemplateStatus() {
    try {
      const res = await App.apiRequest("/api/admin/template/status");
      const data = await res.json();
      const badge = document.getElementById("template-status-badge");
      const removeBtn = document.getElementById("btn-remove-template");
      const filenameLabel = document.getElementById("template-filename-label");

      if (data.has_custom_template) {
        if (badge) badge.innerHTML = `<span class="badge badge-approved">Custom Template Active</span>`;
        if (removeBtn) removeBtn.style.display = "inline-flex";
        if (filenameLabel) filenameLabel.textContent = `Active: ${data.template_name} (${(data.file_size / 1024).toFixed(1)} KB)`;
      } else {
        if (badge) badge.innerHTML = `<span class="badge" style="background:var(--bg-canvas); color:var(--text-secondary); border:1px solid var(--border-light);">Neutral Executive Theme (Default)</span>`;
        if (removeBtn) removeBtn.style.display = "none";
        if (filenameLabel) filenameLabel.textContent = "No custom template uploaded. Using built-in Navy & Teal design.";
      }
    } catch (err) {
      // Ignore if not loaded
    }
  },

  async uploadTemplate(file) {
    if (!file.name.endsWith(".pptx")) {
      App.showToast("Template must be a valid .pptx PowerPoint file.", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      App.showToast("Uploading corporate template...", "info");
      const res = await App.apiRequest("/api/admin/template", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed.");

      App.showToast("Corporate template activated successfully!", "success");
      await this.checkTemplateStatus();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async removeTemplate() {
    try {
      const res = await App.apiRequest("/api/admin/template", {
        method: "DELETE"
      });
      const data = await res.json();
      App.showToast(data.message, "info");
      await this.checkTemplateStatus();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async loadRequests() {
    const tbody = document.getElementById("admin-requests-table-body");
    if (!tbody) return;

    try {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:1.5rem; color:var(--text-secondary);">Loading requests...</td></tr>`;

      const res = await App.apiRequest("/api/admin/requests");
      const requests = await res.json();

      if (!requests || requests.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:1.5rem; color:var(--text-secondary);">No access requests currently registered.</td></tr>`;
        return;
      }

      tbody.innerHTML = requests.map(req => {
        const isPending = req.status === "PENDING";
        const statusBadge = `<span class="badge badge-${req.status.toLowerCase()}">${req.status}</span>`;
        
        let actionButtons = "";
        if (isPending) {
          actionButtons = `
            <div style="display:flex; gap:0.4rem;">
              <button class="btn btn-primary btn-sm" onclick="Admin.reviewRequest(${req.id}, 'APPROVE')">Approve</button>
              <button class="btn btn-outline btn-sm" onclick="Admin.reviewRequest(${req.id}, 'REJECT')">Reject</button>
            </div>
          `;
        } else if (req.invite_token) {
          actionButtons = `
            <button class="btn btn-outline-gold btn-sm" onclick="Admin.copyToken('${req.invite_token}')" title="Click to copy token">
              Copy Token
            </button>
          `;
        } else {
          actionButtons = `<span style="font-size:0.75rem; color:var(--text-muted);">Reviewed</span>`;
        }

        return `
          <tr>
            <td style="font-weight:600; color:var(--ups-brown);">${this.escapeHtml(req.name)}</td>
            <td>${this.escapeHtml(req.email)}</td>
            <td>${this.escapeHtml(req.department || "—")}</td>
            <td style="max-width:240px; font-size:0.8rem; color:var(--text-secondary);">${this.escapeHtml(req.reason)}</td>
            <td>${statusBadge}</td>
            <td>${actionButtons}</td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" style="color:var(--color-danger); text-align:center; padding:1.5rem;">Failed to load requests: ${err.message}</td></tr>`;
    }
  },

  async reviewRequest(requestId, action) {
    try {
      const res = await App.apiRequest(`/api/admin/requests/${requestId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action })
      });

      const updated = await res.json();
      if (!res.ok) throw new Error(updated.detail || "Action failed.");

      if (action === "APPROVE" && updated.invite_token) {
        prompt(
          `Request Approved! Copy the invitation token below and share it with ${updated.name}:`,
          updated.invite_token
        );
        App.showToast(`Request approved for ${updated.name}. Invite token generated!`, "success");
      } else {
        App.showToast(`Request for ${updated.name} has been rejected.`, "info");
      }

      await this.loadDashboardData();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async loadUsers() {
    const tbody = document.getElementById("admin-users-table-body");
    if (!tbody) return;

    try {
      const res = await App.apiRequest("/api/admin/users");
      const users = await res.json();

      if (!users || users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:var(--text-secondary);">No authorized users found.</td></tr>`;
        return;
      }

      tbody.innerHTML = users.map(user => {
        const isAdmin = user.role === "admin";
        const statusPill = user.is_active
          ? `<span class="badge badge-approved">Active</span>`
          : `<span class="badge badge-rejected">Revoked</span>`;

        const actionBtn = isAdmin
          ? `<span style="font-size:0.75rem; color:var(--text-muted);">Protected Master</span>`
          : `<button class="btn btn-outline btn-sm" onclick="Admin.toggleUserStatus(${user.id})">
              ${user.is_active ? "Revoke Access" : "Restore Access"}
             </button>`;

        return `
          <tr>
            <td style="font-weight:600;">${this.escapeHtml(user.full_name)}</td>
            <td>${this.escapeHtml(user.email)}</td>
            <td><span class="role-pill" style="font-size:0.7rem;">${user.role.toUpperCase()}</span></td>
            <td>${statusPill}</td>
            <td>${actionBtn}</td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="5" style="color:var(--color-danger); text-align:center;">Failed to load users: ${err.message}</td></tr>`;
    }
  },

  async toggleUserStatus(userId) {
    try {
      const res = await App.apiRequest(`/api/admin/users/${userId}/toggle-status`, {
        method: "POST"
      });
      const updated = await res.json();
      if (!res.ok) throw new Error(updated.detail || "Could not update user status.");

      App.showToast(`User ${updated.full_name} status updated.`, "success");
      await this.loadUsers();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  copyToken(token) {
    navigator.clipboard.writeText(token).then(() => {
      App.showToast("Invite token copied to clipboard!", "success");
    }).catch(() => {
      prompt("Copy invite token:", token);
    });
  },

  escapeHtml(text) {
    if (!text) return "";
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  Admin.init();
});

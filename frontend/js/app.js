/**
 * frontend/js/app.js
 * ------------------
 * Central State Manager, View Router, Modal Controller, and Toast Notifications.
 */

const App = {
  state: {
    token: localStorage.getItem("ups_token") || null,
    user: JSON.parse(localStorage.getItem("ups_user") || "null"),
    currentView: "landing",
    currentFile: null,      // Inspection metadata from upload
    selectedSheet: null,
    selectedSlides: 4,      // Default 4 slides
    lastGeneratedFile: null,
    eyeComfortDark: localStorage.getItem("patelspark_eye_comfort") === "dark",
  },

  init() {
    this.applyEyeComfort();
    this.bindEvents();
    this.updateAuthUI();
    
    // Auto-route based on session
    if (this.state.token && this.state.user) {
      this.switchView("dashboard");
    } else {
      this.switchView("landing");
    }
  },

  openGuide(e) {
    if (e && typeof e.preventDefault === "function") {
      e.preventDefault();
    }
    this.openModal("modal-user-guide");
  },

  toggleEyeComfort() {
    this.state.eyeComfortDark = !this.state.eyeComfortDark;
    localStorage.setItem("patelspark_eye_comfort", this.state.eyeComfortDark ? "dark" : "light");
    this.applyEyeComfort();
    this.showToast(
      this.state.eyeComfortDark
        ? "🌙 Eye-Comfort Night Mode enabled (Low-Glare Slate)."
        : "☀️ Warm Eye-Comfort Daylight Mode enabled.",
      "info"
    );
  },

  applyEyeComfort() {
    const isDark = !!this.state.eyeComfortDark;
    document.body.classList.toggle("eye-comfort-dark", isDark);
    const btn = document.getElementById("btn-toggle-eye-comfort");
    const icon = document.getElementById("eye-comfort-icon");
    const label = document.getElementById("eye-comfort-label");
    if (btn) btn.classList.toggle("active", isDark);
    if (icon) icon.textContent = isDark ? "☀️" : "🌙";
    if (label) label.textContent = isDark ? "Day Comfort" : "Eye Comfort";
  },

  bindEvents() {
    // Navigation routing
    document.getElementById("nav-brand-logo")?.addEventListener("click", (e) => {
      e.preventDefault();
      this.switchView(this.state.token ? "dashboard" : "landing");
    });

    document.getElementById("nav-btn-home")?.addEventListener("click", (e) => {
      e.preventDefault();
      this.switchView("landing");
    });

    document.getElementById("nav-btn-guide")?.addEventListener("click", (e) => {
      e.preventDefault();
      this.openModal("modal-user-guide");
    });

    document.getElementById("hero-btn-guide")?.addEventListener("click", (e) => {
      e.preventDefault();
      this.openModal("modal-user-guide");
    });

    document.getElementById("nav-btn-workspace")?.addEventListener("click", (e) => {
      e.preventDefault();
      this.switchView("dashboard");
    });

    document.getElementById("nav-btn-admin")?.addEventListener("click", (e) => {
      e.preventDefault();
      this.switchView("admin");
      if (window.Admin) Admin.loadDashboardData();
    });

    // Hero buttons
    document.getElementById("hero-btn-request")?.addEventListener("click", () => {
      this.openModal("modal-request-access");
    });

    document.getElementById("hero-btn-login")?.addEventListener("click", () => {
      this.openModal("modal-login");
    });

    document.getElementById("btn-open-request-access")?.addEventListener("click", () => {
      this.openModal("modal-request-access");
    });

    document.getElementById("btn-open-login")?.addEventListener("click", () => {
      this.openModal("modal-login");
    });

    document.getElementById("btn-logout")?.addEventListener("click", () => {
      if (window.Auth) Auth.logout();
    });

    // Modal close triggers
    document.querySelectorAll("[data-close-modal]").forEach(el => {
      el.addEventListener("click", () => {
        const modalId = el.getAttribute("data-close-modal");
        this.closeModal(modalId);
      });
    });

    // Close on overlay backdrop click
    document.querySelectorAll(".modal-overlay").forEach(overlay => {
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) {
          overlay.classList.remove("active");
        }
      });
    });
  },

  switchView(viewName) {
    this.state.currentView = viewName;
    const views = ["landing", "dashboard", "admin"];
    
    views.forEach(v => {
      const el = document.getElementById(`view-${v}`);
      if (el) el.style.display = (v === viewName) ? "block" : "none";
    });

    // Update active nav links
    document.querySelectorAll(".nav-link").forEach(link => link.classList.remove("active"));
    if (viewName === "landing") document.getElementById("nav-btn-home")?.classList.add("active");
    if (viewName === "dashboard") document.getElementById("nav-btn-workspace")?.classList.add("active");
    if (viewName === "admin") document.getElementById("nav-btn-admin")?.classList.add("active");
  },

  updateAuthUI() {
    const isAuthed = !!this.state.token;
    const user = this.state.user;

    const guestActions = document.getElementById("nav-guest-actions");
    const userActions = document.getElementById("nav-user-actions");
    const navWorkspace = document.getElementById("nav-btn-workspace");
    const navAdmin = document.getElementById("nav-btn-admin");

    if (isAuthed && user) {
      if (guestActions) guestActions.style.display = "none";
      if (userActions) userActions.style.display = "flex";
      if (navWorkspace) navWorkspace.style.display = "block";

      const nameEl = document.getElementById("user-display-name");
      const roleEl = document.getElementById("user-display-role");
      if (nameEl) nameEl.textContent = user.full_name || user.email;
      if (roleEl) {
        roleEl.textContent = (user.role || "USER").toUpperCase();
        roleEl.style.backgroundColor = (user.role === "admin") ? "var(--ups-gold)" : "#94a3b8";
        roleEl.style.color = (user.role === "admin") ? "var(--ups-brown)" : "#ffffff";
      }

      // Show admin tab only for administrators
      if (navAdmin) navAdmin.style.display = (user.role === "admin") ? "block" : "none";
    } else {
      if (guestActions) guestActions.style.display = "flex";
      if (userActions) userActions.style.display = "none";
      if (navWorkspace) navWorkspace.style.display = "none";
      if (navAdmin) navAdmin.style.display = "none";
    }
  },

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("active");
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("active");
  },

  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type === "error" ? "toast-error" : type === "success" ? "toast-success" : ""}`;
    toast.innerHTML = `
      <span>${type === "error" ? "⚠️" : type === "success" ? "✅" : "ℹ️"}</span>
      <div style="flex: 1;">${message}</div>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  },

  async apiRequest(url, options = {}) {
    options.headers = options.headers || {};
    if (this.state.token) {
      options.headers["Authorization"] = `Bearer ${this.state.token}`;
    }

    try {
      const response = await fetch(url, options);
      if (response.status === 401) {
        this.showToast("Your session has expired. Please sign in again.", "error");
        if (window.Auth) Auth.logout();
        throw new Error("Unauthorized");
      }
      return response;
    } catch (err) {
      throw err;
    }
  },
};

window.App = App;

document.addEventListener("DOMContentLoaded", () => {
  App.init();
});

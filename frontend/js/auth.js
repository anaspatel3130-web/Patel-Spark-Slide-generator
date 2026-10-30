/**
 * frontend/js/auth.js
 * -------------------
 * Authentication Controller: Login, Request Access, and Account Activation.
 */

const Auth = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    // Open Activation from Login modal
    document.getElementById("btn-open-activation-from-login")?.addEventListener("click", () => {
      App.closeModal("modal-login");
      App.openModal("modal-activate");
    });

    // Login Form Submit
    document.getElementById("form-login")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await this.handleLogin();
    });

    // Request Access Form Submit
    document.getElementById("form-request-access")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await this.handleRequestAccess();
    });

    // Account Activation Form Submit
    document.getElementById("form-activate")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await this.handleActivate();
    });
  },

  async handleLogin() {
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;
    const btn = document.getElementById("btn-submit-login");

    try {
      btn.disabled = true;
      btn.textContent = "Verifying...";

      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication failed.");
      }

      // Save session
      App.state.token = data.access_token;
      App.state.user = {
        email: data.email,
        full_name: data.full_name,
        role: data.role
      };
      localStorage.setItem("ups_token", data.access_token);
      localStorage.setItem("ups_user", JSON.stringify(App.state.user));

      App.updateAuthUI();
      App.closeModal("modal-login");
      App.switchView("dashboard");
      App.showToast(`Welcome back, ${data.full_name}!`, "success");

      // Load user history
      if (window.Upload) Upload.loadHistory();
    } catch (err) {
      App.showToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Sign In";
    }
  },

  async handleRequestAccess() {
    const name = document.getElementById("req-name").value.trim();
    const email = document.getElementById("req-email").value.trim();
    const department = document.getElementById("req-dept").value.trim();
    const reason = document.getElementById("req-reason").value.trim();
    const btn = document.getElementById("btn-submit-request");

    try {
      btn.disabled = true;
      btn.textContent = "Submitting...";

      const res = await fetch("/api/auth/request-access", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, department, reason })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Could not submit request.");
      }

      App.closeModal("modal-request-access");
      document.getElementById("form-request-access").reset();
      App.showToast(
        "Request submitted successfully! The administrator has been notified to review your credentials.",
        "success"
      );
    } catch (err) {
      App.showToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Submit Request";
    }
  },

  async handleActivate() {
    const invite_token = document.getElementById("act-token").value.trim();
    const full_name = document.getElementById("act-name").value.trim();
    const password = document.getElementById("act-password").value;

    try {
      const res = await fetch("/api/auth/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ invite_token, full_name, password })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Activation failed.");
      }

      App.closeModal("modal-activate");
      document.getElementById("form-activate").reset();
      App.showToast("Account activated successfully! Please sign in with your password.", "success");
      App.openModal("modal-login");
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  logout() {
    App.state.token = null;
    App.state.user = null;
    localStorage.removeItem("ups_token");
    localStorage.removeItem("ups_user");
    App.updateAuthUI();
    App.switchView("landing");
    App.showToast("You have been signed out.", "info");
  }
};

document.addEventListener("DOMContentLoaded", () => {
  Auth.init();
});

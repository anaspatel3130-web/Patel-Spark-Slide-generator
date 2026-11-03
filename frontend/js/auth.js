/**
 * frontend/js/auth.js
 * -------------------
 * Authentication Controller: Direct Owner Access, 1-Click Social Sign-In,
 * Password Login, Request Access, and Account Activation.
 */

const Auth = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    // 1. Direct Owner Access for Anas S Patel (anaspatel3130@gmail.com)
    document.querySelectorAll(".btn-trigger-owner-access").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        await this.handleDirectOwnerAccess();
      });
    });

    // 2. 1-Click Social / Instant Sign-In (Google, GitHub, Facebook, Guest)
    document.getElementById("btn-social-google")?.addEventListener("click", async () => {
      // Direct 1-click Google authentication
      await this.handleSocialLogin("google", "anaspatel3130@gmail.com", "Anas S Patel");
    });

    document.getElementById("btn-social-github")?.addEventListener("click", async () => {
      await this.handleSocialLogin("github", "anaspatel3130@gmail.com", "Anas S Patel");
    });

    document.getElementById("btn-social-guest")?.addEventListener("click", async () => {
      await this.handleSocialLogin("guest", null, "Guest Analyst");
    });

    // 3. Quick-fill credentials helpers
    document.getElementById("btn-fill-owner-creds")?.addEventListener("click", () => {
      const emailEl = document.getElementById("login-email");
      const passEl = document.getElementById("login-password");
      if (emailEl) emailEl.value = "anaspatel3130@gmail.com";
      if (passEl) passEl.value = "PatelSpark2026!";
      App.showToast("⚡ Owner credentials filled for anaspatel3130@gmail.com.", "info");
    });

    document.getElementById("btn-fill-admin-creds")?.addEventListener("click", () => {
      const emailEl = document.getElementById("login-email");
      const passEl = document.getElementById("login-password");
      if (emailEl) emailEl.value = "admin@patelspark.internal";
      if (passEl) passEl.value = "PatelSpark2026!Admin";
      App.showToast("Internal Admin credentials filled.", "info");
    });

    // 4. Open Activation from Login modal
    document.getElementById("btn-open-activation-from-login")?.addEventListener("click", () => {
      App.closeModal("modal-login");
      App.openModal("modal-activate");
    });

    // 5. Login Form Submit
    document.getElementById("form-login")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await this.handleLogin();
    });

    // 6. Request Access Form Submit
    document.getElementById("form-request-access")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await this.handleRequestAccess();
    });

    // 7. Account Activation Form Submit
    document.getElementById("form-activate")?.addEventListener("submit", async (e) => {
      e.preventDefault();
      await this.handleActivate();
    });
  },

  async handleDirectOwnerAccess() {
    try {
      App.showToast("⚡ Authorizing Direct Owner Access for anaspatel3130@gmail.com...", "info");
      const res = await fetch("/api/auth/direct-owner-access", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(App.formatErrorMessage(data));
      }

      this.saveSession(data);
      App.closeModal("modal-login");
      App.closeModal("modal-request-access");
      App.switchView("dashboard");
      App.showToast("⚡ Welcome Anas S Patel! Master Owner Access active.", "success");

      if (window.Upload) Upload.loadHistory();
    } catch (err) {
      App.showToast(App.formatErrorMessage(err), "error");
    }
  },

  async handleSocialLogin(provider = "guest", email = null, name = null) {
    try {
      const res = await fetch("/api/auth/social-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, email, name })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(App.formatErrorMessage(data));
      }

      this.saveSession(data);
      App.closeModal("modal-login");
      App.closeModal("modal-request-access");
      App.switchView("dashboard");
      const providerLabel = provider.charAt(0).toUpperCase() + provider.slice(1);
      App.showToast(`Signed in via ${providerLabel}! Welcome, ${data.full_name}.`, "success");

      if (window.Upload) Upload.loadHistory();
    } catch (err) {
      App.showToast(App.formatErrorMessage(err), "error");
    }
  },

  saveSession(data) {
    App.state.token = data.access_token;
    App.state.user = {
      email: data.email,
      full_name: data.full_name,
      role: data.role
    };
    localStorage.setItem("ups_token", data.access_token);
    localStorage.setItem("ups_user", JSON.stringify(App.state.user));
    App.updateAuthUI();
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
        throw new Error(App.formatErrorMessage(data));
      }

      this.saveSession(data);
      App.closeModal("modal-login");
      App.switchView("dashboard");
      App.showToast(`Welcome back, ${data.full_name}!`, "success");

      if (window.Upload) Upload.loadHistory();
    } catch (err) {
      App.showToast(App.formatErrorMessage(err), "error");
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

    // If owner accidentally submits request access for himself, grant direct access!
    if (email.toLowerCase() === "anaspatel3130@gmail.com") {
      await this.handleDirectOwnerAccess();
      return;
    }

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
        throw new Error(App.formatErrorMessage(data));
      }

      App.closeModal("modal-request-access");
      document.getElementById("form-request-access").reset();
      App.showToast(
        "Request submitted successfully! The administrator (anaspatel3130@gmail.com) has received an email notification.",
        "success"
      );
    } catch (err) {
      App.showToast(App.formatErrorMessage(err), "error");
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
        throw new Error(App.formatErrorMessage(data));
      }

      App.closeModal("modal-activate");
      document.getElementById("form-activate").reset();
      App.showToast("Account activated successfully! Please sign in with your password.", "success");
      App.openModal("modal-login");
    } catch (err) {
      App.showToast(App.formatErrorMessage(err), "error");
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

window.Auth = Auth;

document.addEventListener("DOMContentLoaded", () => {
  Auth.init();
});

/**
 * frontend/js/gamification.js
 * ----------------------------
 * Patel'Spark Gamified Dashboard Engine:
 * - Analyst Rank Tiers & XP Progression System
 * - Live Telemetry Telemetry HUD (Slides, Worksheets, Verified Records, 100% Accuracy)
 * - Unlockable Achievement Trophies & Milestones
 * - Interactive Particle Celebration on Successful Presentation Synthesis
 */

const Gamification = {
  storageKey: "patelspark_gamification_v1",

  badgesConfig: [
    {
      id: "first_ignition",
      title: "Ignition Spark",
      icon: "⚡",
      desc: "Uploaded your first Excel workbook into the Patel'Spark studio",
      xp: 100,
    },
    {
      id: "zero_hallucination",
      title: "Zero Hallucination",
      icon: "🎯",
      desc: "Verified 100% deterministic calculations with zero AI fabricated figures",
      xp: 150,
    },
    {
      id: "global_navigator",
      title: "Global Navigator",
      icon: "🌐",
      desc: "Discovered international routes, connection hubs, and flight schedules",
      xp: 150,
    },
    {
      id: "vault_keeper",
      title: "Vault Keeper",
      icon: "📑",
      desc: "Generated a Complete Information Preservation deck with paginated source tables",
      xp: 200,
    },
    {
      id: "dual_artisan",
      title: "Dual Artisan",
      icon: "🏆",
      desc: "Synthesized both approved UPS PowerPoint (.pptx) & formatted Excel (.xlsx)",
      xp: 200,
    },
    {
      id: "corporate_master",
      title: "Corporate Master",
      icon: "🛡️",
      desc: "Validated approved UPS corporate presentation templates with watermarks",
      xp: 250,
    },
  ],

  levels: [
    { lvl: 1, title: "Data Trainee", icon: "🌱", minXP: 0, maxXP: 250 },
    { lvl: 2, title: "Insight Specialist", icon: "📊", minXP: 250, maxXP: 600 },
    { lvl: 3, title: "Senior Analytics Officer", icon: "🚀", minXP: 600, maxXP: 1200 },
    { lvl: 4, title: "Lead Automation Architect", icon: "⚡", minXP: 1200, maxXP: 2200 },
    { lvl: 5, title: "Master Presentation Director", icon: "👑", minXP: 2200, maxXP: 99999 },
  ],

  state: {
    xp: 150,
    slidesSynthesized: 0,
    sheetsAnalyzed: 0,
    recordsVerified: 0,
    unlockedBadges: ["zero_hallucination"],
  },

  init() {
    this.loadState();
    this.renderHUD();
    this.bindEvents();
  },

  loadState() {
    try {
      const saved = localStorage.getItem(this.storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        this.state = Object.assign(this.state, parsed);
      }
    } catch (e) {
      // Use defaults
    }
  },

  saveState() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.state));
    } catch (e) {}
  },

  getCurrentLevel() {
    const xp = this.state.xp;
    for (let i = this.levels.length - 1; i >= 0; i--) {
      if (xp >= this.levels[i].minXP) {
        return this.levels[i];
      }
    }
    return this.levels[0];
  },

  getNextLevel() {
    const cur = this.getCurrentLevel();
    const idx = this.levels.findIndex(l => l.lvl === cur.lvl);
    if (idx < this.levels.length - 1) {
      return this.levels[idx + 1];
    }
    return cur;
  },

  addXP(points, reason = "") {
    const prevLvl = this.getCurrentLevel();
    this.state.xp += points;
    const newLvl = this.getCurrentLevel();
    this.saveState();
    this.renderHUD();

    if (reason && window.App) {
      App.showToast(`+${points} XP: ${reason}`, "info");
    }

    if (newLvl.lvl > prevLvl.lvl && window.App) {
      this.triggerCelebration();
      App.showToast(`🎉 LEVEL UP! You are now a ${newLvl.icon} ${newLvl.title}!`, "success");
    }
  },

  unlockBadge(badgeId) {
    if (this.state.unlockedBadges.includes(badgeId)) return;
    const badge = this.badgesConfig.find(b => b.id === badgeId);
    if (!badge) return;

    this.state.unlockedBadges.push(badgeId);
    this.saveState();
    this.addXP(badge.xp, `Achievement Unlocked: ${badge.title}`);

    if (window.App) {
      App.showToast(`🏆 BADGE UNLOCKED: "${badge.title}" (+${badge.xp} XP)`, "success");
    }
  },

  recordWorkbookUpload(sheetCount = 1, recordCount = 0) {
    this.state.sheetsAnalyzed += sheetCount;
    this.state.recordsVerified += recordCount;
    this.unlockBadge("first_ignition");
    this.addXP(50, `Ingested ${sheetCount} Sheet(s)`);
    this.saveState();
    this.renderHUD();
  },

  recordPresentationGenerated(slideCount = 4, detailLevel = "summary", hasExcel = true) {
    this.state.slidesSynthesized += slideCount;
    this.unlockBadge("zero_hallucination");

    if (hasExcel) {
      this.unlockBadge("dual_artisan");
    }
    if (detailLevel === "complete" || slideCount > 6) {
      this.unlockBadge("vault_keeper");
    }
    if (this.state.slidesSynthesized >= 15) {
      this.unlockBadge("corporate_master");
    }

    const xpEarned = 100 + slideCount * 15;
    this.addXP(xpEarned, `Synthesized ${slideCount}-Slide Corporate Presentation`);
    this.saveState();
    this.renderHUD();
    this.triggerCelebration();
  },

  renderHUD() {
    const curLvl = this.getCurrentLevel();
    const nextLvl = this.getNextLevel();

    // 1. Level & Avatar
    const avatarEl = document.getElementById("gamified-rank-avatar");
    if (avatarEl) avatarEl.textContent = curLvl.icon;

    const badgeEl = document.getElementById("gamified-level-badge");
    if (badgeEl) badgeEl.textContent = `LVL ${curLvl.lvl}`;

    const titleEl = document.getElementById("gamified-rank-title");
    if (titleEl) titleEl.textContent = curLvl.title;

    // 2. XP Progress
    const xpRange = nextLvl.minXP - curLvl.minXP;
    const currentProgress = this.state.xp - curLvl.minXP;
    const pct = (curLvl.lvl === 5) ? 100 : Math.min(100, Math.max(8, Math.round((currentProgress / Math.max(1, xpRange)) * 100)));

    const fillEl = document.getElementById("gamified-xp-fill");
    if (fillEl) fillEl.style.width = `${pct}%`;

    const textEl = document.getElementById("gamified-xp-text");
    if (textEl) {
      if (curLvl.lvl === 5) {
        textEl.textContent = `${this.state.xp} XP • Maximum Analyst Tier Reached!`;
      } else {
        textEl.textContent = `${this.state.xp} / ${nextLvl.minXP} XP to ${nextLvl.title}`;
      }
    }

    // 3. Stats HUD
    const statSlides = document.getElementById("hud-stat-slides");
    if (statSlides) statSlides.textContent = this.state.slidesSynthesized;

    const statSheets = document.getElementById("hud-stat-sheets");
    if (statSheets) statSheets.textContent = this.state.sheetsAnalyzed;

    const statRecords = document.getElementById("hud-stat-records");
    if (statRecords) statRecords.textContent = Number(this.state.recordsVerified).toLocaleString();

    // 4. Badges count
    const badgeCountEl = document.getElementById("gamified-badge-count");
    if (badgeCountEl) {
      badgeCountEl.textContent = `${this.state.unlockedBadges.length}/${this.badgesConfig.length}`;
    }
  },

  renderAchievementsModal() {
    const container = document.getElementById("achievements-grid-container");
    if (!container) return;

    container.innerHTML = this.badgesConfig.map(badge => {
      const isUnlocked = this.state.unlockedBadges.includes(badge.id);
      return `
        <div class="achievement-card ${isUnlocked ? 'unlocked' : 'locked'}">
          <div class="achievement-icon">${badge.icon}</div>
          <div class="achievement-body">
            <div class="achievement-header">
              <span class="achievement-title">${this.escapeHtml(badge.title)}</span>
              <span class="achievement-xp">+${badge.xp} XP</span>
            </div>
            <div class="achievement-desc">${this.escapeHtml(badge.desc)}</div>
            <div class="achievement-status">
              ${isUnlocked ? '✅ <span class="text-success" style="font-weight:700;">Unlocked</span>' : '🔒 <span>Locked</span>'}
            </div>
          </div>
        </div>
      `;
    }).join("");
  },

  triggerCelebration() {
    // Lightweight canvas particle sparkle celebration
    const container = document.createElement("div");
    container.className = "celebration-particle-container";
    document.body.appendChild(container);

    const colors = ["#f97316", "#ffb500", "#10b981", "#38bdf8", "#ec4899", "#ffffff"];
    const count = 38;

    for (let i = 0; i < count; i++) {
      const p = document.createElement("div");
      p.className = "celebration-particle";
      p.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      p.style.left = `${Math.random() * 100}vw`;
      p.style.top = "-10px";
      p.style.transform = `scale(${Math.random() * 0.8 + 0.6}) rotate(${Math.random() * 360}deg)`;
      p.style.animationDuration = `${Math.random() * 1.5 + 1.2}s`;
      p.style.animationDelay = `${Math.random() * 0.3}s`;
      container.appendChild(p);
    }

    setTimeout(() => {
      if (container && container.parentNode) {
        container.parentNode.removeChild(container);
      }
    }, 2800);
  },

  bindEvents() {
    // Open achievements modal
    document.getElementById("btn-open-achievements")?.addEventListener("click", () => {
      this.renderAchievementsModal();
      if (window.App) App.openModal("modal-achievements");
    });
  },

  escapeHtml(text) {
    if (!text) return "";
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  Gamification.init();
});

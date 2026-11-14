/* ==========================================================================
   mcmusic — iOS-style mobile framework
   The tab bar IS the sidebar (layout.css moves #rail to the bottom), so there
   is exactly one navigation surface. This module owns:
     * device/standalone detection,
     * keyboard anchoring via visualViewport (--kb + body.kb-open),
     * safe-area aware scroll helpers,
     * tab active state.
   ========================================================================== */

export const Mobile = {
  isMobile: false,
  standalone: false,
  keyboardOpen: false,
  mql: null,
  listeners: new Set(),
  _focused: null,
  _raf: 0,

  init() {
    this.mql = window.matchMedia("(max-width: 860px)");
    this._syncMode();
    this.mql.addEventListener("change", () => this._syncMode());

    this.standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true;
    if (this.standalone) document.body.classList.add("standalone");

    this._setupViewport();
    this._setupKeyboard();
    this._setupFocusScroll();
    this._setupPullGuard();

    window.addEventListener("mcmusic:viewchange", (e) => this.updateView(e.detail.view));
  },

  _syncMode() {
    const next = this.mql.matches;
    if (next === this.isMobile) return;
    this.isMobile = next;
    document.body.classList.toggle("is-mobile", next);
    this._emit();
  },

  onChange(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  },

  _emit() {
    for (const fn of this.listeners) {
      try {
        fn({ mobile: this.isMobile, standalone: this.standalone });
      } catch (e) { /* ignore */ }
    }
  },

  /* ── viewport units ─────────────────────────────────────────────────── */
  _setupViewport() {
    const apply = () => {
      const vh = (window.visualViewport?.height || window.innerHeight) * 0.01;
      document.documentElement.style.setProperty("--vh", `${vh}px`);
      document.documentElement.style.setProperty("--vw", `${window.innerWidth * 0.01}px`);
    };
    apply();
    window.addEventListener("resize", apply);
    window.addEventListener("orientationchange", () => setTimeout(apply, 120));
    if (window.visualViewport) window.visualViewport.addEventListener("resize", apply);
  },

  /* ── keyboard anchoring ─────────────────────────────────────────────── */
  _setupKeyboard() {
    const vv = window.visualViewport;
    if (!vv) return;

    const sync = () => {
      cancelAnimationFrame(this._raf);
      this._raf = requestAnimationFrame(() => {
        const inset = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
        const open = inset > 120 && !!this._focused;
        document.documentElement.style.setProperty("--kb", `${Math.round(inset)}px`);
        if (open !== this.keyboardOpen) {
          this.keyboardOpen = open;
          document.body.classList.toggle("kb-open", open);
        }
        if (open) this._anchor(this._focused);
      });
    };

    vv.addEventListener("resize", sync);
    vv.addEventListener("scroll", sync);

    document.addEventListener("focusin", (e) => {
      if (!this.isEditable(e.target)) return;
      this._focused = e.target;
      setTimeout(sync, 60);
    });

    document.addEventListener("focusout", () => {
      this._focused = null;
      setTimeout(() => {
        if (!this._focused) {
          this.keyboardOpen = false;
          document.body.classList.remove("kb-open");
          document.documentElement.style.setProperty("--kb", "0px");
        }
      }, 80);
    });
  },

  isEditable(el) {
    if (!el) return false;
    const tag = el.tagName;
    if (tag === "TEXTAREA" || tag === "SELECT") return true;
    if (tag === "INPUT") {
      return !["button", "submit", "checkbox", "radio", "range", "color", "file"]
        .includes(el.type);
    }
    return el.isContentEditable;
  },

  _anchor(el) {
    if (!el || !el.scrollIntoView) return;
    const kb = parseInt(
      getComputedStyle(document.documentElement).getPropertyValue("--kb") || "0", 10);
    try {
      el.scrollIntoView({ block: "center", behavior: "smooth" });
    } catch (e) { /* ignore */ }
    // Nudge the search field to the very top so results stay visible.
    if (kb && el.closest(".sfield")) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  },

  _setupFocusScroll() {
    document.addEventListener("focusin", (e) => {
      if (!this.isMobile || !this.isEditable(e.target)) return;
      // Let the keyboard settle before scrolling.
      setTimeout(() => {
        try {
          e.target.scrollIntoView({ block: "center", behavior: "smooth" });
        } catch (_) { /* ignore */ }
      }, 260);
    });
  },

  /** Prevent iOS rubber-banding from revealing the page behind the tab bar. */
  _setupPullGuard() {
    let startY = 0;
    document.addEventListener(
      "touchstart",
      (e) => {
        const scroller = e.target.closest("#content, .drawer-b, .sheet-b, .scroll");
        startY = e.touches[0]?.clientY || 0;
        if (!scroller) return;
        this._scroller = scroller;
        this._startTop = scroller.scrollTop;
      },
      { passive: true }
    );
    document.addEventListener(
      "touchmove",
      (e) => {
        if (!this._scroller || !this.isMobile) return;
        const dy = (e.touches[0]?.clientY || 0) - startY;
        const atTop = this._scroller.scrollTop <= 0;
        if (atTop && dy > 0 && !this._scroller.closest(".shelf-track")) {
          // allow native scroll; only block the bounce itself
          if (window.scrollY <= 0) e.preventDefault();
        }
      },
      { passive: false }
    );
  },

  updateView(view) {
    document.querySelectorAll("#railnav .rnav").forEach((btn) => {
      const active = btn.dataset.view === view ||
        (btn.dataset.view === "library" &&
          ["album", "artist", "playlist", "likes", "now"].includes(view)) ||
        (btn.dataset.view === "downloads" && view === "requests");
      btn.classList.toggle("on", active);
      btn.setAttribute("aria-current", active ? "page" : "false");
    });
  },

  blur() {
    const el = document.activeElement;
    if (el && el.blur) el.blur();
  },

  /** True when the layout is a phone-sized viewport. */
  get compact() {
    return this.isMobile;
  },
};

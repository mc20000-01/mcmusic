/* ==========================================================================
   mcmusic — application shell, router and integrations
   · one <audio> element owned by Player
   · one navigation surface (#rail becomes the iOS tab bar on mobile)
   · settings persisted locally (IndexedDB) and to the account
   · offline cache + non-disruptive background updates
   ========================================================================== */

import { api, pendingWrites } from "./api.js";
import * as cache from "./cache.js";
import { icon, repeatIcon, volumeIcon } from "./icons.js";
import { Auth } from "./auth.js";
import { Mobile } from "./mobile.js";
import { Player, deviceHash, deviceName } from "./player.js";
import { Views, hasView, renderSearch } from "./views.js";
import { RealGlass } from "./glass.js";
import { Gfx } from "./gfx.js";
import {
  toast, sheet, closeSheet, empty, art, menu, progressBar, toggleLike,
} from "./ui.js";

const CONFIG = window.__MC__ || {};
const root = document.documentElement;

const DEFAULTS = {
  theme: "dusk",
  accent: "#a06bff",
  density: "comfy",
  material: "glass",
  covers: true,
  autoplay: true,
  hide_explicit: false,
  private: false,
  yt_stats: true,
  remember_volume: true,
  volume: 0.8,
  prefetch: true,
  offline_audio: true,
  real_glass: "auto",
};

const NAV = [
  ["home", "Home", "home"],
  ["search", "Search", "search"],
  ["library", "Library", "library"],
  ["downloads", "Downloads", "download"],
  ["settings", "Settings", "settings"],
];

/* ── colour helpers ─────────────────────────────────────────────────────── */
function hexToRgb(hex) {
  const h = String(hex || "").replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const n = parseInt(full, 16);
  if (!isFinite(n)) return { r: 217, g: 138, b: 61 };
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

function luminance(hex) {
  const { r, g, b } = hexToRgb(hex);
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
}

const $ = (sel, r = document) => r.querySelector(sel);

/* ── brand mark ─────────────────────────────────────────────────────────── */
/* A clean monogram: an open violet C with a lowercase m nested inside it.
   Same geometry as web/icon.svg, the Linux window and the Android launcher. */
const MARK_PATHS = [
  ["M387 167.6 A158 158 0 1 0 387 344.4", 42],
  ["M182 300 V226 a37 37 0 0 1 74 0 v74 M256 300 V226 a37 37 0 0 1 74 0 v74", 36],
];
const SVG_NS = "http://www.w3.org/2000/svg";

/** Inline logo mark at `height` px, tinted with the current text colour. */
function brandMark(height = 22) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "56 56 400 400");
  svg.setAttribute("height", String(height));
  svg.setAttribute("width", String(height));
  svg.setAttribute("class", "mark");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const g = document.createElementNS(SVG_NS, "g");
  g.setAttribute("fill", "none");
  g.setAttribute("stroke", "currentColor");
  g.setAttribute("stroke-linecap", "round");
  g.setAttribute("stroke-linejoin", "round");
  MARK_PATHS.forEach(([d, width]) => {
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", d);
    path.setAttribute("stroke-width", String(width));
    g.appendChild(path);
  });
  svg.appendChild(g);
  return svg;
}

/* ── app ────────────────────────────────────────────────────────────────── */
class App {
  constructor() {
    this.me = null;
    this.set = { ...DEFAULTS };
    this.view = "home";
    this.arg = null;
    this._hashReady = false;
    this.hist = [];
    this.lib = "songs";
    this.dl = "files";
    this.sort = "artist";
    this.q = "";
    this.timer = null;
    this.drawerOpen = false;
    this.devices = [];
    this._remoteState = null;
    this.deviceId = null;
    this.host = null;
    this.room = null;
    this.lst = null;
    this.installEvt = null;
    this.build = CONFIG.build || "dev";
    this.updateReady = false;
    this._swRegistration = null;
    this._reloadingForUpdate = false;
    this._pendingApply = false;
    this._saveTimer = null;
    this._booted = false;
    this._searchTimer = null;
    this._roomTimer = null;
    this._pollTimer = null;
    this._heartbeatTimer = null;
  }

  /* ── boot ─────────────────────────────────────────────────────────────── */
  async init() {
    Mobile.init();

    const stored = (await cache.get(cache.K.settings)) || {};
    Object.assign(this.set, stored);
    RealGlass.init(this.set.real_glass || "auto");
    Gfx.setNotifier((text) => toast(text, { iconName: "gauge" }));
    Gfx.init();
    this._applyTheme();

    Player.device = deviceHash();
    Player.init(document.getElementById("audio"));
    window.Player = Player;
    this._bindPlayer();

    const me = await Auth.init();
    Auth.onChange(({ me: m }) => {
      this.me = m;
      this._paintRailUser();
    });

    // A reset link opens /reset?token=...; the form spends the token.
    const token = new URLSearchParams(location.search).get("token");
    if (location.pathname === "/reset" && token) {
      this._showReset(token);
      return;
    }

    if (!me) {
      this.showLogin();
      return;
    }

    this.me = me;
    await this._bootShell();
  }

  async _bootShell() {
    if (this._booted) return;
    this._booted = true;

    // Server-side preferences win over the local cache.
    try {
      const server = await api("settings");
      Object.assign(this.set, server);
      await cache.set(cache.K.settings, this.set);
      RealGlass.setMode(this.set.real_glass || "auto");
      this._applyTheme();
    } catch (e) { /* offline: keep local */ }

    Player.hideExplicit = !!this.set.hide_explicit;
    Player.private = !!this.set.private;
    if (this.set.remember_volume) Player.setVolume(this.set.volume);
    Player.muted = false;

    this._buildShell();
    await this.refreshSide();
    this.draw();

    this._syncDevices();
    this._startHeartbeat();
    this._startCommandPoll();
    this._registerServiceWorker();
    this._checkForUpdates();
    setInterval(() => this._checkForUpdates(), 15 * 60 * 1000);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) this._checkForUpdates();
    });

    window.addEventListener("online", () => this._net(true));
    window.addEventListener("offline", () => this._net(false));
    this._net(navigator.onLine);

    // Writes made offline are queued by api.js and replayed on reconnect.
    window.addEventListener("mc:queued", () => {
      toast("Saved for now — we’ll sync it when you’re back online", { iconName: "wifi-off" });
    });
    window.addEventListener("mc:synced", (e) => {
      const n = e.detail?.count || 0;
      if (n) toast(`All caught up — synced ${n} change${n === 1 ? "" : "s"}`, { iconName: "check" });
    });
    window.addEventListener("mc:syncfail", () => {
      toast("An offline change was rejected", { iconName: "triangle-alert" });
    });
    ["mc:queued", "mc:synced", "mc:syncfail", "online", "offline"].forEach((name) => {
      window.addEventListener(name, () => this._paintPending());
    });

    this._setupKeyboard();
    this._setupInstall();
    window.addEventListener("hashchange", () => this._maybeJoinRoomFromHash());
    this._maybeJoinRoomFromHash();

    if (Player.queue.length) {
      toast(`Picking up where you left off: ${Player.current()?.title || "your last track"}`, {
        iconName: "disc-3",
        action: { label: "Play", fn: () => Player.toggle() },
        duration: 6000,
      });
    }
  }

  /* ── login ────────────────────────────────────────────────────────────── */
  showLogin() {
    const app = document.getElementById("app");
    app.replaceChildren();

    const wrap = document.createElement("div");
    wrap.className = "login";

    const stage = document.createElement("div");
    stage.className = "login-stage";

    const card = document.createElement("div");
    card.className = "login-card";

    const brand = document.createElement("div");
    brand.className = "login-brand";
    const kick = document.createElement("span");
    kick.className = "kicker";
    kick.textContent = "self-hosted music";
    const row = document.createElement("div");
    row.className = "brand-row";
    const h1 = document.createElement("h1");
    h1.textContent = "mcmusic";
    row.appendChild(brandMark(36));
    row.appendChild(h1);
    brand.appendChild(kick);
    brand.appendChild(row);
    card.appendChild(brand);

    /* The left half showcases the brand. On phones it steps aside so the form stays the whole story. */
    const aside = document.createElement("aside");
    aside.className = "login-aside";

    const aKick = document.createElement("span");
    aKick.className = "kicker";
    aKick.textContent = "your music, your room";
    aside.appendChild(aKick);

    const aBrand = document.createElement("div");
    aBrand.className = "brand-row";
    // Enhanced brand with tagline
    aBrand.appendChild(brandMark(56));
    const aSub = document.createElement("p");
    aSub.className = "brand-tagline";
    aSub.textContent = "Self-hosted. Private. Yours.";
    aBrand.appendChild(aSub);
    const aTitle = document.createElement("h1");
    aTitle.textContent = "mcmusic";
    aBrand.appendChild(aTitle);
    aside.appendChild(aBrand);

    const aLead = document.createElement("p");
    aLead.className = "login-aside-lead";
    aLead.textContent = "Your library, your playlists, your rules — streamed from a server you actually own.";
    aside.appendChild(aLead);

    const feature = (iconName, title, text) => {
      const item = document.createElement("div");
      item.className = "login-feature";
      const badge = document.createElement("span");
      badge.className = "fi";
      badge.appendChild(icon(iconName, { size: 16 }));
      const copy = document.createElement("div");
      const b = document.createElement("b");
      b.textContent = title;
      const span = document.createElement("span");
      span.textContent = text;
      copy.appendChild(b);
      copy.appendChild(span);
      item.appendChild(badge);
      item.appendChild(copy);
      return item;
    };

    const features = document.createElement("div");
    features.className = "login-features";
    features.appendChild(feature("disc-3", "No feed. No algorithm.", "Only the records you put here."));
    features.appendChild(feature("smartphone", "Phone and desktop.", "Pick up on one device where the other stopped."));
    features.appendChild(feature("wifi-off", "Keeps playing offline.", "Downloads and artwork travel with you."));
    aside.appendChild(features);

    const turntable = document.createElement("div");
    turntable.className = "login-now";
    const disc = document.createElement("div");
    disc.className = "login-disc";
    disc.setAttribute("aria-hidden", "true");
    turntable.appendChild(disc);
    const turnMeta = document.createElement("div");
    turnMeta.className = "login-now-meta";
    const turnKick = document.createElement("small");
    turnKick.textContent = "ON THE TURNTABLE";
    const turnTitle = document.createElement("b");
    turnTitle.textContent = "Something you already love";
    turnMeta.appendChild(turnKick);
    turnMeta.appendChild(turnTitle);
    turntable.appendChild(turnMeta);
    const eq = document.createElement("div");
    eq.className = "login-eq";
    eq.setAttribute("aria-hidden", "true");
    for (let i = 0; i < 5; i++) eq.appendChild(document.createElement("i"));
    turntable.appendChild(eq);
    aside.appendChild(turntable);

    const quote = document.createElement("p");
    quote.className = "login-quote";
    quote.textContent = "“No feed. No algorithm. Just your shelf, playing.”";
    aside.appendChild(quote);

    stage.appendChild(aside);
    stage.appendChild(card);

    const welcome = document.createElement("div");
    welcome.className = "login-welcome";
    const welcomeTitle = document.createElement("h2");
    welcomeTitle.textContent = "Welcome back";
    const welcomeCopy = document.createElement("p");
    welcomeCopy.textContent = "Sign in to pick up right where you left off.";
    welcome.appendChild(welcomeTitle);
    welcome.appendChild(welcomeCopy);
    card.appendChild(welcome);

    let mode = "in";

    const tabs = document.createElement("div");
    tabs.className = "seg";
    tabs.style.width = "100%";
    const inBtn = document.createElement("button");
    inBtn.textContent = "Sign in";
    inBtn.className = "on";
    const upBtn = document.createElement("button");
    upBtn.textContent = "Create an account";
    inBtn.onclick = () => setMode("in");
    upBtn.onclick = () => setMode("up");
    inBtn.style.flex = "1";
    upBtn.style.flex = "1";
    tabs.appendChild(inBtn);
    tabs.appendChild(upBtn);

    const user = document.createElement("div");
    user.className = "field";
    const ul = document.createElement("label");
    ul.textContent = "Username";
    const userInput = document.createElement("input");
    userInput.autocomplete = "username";
    userInput.placeholder = "Your username";
    user.appendChild(ul);
    user.appendChild(userInput);

    const pass = document.createElement("div");
    pass.className = "field";
    const pl = document.createElement("label");
    pl.textContent = "Password";
    const passInput = document.createElement("input");
    passInput.type = "password";
    passInput.autocomplete = "current-password";
    passInput.placeholder = "Your password";
    pass.appendChild(pl);
    pass.appendChild(passInput);

    const invite = document.createElement("div");
    invite.className = "field";
    invite.hidden = true;
    const il = document.createElement("label");
    il.textContent = "Invite code";
    const inviteInput = document.createElement("input");
    inviteInput.placeholder = "paste your invite";
    invite.appendChild(il);
    invite.appendChild(inviteInput);

    const submit = document.createElement("button");
    submit.className = "btn solid";
    submit.style.width = "100%";
    submit.textContent = "Sign in";

    const divider = document.createElement("div");
    divider.className = "login-divider";
    divider.textContent = "or";

    const rotur = document.createElement("button");
    rotur.className = "rotur-btn";
    rotur.appendChild(icon("link", { size: 15 }));
    const roturLabel = document.createElement("span");
    roturLabel.textContent = "Continue with Rotur";
    rotur.appendChild(roturLabel);
    rotur.onclick = () => Auth.roturLogin("/");

    const note = document.createElement("p");
    note.className = "login-note";
    note.textContent = Auth.rotur.configured
      ? "You’ll sign in on the official Rotur page. mcmusic never sees your Rotur password."
      : "Rotur sign-in isn’t available on this server right now — you can use your account below instead.";
    const noteText = note.textContent;

    function setMode(next) {
      mode = next;
      inBtn.classList.toggle("on", next === "in");
      upBtn.classList.toggle("on", next === "up");
      submit.textContent = next === "in" ? "Sign in" : "Create account";
      welcomeTitle.textContent = next === "in" ? "Welcome back" : "Create your account";
      welcomeCopy.textContent = next === "in"
        ? "Sign in to pick up right where you left off."
        : "It only takes a moment — you’ll be listening in no time.";
      passInput.autocomplete = next === "in" ? "current-password" : "new-password";
      invite.hidden = !(next === "up" && CONFIG.inviteCode);
    }

    const go = async () => {
      submit.disabled = true;
      try {
        const me = mode === "in"
          ? await Auth.login(userInput.value.trim(), passInput.value)
          : await Auth.register(userInput.value.trim(), passInput.value, inviteInput.value.trim());
        this.me = me;
        await this._bootShell();
      } catch (e) {
        toast(e.message || "Could not sign in", { iconName: "triangle-alert" });
        submit.disabled = false;
      }
    };

    submit.onclick = go;
    passInput.onkeydown = (e) => {
      if (e.key === "Enter") go();
    };

    /* forgot password — same card, swapped for a reset request */
    const forgot = document.createElement("button");
    forgot.type = "button";
    forgot.className = "btn ghost sm";
    forgot.style.width = "100%";
    forgot.textContent = "Forgot password?";

    const resetBox = document.createElement("div");
    resetBox.hidden = true;
    resetBox.className = "field";
    const rlabel = document.createElement("label");
    rlabel.textContent = "Account email";
    const rEmail = document.createElement("input");
    rEmail.type = "email";
    rEmail.autocomplete = "email";
    rEmail.placeholder = "you@example.com";
    const rSend = document.createElement("button");
    rSend.type = "button";
    rSend.className = "btn solid";
    rSend.style.width = "100%";
    rSend.textContent = "Send reset link";
    const rBack = document.createElement("button");
    rBack.type = "button";
    rBack.className = "btn ghost sm";
    rBack.style.width = "100%";
    rBack.textContent = "Back to sign in";
    resetBox.appendChild(rlabel);
    resetBox.appendChild(rEmail);
    resetBox.appendChild(rSend);
    resetBox.appendChild(rBack);

    forgot.onclick = () => {
      tabs.hidden = true;
      user.hidden = true;
      pass.hidden = true;
      invite.hidden = true;
      submit.hidden = true;
      divider.hidden = true;
      rotur.hidden = true;
      forgot.hidden = true;
      resetBox.hidden = false;
      welcomeTitle.textContent = "Reset your password";
      welcomeCopy.textContent = "Enter the email on your account and we’ll send a one-time reset link.";
      note.textContent = "If that address is on file, you’ll get an email in a minute or two.";
      setTimeout(() => rEmail.focus(), 40);
    };

    rBack.onclick = () => {
      tabs.hidden = false;
      user.hidden = false;
      pass.hidden = false;
      submit.hidden = false;
      invite.hidden = !(mode === "up" && CONFIG.inviteCode);
      divider.hidden = !Auth.rotur.configured;
      rotur.hidden = !Auth.rotur.configured;
      forgot.hidden = false;
      resetBox.hidden = true;
      note.textContent = noteText;
      setMode(mode);
    };

    rSend.onclick = async () => {
      rSend.disabled = true;
      try {
        const r = await Auth.requestReset(rEmail.value.trim());
        note.textContent = r.mail === false
          ? "Email isn’t set up on this server yet. Ask an admin to configure SMTP so reset links can be sent."
          : "If that address is on file, check your inbox for a reset link shortly.";
      } catch (e) {
        toast(e.message || "Could not send the reset link", { iconName: "triangle-alert" });
      } finally {
        rSend.disabled = false;
      }
    };

    card.appendChild(tabs);
    card.appendChild(user);
    card.appendChild(pass);
    card.appendChild(invite);
    card.appendChild(submit);
    card.appendChild(forgot);
    card.appendChild(resetBox);
    if (Auth.rotur.configured) {
      card.appendChild(divider);
      card.appendChild(rotur);
    }
    card.appendChild(note);

    wrap.appendChild(stage);
    app.replaceChildren(wrap);
    setTimeout(() => userInput.focus(), 60);
  }

  /** /reset?token=... — spend the one-time link and set a new password. */
  _showReset(token) {
    const app = document.getElementById("app");

    const wrap = document.createElement("div");
    wrap.className = "login";
    const card = document.createElement("div");
    card.className = "login-card";

    const brand = document.createElement("div");
    brand.className = "login-brand";
    const kick = document.createElement("div");
    kick.className = "kicker";
    kick.textContent = "self-hosted music";
    const row = document.createElement("div");
    row.className = "brand-row";
    const h1 = document.createElement("h1");
    h1.textContent = "mcmusic";
    row.appendChild(brandMark(36));
    row.appendChild(h1);
    brand.appendChild(kick);
    brand.appendChild(row);
    card.appendChild(brand);

    const intro = document.createElement("p");
    intro.className = "login-note";
    intro.textContent = "Choose a new password. The link works once.";

    const pw = document.createElement("input");
    pw.type = "password";
    pw.autocomplete = "new-password";
    pw.placeholder = "6+ characters";
    const pw2 = document.createElement("input");
    pw2.type = "password";
    pw2.autocomplete = "new-password";
    pw2.placeholder = "repeat it";

    const field1 = document.createElement("div");
    field1.className = "field";
    const l1 = document.createElement("label");
    l1.textContent = "New password";
    field1.appendChild(l1);
    field1.appendChild(pw);

    const field2 = document.createElement("div");
    field2.className = "field";
    const l2 = document.createElement("label");
    l2.textContent = "Confirm password";
    field2.appendChild(l2);
    field2.appendChild(pw2);

    const submit = document.createElement("button");
    submit.className = "btn solid";
    submit.style.width = "100%";
    submit.textContent = "Set password";

    const note = document.createElement("p");
    note.className = "login-note";
    note.textContent = "Use at least 6 characters.";

    // Ask the server now, so a dead link says so before a password is typed.
    Auth.checkReset(token).catch((e) => {
      note.textContent = e.message || "That link is no longer valid.";
      submit.disabled = true;
    });

    const go = async () => {
      if (pw.value !== pw2.value) {
        note.textContent = "The two passwords don't match.";
        return;
      }
      if (pw.value.length < 6) {
        note.textContent = "Use at least 6 characters.";
        return;
      }
      submit.disabled = true;
      try {
        await Auth.confirmReset(token, pw.value);
        history.replaceState({}, "", "/");
        toast("Password updated — sign in with it", { iconName: "check" });
        this.showLogin();
      } catch (e) {
        note.textContent = e.message || "That link is no longer valid.";
        submit.disabled = false;
      }
    };

    submit.onclick = go;
    pw2.onkeydown = (e) => {
      if (e.key === "Enter") go();
    };

    card.appendChild(intro);
    card.appendChild(field1);
    card.appendChild(field2);
    card.appendChild(submit);
    card.appendChild(note);
    wrap.appendChild(card);
    app.replaceChildren(wrap);
    setTimeout(() => pw.focus(), 60);
  }

  /* ── shell ────────────────────────────────────────────────────────────── */
  _buildShell() {
    const app = document.getElementById("app");
    app.replaceChildren();

    /* rail */
    const rail = document.createElement("aside");
    rail.id = "rail";

    const brand = document.createElement("div");
    brand.id = "brand";
    brand.appendChild(brandMark(24));
    const brandName = document.createElement("span");
    brandName.textContent = "mcmusic";
    brand.appendChild(brandName);
    rail.appendChild(brand);

    const nav = document.createElement("nav");
    nav.id = "railnav";
    nav.setAttribute("aria-label", "Primary");
    NAV.forEach(([view, label, iconName]) => {
      nav.appendChild(this._navItem(view, label, iconName));
    });
    if (this.me?.is_admin) {
      nav.appendChild(this._navItem("admin", "Admin", "users"));
    }
    rail.appendChild(nav);

    const sep = document.createElement("div");
    sep.className = "rsep";
    rail.appendChild(sep);

    const plLabel = document.createElement("div");
    plLabel.className = "rail-label";
    plLabel.textContent = "Playlists";
    rail.appendChild(plLabel);

    const pls = document.createElement("div");
    pls.id = "railplaylists";
    rail.appendChild(pls);

    const foot = document.createElement("div");
    foot.id = "railfoot";
    rail.appendChild(foot);

    /* main */
    const main = document.createElement("div");
    main.id = "main";

    const top = document.createElement("header");
    top.id = "top";

    const back = document.createElement("button");
    back.id = "back";
    back.className = "iconbtn";
    back.setAttribute("aria-label", "Back");
    back.hidden = true;
    back.appendChild(icon("chevron-left", { size: 18 }));
    back.onclick = () => this.back();

    const field = document.createElement("label");
    field.className = "sfield";
    field.appendChild(icon("search", { size: 15 }));
    const q = document.createElement("input");
    q.id = "q";
    q.type = "search";
    q.placeholder = "Search for songs, albums, or artists   ( / )";
    q.autocomplete = "off";
    q.enterKeyHint = "search";
    q.oninput = (e) => this.onSearch(e.target.value);
    q.onkeydown = (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        q.blur();
        Mobile.blur();
      }
    };
    field.appendChild(q);

    const actions = document.createElement("div");
    actions.id = "topactions";

    // Offline writes waiting to replay are visible from every view; the row in
    // Settings is where they are sent.
    const pendingChip = document.createElement("button");
    pendingChip.id = "pending";
    pendingChip.type = "button";
    pendingChip.hidden = true;
    pendingChip.onclick = () => this.go("settings");
    pendingChip.appendChild(icon("refresh-cw", { size: 12 }));
    const pendingCount = document.createElement("span");
    pendingCount.id = "pending-count";
    pendingChip.appendChild(pendingCount);
    actions.appendChild(pendingChip);

    const nowBtn = document.createElement("button");
    nowBtn.className = "iconbtn";
    nowBtn.setAttribute("aria-label", "Open player");
    nowBtn.appendChild(icon("tv-2", { size: 17 }));
    nowBtn.onclick = () => this.go("now");
    actions.appendChild(nowBtn);

    const install = document.createElement("button");
    install.className = "iconbtn";
    install.id = "install";
    install.setAttribute("aria-label", "Install app");
    install.hidden = true;
    install.appendChild(icon("cloud-download", { size: 17 }));
    install.onclick = () => this._install();
    actions.appendChild(install);

    const logout = document.createElement("button");
    logout.className = "iconbtn";
    logout.id = "logout";
    logout.setAttribute("aria-label", "Sign out");
    logout.textContent = "Logout";
    logout.onclick = () => this.logout();
    actions.appendChild(logout);

    top.appendChild(back);
    top.appendChild(field);
    top.appendChild(actions);

    const content = document.createElement("div");
    content.id = "content";
    content.setAttribute("role", "main");
    let scrollFade = 0;
    content.addEventListener("scroll", () => {
      Gfx.activity();
      content.classList.add("is-scrolling");
      clearTimeout(scrollFade);
      scrollFade = setTimeout(() => content.classList.remove("is-scrolling"), 700);
    }, { passive: true });

    main.appendChild(top);
    main.appendChild(content);

    /* deck */
    const deck = document.createElement("footer");
    deck.id = "deck";

    const now = document.createElement("div");
    now.className = "deck-now";
    const nowArt = document.createElement("button");
    nowArt.className = "art art-sm";
    nowArt.id = "deck-art";
    nowArt.setAttribute("aria-label", "Open player");
    nowArt.onclick = () => this.go("now");
    const meta = document.createElement("div");
    meta.className = "deck-meta";
    const title = document.createElement("b");
    title.id = "deck-title";
    title.textContent = "Nothing playing right now";
    const sub = document.createElement("small");
    sub.id = "deck-sub";
    sub.textContent = "Pick a song to get started";
    meta.appendChild(title);
    meta.appendChild(sub);
    const likeBtn = document.createElement("button");
    likeBtn.className = "iconbtn";
    likeBtn.id = "deck-like";
    likeBtn.setAttribute("aria-label", "Like");
    likeBtn.appendChild(icon("heart", { size: 18 }));
    likeBtn.onclick = () => {
      const t = Player.current();
      if (t) toggleLike(t);
    };
    now.appendChild(nowArt);
    now.appendChild(meta);
    now.appendChild(likeBtn);

    const center = document.createElement("div");
    center.className = "deck-center";
    const controls = document.createElement("div");
    controls.className = "deck-controls";

    const shuffle = document.createElement("button");
    shuffle.className = "iconbtn";
    shuffle.id = "btn-shuffle";
    shuffle.setAttribute("aria-label", "Shuffle");
    shuffle.appendChild(icon("shuffle", { size: 18 }));
    shuffle.onclick = () => this.toggleShuffle();

    const prev = document.createElement("button");
    prev.className = "iconbtn";
    prev.setAttribute("aria-label", "Previous");
    prev.appendChild(icon("skip-back", { size: 18 }));
    prev.onclick = () => Player.prev();

    const play = document.createElement("button");
    play.className = "iconbtn play";
    play.id = "btn-play";
    play.setAttribute("aria-label", "Play or pause");
    play.appendChild(icon("play", { size: 18, filled: true }));
    play.onclick = () => Player.toggle();

    const next = document.createElement("button");
    next.className = "iconbtn";
    next.setAttribute("aria-label", "Next");
    next.appendChild(icon("skip-forward", { size: 18 }));
    next.onclick = () => Player.next();

    const repeat = document.createElement("button");
    repeat.className = "iconbtn";
    repeat.id = "btn-repeat";
    repeat.setAttribute("aria-label", "Repeat");
    repeat.appendChild(repeatIcon("off"));
    repeat.onclick = () => this.cycleRepeat();

    controls.appendChild(shuffle);
    controls.appendChild(prev);
    controls.appendChild(play);
    controls.appendChild(next);
    controls.appendChild(repeat);

    const deckBar = progressBar();
    deckBar.id = "deck-progress";

    center.appendChild(controls);
    center.appendChild(deckBar);

    /* right */
    const right = document.createElement("div");
    right.className = "deck-right";

    const devices = document.createElement("button");
    devices.className = "iconbtn hide-m deck-secondary dim";
    devices.id = "btn-devices";
    devices.setAttribute("aria-label", "Devices");
    devices.appendChild(icon("cast", { size: 18 }));
    devices.onclick = (e) => this.deviceMenu(e.currentTarget);

    const queueBtn = document.createElement("button");
    queueBtn.className = "iconbtn";
    queueBtn.id = "btn-queue";
    queueBtn.setAttribute("aria-label", "Queue");
    queueBtn.appendChild(icon("list-music", { size: 18 }));
    queueBtn.onclick = () => this.toggleDrawer();

    const volIcon = document.createElement("button");
    volIcon.className = "iconbtn hide-m deck-volume-icon";
    volIcon.setAttribute("aria-label", "Mute");
    volIcon.appendChild(volumeIcon(false, this.set.volume));
    volIcon.onclick = () => Player.toggleMute();

    const vol = document.createElement("input");
    vol.type = "range";
    vol.id = "vol";
    vol.className = "deck-volume";
    vol.min = "0";
    vol.max = "100";
    vol.value = String(Math.round(this.set.volume * 100));
    vol.style.setProperty("--p", `${vol.value}%`);
    vol.setAttribute("aria-label", "Volume");
    vol.oninput = (e) => {
      const v = Number(e.target.value) / 100;
      e.target.style.setProperty("--p", `${e.target.value}%`);
      Player.setVolume(v);
      volIcon.replaceChildren(volumeIcon(Player.muted, v));
      if (this.set.remember_volume) this.setPref("volume", v);
    };
    volIcon.addEventListener("click", () => {
      setTimeout(() => volIcon.replaceChildren(volumeIcon(Player.muted, Player.volume)), 0);
    });

    const lyricsBtn = document.createElement("button");
    lyricsBtn.className = "iconbtn hide-m deck-secondary";
    lyricsBtn.id = "btn-lyrics";
    lyricsBtn.textContent = "Aa";
    lyricsBtn.setAttribute("aria-label", "Lyrics");
    lyricsBtn.onclick = () => this.openLyrics();

    const videoBtn = document.createElement("button");
    videoBtn.className = "iconbtn hide-m deck-secondary";
    videoBtn.id = "btn-video";
    videoBtn.textContent = "YT";
    videoBtn.setAttribute("aria-label", "Video");
    videoBtn.onclick = () => this.openVideo();

    const moreBtn = document.createElement("button");
    moreBtn.className = "iconbtn deck-more";
    moreBtn.id = "btn-deck-more";
    moreBtn.setAttribute("aria-label", "More player actions");
    moreBtn.appendChild(icon("more-horizontal", { size: 18 }));
    moreBtn.onclick = () => menu(moreBtn, [
      { label: "Queue", iconName: "list-music", fn: () => this.toggleDrawer(true) },
      { label: "Devices", iconName: "cast", fn: () => this.deviceMenu(moreBtn) },
      { label: "Lyrics", iconName: "text", fn: () => this.openLyrics() },
      { label: "Video", iconName: "tv-2", fn: () => this.openVideo() },
      "-",
      {
        label: Player.muted ? "Unmute" : "Mute",
        iconName: "volume-x",
        fn: () => Player.toggleMute(),
      },
    ]);

    right.appendChild(queueBtn);
    right.appendChild(volIcon);
    right.appendChild(vol);
    right.appendChild(lyricsBtn);
    right.appendChild(devices);
    right.appendChild(videoBtn);
    right.appendChild(moreBtn);

    deck.appendChild(now);
    deck.appendChild(center);
    deck.appendChild(right);

    /* drawer */
    const drawer = document.createElement("aside");
    drawer.id = "drawer";
    drawer.setAttribute("aria-label", "Queue");
    const dh = document.createElement("div");
    dh.className = "drawer-h";
    const dTitle = document.createElement("h2");
    dTitle.textContent = "Queue";
    const sleep = document.createElement("select");
    sleep.style.width = "auto";
    [["0", "Sleep"], ["15", "15m"], ["30", "30m"], ["60", "1h"]].forEach(([v, label]) => {
      const o = document.createElement("option");
      o.value = v;
      o.textContent = label;
      sleep.appendChild(o);
    });
    sleep.onchange = (e) => {
      this.setSleep(Number(e.target.value));
      e.target.value = "0";
    };
    const clear = document.createElement("button");
    clear.className = "btn ghost sm";
    clear.textContent = "Clear";
    clear.onclick = () => {
      Player.queue.length = Player.qi + 1;
      this.paintQueue();
      toast("Queue cleared", { iconName: "check" });
    };
    const close = document.createElement("button");
    close.className = "iconbtn";
    close.setAttribute("aria-label", "Close queue");
    close.appendChild(icon("x", { size: 16 }));
    close.onclick = () => this.toggleDrawer(false);
    dh.appendChild(dTitle);
    dh.appendChild(sleep);
    dh.appendChild(clear);
    dh.appendChild(close);

    const db = document.createElement("div");
    db.className = "drawer-b";
    db.id = "drawer-body";

    drawer.appendChild(dh);
    drawer.appendChild(db);

    const scrim = document.createElement("div");
    scrim.className = "scrim";
    scrim.id = "drawer-scrim";
    scrim.onclick = () => this.toggleDrawer(false);

    app.appendChild(rail);
    app.appendChild(main);
    app.appendChild(deck);

    /* Remote playback is now shown inside the deck, not as a separate bar.
       _paintDeck will display remote status when another device is active. */
    /* remote bar removed - controls routed through deck */

    const modal = document.createElement("div");
    modal.id = "media-modal";
    modal.hidden = true;
    const modalHead = document.createElement("div");
    modalHead.className = "modal-head";
    const modalTitle = document.createElement("b");
    modalTitle.id = "media-title";
    const modalClose = document.createElement("button");
    modalClose.className = "iconbtn";
    modalClose.textContent = "×";
    modalClose.setAttribute("aria-label", "Close");
    modalClose.onclick = () => { modal.hidden = true; modal.querySelector("#media-body").replaceChildren(); };
    modalHead.append(modalTitle, modalClose);
    const modalBody = document.createElement("div");
    modalBody.id = "media-body";
    modal.append(modalHead, modalBody);
    document.body.appendChild(modal);
    app.appendChild(drawer);
    app.appendChild(scrim);

    this._paintRailUser();
    this._paintDeck();
    this._paintPending();
  }

  _navItem(view, label, iconName) {
    const btn = document.createElement("button");
    btn.className = `rnav${this.view === view ? " on" : ""}`;
    btn.dataset.view = view;
    btn.type = "button";
    // The label text is hidden in the compact landscape tab bar, so the button
    // needs its own accessible name.
    btn.setAttribute("aria-label", label);
    btn.setAttribute("title", label);
    btn.appendChild(icon(iconName, { size: 16 }));
    const span = document.createElement("span");
    span.textContent = label;
    btn.appendChild(span);
    btn.onclick = () => this.navTo(view);
    return btn;
  }

  _paintRailUser() {
    const foot = document.getElementById("railfoot");
    if (!foot || !this.me) return;

    foot.replaceChildren();

    const user = document.createElement("div");
    user.className = "rail-user";
    const av = document.createElement("span");
    av.className = "avatar";
    av.textContent = (this.me.username || "?").charAt(0);
    const b = document.createElement("b");
    b.textContent = this.me.username || "";
    user.appendChild(av);
    user.appendChild(b);

    const net = document.createElement("div");
    net.className = "rail-net";
    net.id = "rail-net";
    const dot = document.createElement("span");
    dot.className = "dot";
    const label = document.createElement("span");
    label.textContent = navigator.onLine ? "online" : "offline";
    net.appendChild(dot);
    net.appendChild(label);

    const actions = document.createElement("div");
    actions.style.cssText = "display:flex;gap:2px;margin-left:auto";
    const out = document.createElement("button");
    out.className = "iconbtn";
    out.setAttribute("aria-label", "Log out");
    out.appendChild(icon("log-out", { size: 15 }));
    out.onclick = () => this.logout();
    actions.appendChild(out);
    user.appendChild(actions);

    foot.appendChild(user);
    foot.appendChild(net);
    this._net(navigator.onLine);
  }

  _net(online) {
    const net = document.getElementById("rail-net");
    if (!net) return;
    net.classList.toggle("offline", !online);
    net.lastChild.textContent = online ? "online" : "offline";
  }

  /* Keep the queued-write count current wherever the user is. */
  async _paintPending() {
    const chip = document.getElementById("pending");
    const count = document.getElementById("pending-count");
    if (!chip || !count) return;
    const n = await pendingWrites().catch(() => 0);
    chip.hidden = n === 0;
    count.textContent = String(n);
    const label = `${n} change${n === 1 ? "" : "s"} waiting to sync`;
    chip.setAttribute("aria-label", label);
    chip.title = label;
  }

  /* ── router ───────────────────────────────────────────────────────────── */
  navTo(view) {
    this.hist = [];
    this.q = "";
    const q = document.getElementById("q");
    if (q) q.value = "";
    this.view = view;
    this.arg = null;
    this.draw();
  }

  go(view, arg = null) {
    if (!hasView(view)) return;
    this.hist.push([this.view, this.arg]);
    this.view = view;
    this.arg = arg;
    this.draw();
  }

  back() {
    const prev = this.hist.pop();
    if (!prev) return;
    [this.view, this.arg] = prev;
    this.draw();
  }

  draw() {
    Gfx.activity();
    // Resolve when the view has either painted or has taken too long; a slow
    // network must not hold the old View Transition snapshot on screen.
    const render = () => new Promise((resolve) => {
      let settled = false;
      const finish = () => {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        resolve();
      };
      const timeout = setTimeout(finish, 650);
      this._drawInner(finish);
    });
    return Gfx.transition(render);
  }

  _drawInner(finish) {
    clearInterval(this.timer);
    this.timer = null;

    const host = document.getElementById("content");
    if (!host) {
      finish();
      return;
    }

    // Each draw gets its own content node. A slow view from an earlier draw
    // (home, waiting on /api/home) then paints into a node nobody can see
    // instead of stacking underneath the view the user asked for.
    const gen = (this._drawGen = (this._drawGen || 0) + 1);
    const content = host.cloneNode(false);
    host.replaceWith(content);
    content.scrollTop = 0;
    // retrigger the page-enter animation even when two views look alike
    content.classList.remove("swap");
    void content.offsetWidth;
    content.classList.add("swap");
    const main = document.getElementById("main");
    if (main) main.scrollTop = 0;

    const back = document.getElementById("back");
    if (back) back.hidden = !this.hist.length;

    Mobile.updateView(this.view);
    document.querySelectorAll("#railnav .rnav").forEach((b) => {
      const active = b.dataset.view === this.view ||
        (b.dataset.view === "library" &&
          ["album", "artist", "playlist", "likes", "now"].includes(this.view)) ||
        (b.dataset.view === "downloads" && this.view === "requests");
      b.classList.toggle("on", active);
      b.setAttribute("aria-current", active ? "page" : "false");
    });

    window.dispatchEvent(new CustomEvent("mcmusic:viewchange", { detail: { view: this.view } }));
    if (this._hashReady) this._syncHash();

    const view = hasView(this.view) ? Views[this.view] : null;

    Promise.resolve().then(async () => {
      if (gen !== this._drawGen) return;
      // Clear again: a synchronous draw may have run between the clear above
      // and this builder, and its view would otherwise stay on screen.
      content.replaceChildren();
      if (this.room && !this.lst) {
        content.appendChild(this._roomNotice());
      }
      if (this.lst) {
        content.appendChild(this._listenNotice());
      }
      if (!view) {
        content.appendChild(empty("Not found", "That view does not exist.", { iconName: "circle-help" }));
        return;
      }
      try {
        await view.call(Views, content, this.arg);
      } catch (e) {
        if (gen !== this._drawGen) return;
        console.warn(`view ${this.view} failed`, e);
        content.appendChild(
          empty("Something went wrong", e.message || String(e), {
            iconName: "triangle-alert",
            action: { label: "Reload", fn: () => location.reload() },
          })
        );
      }
    }).catch((e) => {
      console.warn("view draw failed", e);
    }).finally(finish);
  }

  async refreshSide() {
    const host = document.getElementById("railplaylists");
    if (!host) return;
    try {
      const pls = (await api("playlists")).playlists || [];
      host.replaceChildren();
      if (!pls.length) {
        const none = document.createElement("div");
        none.className = "rail-label";
        none.style.paddingTop = "2px";
        none.textContent = "none yet";
        host.appendChild(none);
        return;
      }
      pls.forEach((p) => {
        const btn = document.createElement("button");
        btn.className = "rpl";
        btn.textContent = p.name;
        btn.title = `${p.n || 0} tracks`;
        btn.onclick = () => {
          this.hist = [];
          this.go("playlist", p.id);
        };
        host.appendChild(btn);
      });
    } catch (e) { /* offline or signed out */ }
  }

  onSearch(value) {
    clearTimeout(this._searchTimer);
    this._searchTimer = setTimeout(() => {
      this.q = value.trim();
      if (this.view !== "search") {
        this.view = "search";
        this.arg = null;
        this.draw();
      } else {
        renderSearch(document.getElementById("sres"), this.q);
      }
    }, 220);
  }

  /* ── preferences ──────────────────────────────────────────────────────── */
  async setPref(key, value) {
    this.set[key] = value;
    if (key === "show_room_url" || key === "rotur_activity") {
      // Re-publish the current track so the activity reflects the toggle at once.
      const playing = !!this.set.rotur_activity && !Player.el?.paused;
      this._pushRoturActivity(Player.current(), playing, true);
    }
    this._applyTheme();
    if (key === "real_glass") RealGlass.setMode(this.set.real_glass || "auto");

    Player.hideExplicit = !!this.set.hide_explicit;
    Player.private = !!this.set.private;

    cache.set(cache.K.settings, this.set).catch(() => {});
    try {
      localStorage.setItem("mc_set", JSON.stringify(this.set));
    } catch (e) { /* ignore */ }

    clearTimeout(this._saveTimer);
    this._saveTimer = setTimeout(() => {
      api("settings", "PUT", this.set).catch(() => {});
    }, 600);

    return true;
  }

  _applyTheme() {
    const s = this.set;
    const resolved = s.theme === "auto"
      ? (matchMedia("(prefers-color-scheme: light)").matches ? "paper" : "dusk")
      : s.theme;

    root.dataset.theme = resolved;
    root.dataset.material = s.material || "glass";
    root.style.setProperty("--accent", s.accent);
    root.style.setProperty("--accent-fg", luminance(s.accent) > 0.6 ? "#0b0616" : "#f2ecff");
    const { r, g, b } = hexToRgb(s.accent);
    root.style.setProperty("--accent-soft", `rgba(${r}, ${g}, ${b}, 0.14)`);

    document.body.dataset.density = s.density === "compact" ? "compact" : "comfy";
    document.body.dataset.covers = s.covers ? "on" : "off";
    if (!s.covers) {
      document.querySelectorAll('img[src*="/cover"]').forEach((img) => img.removeAttribute("src"));
    }

    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      const bg = getComputedStyle(root).getPropertyValue("--bg").trim() || "#08060d";
      meta.setAttribute("content", bg);
    }
  }

  toggleShuffle() {
    const on = Player.toggleShuffle();
    this._paintControls();
    toast(on ? "Shuffle on" : "Shuffle off", { iconName: "shuffle" });
  }

  cycleRepeat() {
    const state = Player.cycleRepeat();
    this._paintControls();
    toast(`Repeat: ${state}`, { iconName: state === "one" ? "repeat-1" : "repeat" });
  }

  setSleep(minutes) {
    clearTimeout(this._sleep);
    if (!minutes) {
      toast("Sleep timer off");
      return;
    }
    this._sleep = setTimeout(() => {
      Player.pause();
      toast("Sleep timer reached — playback paused", { iconName: "clock" });
    }, minutes * 60000);
    toast(`Sleep timer: ${minutes} min`, { iconName: "clock" });
  }

  async logout() {
    Player.pause();
    await Auth.logout();
    await Player.clearState();
    this.me = null;
    this.hist = [];
    this.view = "home";
    this._booted = false;
    clearInterval(this._pollTimer);
    clearInterval(this._heartbeatTimer);
    this.showLogin();
  }

  /* ── player bindings ──────────────────────────────────────────────────── */
  _bindPlayer() {
    window.addEventListener("mcmusic:playback", (e) => {
      this._paintDeck(e.detail);
      this._paintControls();
      if (this.drawerOpen) this.paintQueue();
      if (e.detail?.kind === "error") {
        toast("Playback failed — the file may be missing", { iconName: "triangle-alert" });
      }
      if (e.detail?.kind === "blocked") {
        toast("Tap play to start audio", { iconName: "play" });
      }
      if (e.detail?.kind === "info" && e.detail.detail?.message) {
        toast(e.detail.detail.message, { iconName: "radio" });
      }
      if (this._pendingApply && !Player.playing) this.applyUpdate();
      const kind = e.detail?.kind;
      if (["track", "playing", "paused", "seek", "restored"].includes(kind)) {
        this._pushRoturActivity(e.detail?.track || Player.current(), !Player.el?.paused);
      }
    });

    window.addEventListener("mcmusic:like", (e) => {
      const t = e.detail?.track;
      const cur = Player.current();
      if (t && cur && t.id === cur.id) this._paintDeck();
    });
  }

  _paintDeck() {
    const local = Player.current();
    const remote = this._remoteState && this._remoteState.device && this._remoteState.device !== deviceHash() && this._remoteState.track
      ? this._remoteState : null;
    // Mirror selected/active remote device state in the UI while local audio
    // remains on this device (or routes through the selected player device).
    const t = remote?.track || local;
    const title = document.getElementById("deck-title");
    const sub = document.getElementById("deck-sub");
    const holder = document.getElementById("deck-art");
    const like = document.getElementById("deck-like");
    if (!title || !holder || !sub) return;

    if (!t) {
      title.textContent = "Nothing playing right now";
      sub.textContent = "Pick a song to get started";
      holder.replaceChildren(icon("disc-3", { size: 16 }));
      like?.classList.remove("liked");
      like?.removeAttribute("data-like");
      document.title = "mcmusic";
      document.documentElement.style.removeProperty("--hero");
      document.documentElement.style.removeProperty("--tint");
      return;
    }

    title.textContent = t.title || "Unknown";
    sub.replaceChildren();
    const names = Array.isArray(t.artists) && t.artists.length ? t.artists : (t.artist ? [t.artist] : []);
    if (remote) {
      const dev = remote.device_name || "selected device";
      const status = `${remote.playing ? "Playing" : "Paused"} on ${dev} · audio on selected device`;
      sub.appendChild(document.createTextNode(status));
      const detail = [names.join(", "), t.album].filter(Boolean).join(" · ");
      if (detail) sub.appendChild(document.createTextNode(` — ${detail}`));
    } else {
      names.forEach((name, i) => {
        if (i) sub.appendChild(document.createTextNode(" · "));
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "artistchip";
        chip.textContent = name;
        chip.onclick = (e) => {
          e.stopPropagation();
          this.go("artist", name);
        };
        sub.appendChild(chip);
      });
      if (t.album) sub.appendChild(document.createTextNode(`${names.length ? " · " : ""}${t.album}`));
      if (!names.length && !t.album) sub.textContent = "—";
    }

    holder.replaceChildren();
    const img = document.createElement("img");
    if (document.body.dataset.covers !== "off") img.src = `/api/tracks/${t.id}/cover`;
    img.alt = "";
    img.decoding = "async";
    img.onerror = () => {
      img.remove();
      holder.appendChild(icon("disc-3", { size: 16 }));
    };
    if (typeof ambientTint === "function") {
      img.onload = () => ambientTint(img);
      if (img.complete) ambientTint(img);
    }
    holder.appendChild(img);

    if (like) {
      if (typeof t.liked === "boolean") {
        like.classList.toggle("liked", !!t.liked);
        like.replaceChildren(icon("heart", { size: 15, filled: !!t.liked }));
      }
      if (t.id != null) like.dataset.like = String(t.id);
    }
    const artistText = names.join(", ") || t.artist || "mcmusic";
    document.title = `${t.title} · ${artistText}`;
  }

  /** Push the current track as a Rotur rich activity, or clear it on pause. */
  _pushRoturActivity(t, playing, force = false) {
    if (!this.set?.rotur_activity && !force) return;
    const body = t && playing
      ? {
          track_id: t.id,
          position: Math.max(0, Number(Player.el?.currentTime) || 0),
          playing: true,
          presence: "online",
        }
      : { playing: false };
    api("auth/rotur/activity", "POST", body).catch((e) => {
      // Do not fail silently: the settings toggle is useless if the account
      // is not linked or the server cannot open the Rotur socket.
      toast(`Rotur activity: ${e?.message || "could not publish"}`, {
        iconName: "triangle-alert",
      });
    });
  }

  _paintControls() {
    const play = document.getElementById("btn-play");
    if (play) {
      play.replaceChildren(icon(Player.playing ? "pause" : "play", { size: 17, filled: true }));
    }
    const shuffle = document.getElementById("btn-shuffle");
    if (shuffle) shuffle.classList.toggle("on", Player.shuffle);

    const repeat = document.getElementById("btn-repeat");
    if (repeat) {
      repeat.replaceChildren(repeatIcon(Player.repeat));
      repeat.classList.toggle("on", Player.repeat !== "off");
      repeat.classList.toggle("dim", Player.repeat === "off");
    }

    const vol = document.getElementById("vol");
    if (vol && document.activeElement !== vol) {
      const v = Math.round((Player.muted ? 0 : Player.volume) * 100);
      vol.value = String(v);
      vol.style.setProperty("--p", `${v}%`);
    }
  }

  /* ── queue drawer ─────────────────────────────────────────────────────── */
  toggleDrawer(force) {
    const drawer = document.getElementById("drawer");
    const scrim = document.getElementById("drawer-scrim");
    const open = typeof force === "boolean" ? force : !this.drawerOpen;
    this.drawerOpen = open;
    drawer?.classList.toggle("open", open);
    scrim?.classList.toggle("on", open);
    document.getElementById("btn-queue")?.classList.toggle("on", open);
    if (open) this.paintQueue();
  }

  paintQueue() {
    const body = document.getElementById("drawer-body");
    if (!body) return;
    body.replaceChildren();

    const t = Player.current();
    if (!t) {
      body.appendChild(empty("Queue is empty", "Play something to fill it.", { iconName: "list-music" }));
      return;
    }

    const label = document.createElement("div");
    label.className = "drawer-label";
    label.textContent = "Now playing";
    body.appendChild(label);

    const current = document.createElement("button");
    current.className = "qrow now";
    current.appendChild(art(t.id, "art-xs"));
    const meta = document.createElement("div");
    meta.className = "meta";
    const b = document.createElement("b");
    b.textContent = t.title;
    const s = document.createElement("small");      s.replaceChildren();
      (Array.isArray(t.artists) && t.artists.length ? t.artists : (t.artist ? [t.artist] : [])).forEach((name, i) => {
        if (i) s.appendChild(document.createTextNode(" · "));
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "artistchip";
        chip.textContent = name;
        chip.onclick = (e) => {
          e.stopPropagation();
          window.App?.go("artist", name);
        };
        s.appendChild(chip);
      });
    meta.appendChild(b);
    meta.appendChild(s);
    current.appendChild(meta);
    current.onclick = () => Player.seekTo(0);
    body.appendChild(current);

    const up = Player.upNext(60);
    if (up.length) {
      const h = document.createElement("div");
      h.className = "drawer-label";
      h.textContent = `Up next · ${up.length}`;
      body.appendChild(h);
    }

    up.forEach((track, i) => {
      const row = document.createElement("div");
      row.className = "qrow";
      row.appendChild(art(track.id, "art-xs"));

      const m = document.createElement("div");
      m.className = "meta";
      const tb = document.createElement("b");
      tb.textContent = track.title;
      const ts = document.createElement("small");
      ts.textContent = track.artist || "";
      m.appendChild(tb);
      m.appendChild(ts);

      const go = document.createElement("button");
      go.style.cssText = "display:flex;align-items:center;gap:10px;flex:1;min-width:0;text-align:left";
      go.appendChild(m);
      go.onclick = () => {
        Player.qi = Player.qi + 1 + i;
        Player.load(track);
      };

      const rm = document.createElement("button");
      rm.className = "iconbtn";
      rm.setAttribute("aria-label", "Remove from queue");
      rm.appendChild(icon("x", { size: 14 }));
      rm.onclick = () => {
        Player.removeAt(Player.qi + 1 + i);
        this.paintQueue();
      };

      row.appendChild(go);
      row.appendChild(rm);
      body.appendChild(row);
    });
  }

  /* ── remote commands ──────────────────────────────────────────────────── */
  _startCommandPoll() {
    clearInterval(this._pollTimer);
    const tick = async () => {
      if (!Auth.signedIn || document.hidden) return;
      try {
        const r = await api(`playback?device=${encodeURIComponent(deviceHash())}`);
        this._remoteState = r.state && r.state.device && r.state.device !== deviceHash()
          && r.state.track ? r.state : null;
        this._paintRemote();
        const cmds = r.commands || [];
        for (const cmd of cmds) {
          if (cmd.action === "enqueue" && cmd.arg?.track) {
            Player.add(cmd.arg.track);
            toast(`Queued from chat: ${cmd.arg.track.title}`, { iconName: "list-music" });
          } else if (cmd.action === "seek") {
            Player.seekTo(Number(cmd.arg?.position) || 0);
          } else if (cmd.action === "play_track" && cmd.arg?.track) {
            Player.queue = [cmd.arg.track];
            Player.qi = 0;
            Player.load(cmd.arg.track);
            toast(`Playing from ${cmd.arg.from || "another device"}`, { iconName: "cast" });
          } else if (!Player.applyCommand(cmd)) {
            /* unsupported command: ignore */
          } else if (cmd.action === "skip" || cmd.action === "toggle") {
            toast("Playback changed from chat", { iconName: "cast" });
          }
        }
      } catch (e) { /* offline */ }
    };
    tick();
    this._pollTimer = setInterval(tick, 2000);
  }

  /* ── devices ──────────────────────────────────────────────────────────── */
  _startHeartbeat() {
    clearInterval(this._heartbeatTimer);
    const beat = () => {
      const t = Player.current();
      api("devices/heartbeat", "POST", {
        device_hash: deviceHash(),
        name: deviceName(),
        track_id: t ? t.id : null,
        position: Math.round((Player.el?.currentTime || 0) * 10) / 10,
        paused: Player.el?.paused ? 1 : 0,
      }).then(() => this._syncDevices()).catch(() => {});
    };
    beat();
    this._heartbeatTimer = setInterval(beat, 15000);
    this._syncDevices();
    clearInterval(this._devicesTimer);
    this._devicesTimer = setInterval(() => this._syncDevices(), 15000);
  }

  async _syncDevices() {
    try {
      const r = await api("devices");
      this.devices = r.devices || [];
      const me = this.devices.find((d) => d.device_hash === deviceHash());
      const btn = document.getElementById("btn-devices");
      if (btn) {
        btn.classList.toggle("on", !!me?.is_active);
        btn.classList.toggle("dim", !me?.is_active);
      }
    } catch (e) { /* ignore */ }
  }

  async deviceMenu(anchor) {
    await this._syncDevices();
    if (!this.devices.length) {
      toast("No other devices", { iconName: "cast" });
      return;
    }
    const me = this.devices.find((d) => d.device_hash === deviceHash());
    const items = [{
      label: me?.is_active ? "This device is the player" : "Play on this device",
      iconName: me?.is_active ? "check" : "play",
      fn: () => this._takeOver(),
    }, "-"];
    this.devices.forEach((d) => {
      const mine = d.device_hash === deviceHash();
      const name = d.name || "device";
      items.push({
        label: `${mine ? "This device" : name}${d.is_active ? " · playing" : ""}`,
        iconName: d.is_active ? "check" : (mine ? "smartphone" : "tv-2"),
        fn: async () => {
          try {
            await api(`devices/${d.id}/activate`, "POST");
            toast(`Active device: ${name}`, { iconName: "check" });
            this._syncDevices();
          } catch (e) {
            toast(e.message);
          }
        },
      });
      if (!mine) {
        items.push({ label: `Pause on ${name}`, iconName: "pause", fn: () => this._remote(d, "pause") });
        items.push({ label: `Play on ${name}`, iconName: "play", fn: () => this._remote(d, "play") });
      }
    });
    items.push("-", {
      label: "Refresh list",
      iconName: "refresh-cw",
      fn: () => this._syncDevices(),
    }, {
      label: "Reset my devices",
      iconName: "trash-2",
      danger: true,
      fn: async () => {
        if (!confirm("Clear all your device records? Devices will re-register on next heartbeat.")) return;
        try {
          await api("devices/clear", "POST");
          this.devices = [];
          toast("Devices cleared — this device will re-register shortly", { iconName: "check" });
          this._startHeartbeat();
        } catch (e) {
          toast(e.message);
        }
      },
    });
    menu(anchor, items);
  }

  async _remote(device, action) {
    const t = Player.current();
    try {
      await api("playback/command", "POST", {
        action,
        target: device.device_hash,
        origin: deviceHash(),
        origin_name: deviceName(),
        track_id: action === "play_track" && t ? t.id : null,
        position: Player.el?.currentTime || 0,
      });
      toast(
        `${action.replace("_", " ")} sent to ${device.name || "device"}`,
        { iconName: "cast" }
      );
    } catch (e) {
      toast(e.message);
    }
  }

  /* ── lyrics / video ───────────────────────────────────────────────────── */
  async openLyrics() {
    const t = Player.current();
    if (!t) return;
    const modal = document.getElementById("media-modal");
    const body = document.getElementById("media-body");
    if (!modal || !body) return;
    document.getElementById("media-title").textContent = `Lyrics · ${t.title}`;
    body.className = "lyrics-body";
    body.innerHTML = "Loading…";
    modal.hidden = false;
    try {
      const r = await api(`tracks/${t.id}/lyrics`);
      const lyrics = r.lyrics?.trim();
      const source = r.source;
      if (lyrics) {
        body.innerHTML = `<p>${lyrics}</p>`;
        if (source) {
          const s = document.createElement("small");
          s.style.cssText = "font-size: 10px; color: var(--dim); margin-top: 4px;";
          s.textContent = `— from ${source}`;
          body.appendChild(s);
        }
      } else {
        body.innerHTML = "No lyrics found for this track.";
      }
    } catch (e) {
      body.innerHTML = e.message || "Could not load lyrics";
    }
  }

  openVideo() {
    const t = Player.current();
    if (!t) return;
    const modal = document.getElementById("media-modal");
    const body = document.getElementById("media-body");
    if (!modal || !body) return;
    const id = t.yt_id || t.ytId;
    document.getElementById("media-title").textContent = `Video · ${t.title}`;
    body.className = "video-body";
    if (!id) {
      body.replaceChildren();
      const note = document.createElement("p");
      note.textContent = "No video linked. Opening YouTube search…";
      body.appendChild(note);
      window.open(
        `https://www.youtube.com/results?search_query=${encodeURIComponent(`${t.title} ${t.artist}`)}`,
        "_blank",
        "noopener",
      );
    } else {
      const frame = document.createElement("iframe");
      frame.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}`;
      frame.allow = "autoplay; encrypted-media; picture-in-picture";
      frame.allowFullscreen = true;
      frame.title = t.title;
      body.replaceChildren(frame);
      // Add download note
      const downloadNote = document.createElement("p");
      downloadNote.style.cssText = "font-size: 10px; color: var(--dim); margin-top: 4px;";
      downloadNote.textContent = "• Long-press iframe to save video (requires yt-dlp)";
      body.appendChild(downloadNote);
    }
    modal.hidden = false;
  }

  /* ── remote playback banner ───────────────────────────────────────────── */
  _paintRemote() {
    const bar = document.getElementById("remote-bar");
    if (!bar) return;
    const r = this._remoteState;
    if (!r || !r.track) {
      bar.hidden = true;
      return;
    }
    bar.hidden = false;
    const name = r.device_name || "another device";
    document.getElementById("remote-label").textContent =
      `${r.playing ? "Playing" : "Paused"} on ${name}`;
    document.getElementById("remote-track").textContent =
      `${r.track.title} — ${r.track.artist || ""}`.replace(/ — $/, "");
    document.getElementById("remote-toggle").textContent = r.playing ? "Pause" : "Play";
  }

  async _remoteSend(action, extra = {}) {
    const r = this._remoteState;
    if (!r?.device) return;
    try {
      await api("playback/command", "POST", {
        action,
        target: r.device,
        origin: deviceHash(),
        origin_name: deviceName(),
        track_id: extra.track_id || null,
        position: extra.position || 0,
      });
    } catch (e) {
      toast(e.message);
    }
  }

  async _takeOver() {
    const r = this._remoteState;
    try {
      if (r?.device) await this._remoteSend("pause");
      const me = this.devices.find((d) => d.device_hash === deviceHash());
      if (me) await api(`devices/${me.id}/activate`, "POST");
      if (r?.track) {
        Player.play([r.track], 0);
        if (r.position) setTimeout(() => Player.seekTo(Number(r.position) || 0), 400);
      }
      this._remoteState = null;
      this._paintRemote();
      this._syncDevices();
      toast("Playback moved to this device", { iconName: "cast" });
    } catch (e) {
      toast(e.message);
    }
  }

  /* ── rooms (listen along) ─────────────────────────────────────────────── */
  _roomNotice() {
    const el = document.createElement("div");
    el.className = "notice";
    el.appendChild(icon("users", { size: 15 }));
    const b = document.createElement("b");
    b.textContent = "You were invited to listen along";
    el.appendChild(b);
    const join = document.createElement("button");
    join.className = "btn sm";
    join.textContent = "Join";
    join.onclick = () => this.joinRoom(this.room);
    el.appendChild(join);
    return el;
  }

  _listenNotice() {
    const el = document.createElement("div");
    el.className = "notice";
    el.appendChild(icon("users", { size: 15 }));
    const b = document.createElement("b");
    b.textContent = `Listening with ${this.lst?.host || "host"} — they control playback`;
    el.appendChild(b);
    const leave = document.createElement("button");
    leave.className = "btn ghost sm";
    leave.textContent = "Leave";
    leave.onclick = () => {
      this.leaveRoom();
      this.draw();
    };
    el.appendChild(leave);
    return el;
  }

  /* ── deep links ───────────────────────────────────────────────────────── */
  /* The URL is the state: /#page=artist?name=X, /#page=settings, and the old
     /#room=CODE invite still works. #page=settings?joinroomcode=CODE does
     both — open settings and join that listen-along room. */
  _routeParams() {
    if (this.arg == null || this.arg === "") return [];
    if (this.view === "album" || this.view === "artist") return [["name", String(this.arg)]];
    if (this.view === "playlist") return [["id", String(this.arg)]];
    return [];
  }

  _syncHash() {
    const params = this._routeParams();
    if (this.view === "home" && !params.length) {
      if (location.hash) history.replaceState(null, "", location.pathname);
      return;
    }
    const qs = params.map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join("&");
    const hash = `#page=${this.view}${qs ? "?" + qs : ""}`;
    if (location.hash !== hash) history.replaceState(null, "", hash);
  }

  _maybeJoinRoomFromHash() {
    this._hashReady = true;
    const raw = location.hash || "";
    if (!raw) return;

    const legacy = /^#room=([\w-]+)/.exec(raw);
    if (legacy) {
      this.room = legacy[1];
      history.replaceState(null, "", location.pathname);
      this.draw();
      return;
    }

    if (!raw.startsWith("#page=")) return;
    const [view, ...tail] = raw.slice(6).split("?");
    const params = new URLSearchParams(tail.join("?"));

    const q = params.get("q");
    if (q) {
      this.q = q;
      const field = document.getElementById("q");
      if (field) field.value = q;
    }
    if (hasView(view)) {
      this.view = view;
      this.arg = view === "playlist"
        ? (params.get("id") || null)
        : (params.get("name") || null);
      this.hist = [];
      this.draw();
    }
    const code = params.get("joinroomcode");
    if (code) {
      this.joinRoom(code);
      this._syncHash();
    }
  }

  async startRoom() {
    try {
      const r = await api("rooms", "POST", {});
      this.host = r.code;
      const link = `${location.origin}/#room=${r.code}`;
      try {
        await navigator.clipboard.writeText(link);
        toast("Room started — link copied", { iconName: "users" });
      } catch (e) {
        sheet("Listen along", Object.assign(document.createElement("input"), {
          value: link, readOnly: true,
        }));
      }
      this._pushRoomState();
    } catch (e) {
      toast(e.message);
    }
  }

  async joinRoom(code) {
    try {
      const s = await api(`rooms/${code}`);
      if (s.host_id === this.me?.id) {
        toast("That is your own room", { iconName: "info" });
        return;
      }
      this.lst = { code, host: s.host_name, tid: null };
      this.room = null;
      clearInterval(this._roomTimer);
      this._roomTimer = setInterval(() => this._pollRoom(), 2000);
      this._pollRoom();
      this.draw();
    } catch (e) {
      toast(`Could not join: ${e.message}`, { iconName: "triangle-alert" });
    }
  }

  async _pollRoom() {
    if (!this.lst) return;
    let s;
    try {
      s = await api(`rooms/${this.lst.code}`);
    } catch (e) {
      toast("Listen-along ended", { iconName: "info" });
      this.leaveRoom();
      return;
    }
    if (!s.track) return;
    if (this.lst.tid !== s.track.id) {
      this.lst.tid = s.track.id;
      Player.queue = [s.track];
      Player.qi = 0;
      Player.load(s.track);
    }
    const target = (s.pos || 0) + (s.playing ? (s.server_now - s.state_ts) : 0);
    if (isFinite(target) && Math.abs((Player.el?.currentTime || 0) - target) > 1.5) {
      Player.seekTo(target);
    }
    if (s.playing && Player.el?.paused) Player.el.play().catch(() => {});
    if (!s.playing && !Player.el?.paused) Player.pause();
  }

  leaveRoom() {
    clearInterval(this._roomTimer);
    this._roomTimer = null;
    this.lst = null;
    Player.pause();
    if (location.hash.startsWith("#room=")) {
      history.replaceState(null, "", location.pathname);
    }
  }

  _pushRoomState() {
    if (!this.host) return;
    const t = Player.current();
    api(`rooms/${this.host}/state`, "POST", {
      track_id: t ? t.id : null,
      pos: Player.el?.currentTime || 0,
      playing: !Player.el?.paused,
    }).catch(() => {});
  }

  /* ── install prompt ───────────────────────────────────────────────────── */
  _setupInstall() {
    window.addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault();
      this.installEvt = e;
      const b = document.getElementById("install");
      if (b) b.hidden = false;
    });
    window.addEventListener("appinstalled", () => {
      this.installEvt = null;
      const b = document.getElementById("install");
      if (b) b.hidden = true;
      toast("mcmusic installed", { iconName: "check" });
    });
  }

  async _install() {
    if (!this.installEvt) {
      toast("Use your browser menu → Install app", { iconName: "info" });
      return;
    }
    this.installEvt.prompt();
    try {
      await this.installEvt.userChoice;
    } catch (e) { /* ignore */ }
    this.installEvt = null;
    const b = document.getElementById("install");
    if (b) b.hidden = true;
  }

  /* ── service worker + updates ─────────────────────────────────────────── */
  async _registerServiceWorker() {
    if (!("serviceWorker" in navigator)) return;
    try {
      const reg = await navigator.serviceWorker.register("/sw.js", {
        scope: "/",
        // Without this the browser may serve sw.js from its HTTP cache for up
        // to 24h, which hides a deploy from the update prompt below.
        updateViaCache: "none",
      });
      this._swRegistration = reg;

      if (reg.waiting) this._markUpdateReady();

      reg.addEventListener("updatefound", () => {
        const sw = reg.installing;
        if (!sw) return;
        sw.addEventListener("statechange", () => {
          if (sw.state === "installed" && navigator.serviceWorker.controller) {
            this._markUpdateReady();
          }
        });
      });

      navigator.serviceWorker.addEventListener("controllerchange", () => {
        if (this._reloadingForUpdate) return;
        // A controller change without our apply flow should still keep audio.
        if (!Player.playing) this._reloadingForUpdate = true;
      });

      // A long-lived tab would otherwise never see a deploy. Re-check when the
      // tab comes back into view, at most every half hour.
      const recheck = () => {
        if (document.visibilityState !== "visible") return;
        if (Date.now() - (this._lastUpdateCheck || 0) < 30 * 60 * 1000) return;
        this._checkForUpdates(false);
      };
      document.addEventListener("visibilitychange", recheck);
      window.addEventListener("focus", recheck);
    } catch (e) {
      console.warn("service worker failed", e);
    }
  }

  _markUpdateReady() {
    if (this.updateReady) return;
    this.updateReady = true;
    toast("Update ready — apply after this track", {
      iconName: "refresh-cw",
      duration: 12000,
      action: { label: "Apply", fn: () => this.applyUpdate() },
    });
    if (this.view === "settings") this.draw();
  }

  checkForUpdates(manual = false) {
    return this._checkForUpdates(manual);
  }

  async _checkForUpdates(manual = false) {
    this._lastUpdateCheck = Date.now();
    try {
      const v = await api("version");
      if (v.build && this.build && v.build !== this.build) {
        this._markUpdateReady();
      } else if (manual) {
        toast("You are up to date", { iconName: "check" });
      }
      // Re-fetch the worker on automatic checks too, so a redeployed sw.js is
      // noticed without waiting for the next navigation.
      if (this._swRegistration) {
        try {
          await this._swRegistration.update();
        } catch (e) { /* ignore */ }
      }
    } catch (e) {
      if (manual) toast("Could not check for updates offline", { iconName: "wifi-off" });
    }
  }

  applyUpdate() {
    if (!this.updateReady && !this._swRegistration?.waiting) {
      location.reload();
      return;
    }

    // Never cut audio off mid-track unless the listener asked twice.
    if (Player.playing && !this._forceApply) {
      this._pendingApply = true;
      this._forceApply = true;
      toast("Update queued — it will apply when playback pauses", {
        iconName: "refresh-cw",
        action: { label: "Now", fn: () => this._applyNow() },
      });
      return;
    }
    this._applyNow();
  }

  async _applyNow() {
    this._pendingApply = false;
    Player.save();
    await new Promise((r) => setTimeout(r, 120)); // let the snapshot hit IndexedDB
    const waiting = this._swRegistration?.waiting;
    if (waiting) {
      this._reloadingForUpdate = true;
      waiting.postMessage({ type: "SKIP_WAITING" });
      const reload = () => location.reload();
      navigator.serviceWorker?.addEventListener("controllerchange", reload, { once: true });
      setTimeout(reload, 1500);
    } else {
      location.reload();
    }
  }

  /* ── keyboard ─────────────────────────────────────────────────────────── */
  _setupKeyboard() {
    window.addEventListener("keydown", (e) => {
      const tag = e.target?.tagName;
      const editing = tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" ||
        e.target?.isContentEditable;

      if (e.key === "Escape") {
        if (editing) e.target.blur?.();
        closeSheet();
        this.toggleDrawer(false);
        return;
      }
      if (editing || !this.me) return;

      switch (e.key) {
        case " ":
          e.preventDefault();
          Player.toggle();
          break;
        case "ArrowRight":
          if (e.shiftKey) {
            e.preventDefault();
            Player.next();
          }
          break;
        case "ArrowLeft":
          if (e.shiftKey) {
            e.preventDefault();
            Player.prev();
          }
          break;
        case "/":
          e.preventDefault();
          document.getElementById("q")?.focus();
          break;
        case "m":
        case "M":
          Player.toggleMute();
          this._paintControls();
          break;
        case "l":
        case "L": {
          const t = Player.current();
          if (t) toggleLike(t);
          break;
        }
        case "q":
        case "Q":
          this.toggleDrawer();
          break;
        case "ArrowUp":
          if (e.shiftKey) {
            e.preventDefault();
            Player.setVolume(Player.volume + 0.05);
          }
          break;
        case "ArrowDown":
          if (e.shiftKey) {
            e.preventDefault();
            Player.setVolume(Player.volume - 0.05);
          }
          break;
        default:
          break;
      }
    });
  }
}

/* Pull the page tint from the current cover. Covers are served same-origin,
   but a tainted/remote image simply leaves the token fallback in place. */
function ambientTint(img) {
  try {
    if (!img || !img.complete || !img.naturalWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 16;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;
    ctx.drawImage(img, 0, 0, 16, 16);
    const data = ctx.getImageData(0, 0, 16, 16).data;
    let r = 0, g = 0, b = 0, n = 0;
    for (let i = 0; i < data.length; i += 4) {
      r += data[i]; g += data[i + 1]; b += data[i + 2]; n += 1;
    }
    if (!n) return;
    r = Math.round(r / n); g = Math.round(g / n); b = Math.round(b / n);
    root.style.setProperty("--hero", `rgb(${r}, ${g}, ${b})`);
    root.style.setProperty("--tint", `rgb(${Math.round(r * 0.3)}, ${Math.round(g * 0.3)}, ${Math.round(b * 0.3)})`);
  } catch {
    /* cross-origin cover: keep the palette-derived fallback */
  }
}

/* ── boot ───────────────────────────────────────────────────────────────── */
window.App = new App();
window.Views = Views;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => window.App.init(), { once: true });
} else {
  window.App.init();
}

/* expose for the shell / debugging without another import */
window.mcmusic = { CONFIG, Player, Auth, Mobile };

/* ==========================================================================
   mcmusic — session and RoturLink
   The browser never sees a Rotur token. Sign-in is a full-page redirect to
   /api/auth/rotur/authorize; the server exchanges the code (PKCE), links the
   account and sets our own session cookie.
   ========================================================================== */

import { api } from "./api.js";
import * as store from "./cache.js";

export const Auth = {
  me: null,
  rotur: { linked: false, configured: false },
  discord: { linked: false, configured: false, missing: [] },
  listeners: new Set(),

  async init() {
    let cached = null;
    try {
      cached = await store.get(store.K.user);
    } catch (e) { /* ignore */ }
    if (cached && cached.id) {
      this.me = cached;
      this._emit();
    }

    const [me, rotur, discord] = await Promise.all([
      api("me").catch(() => null),
      api("auth/rotur/status").catch(() => null),
      api("auth/discord/status").catch(() => null),
    ]);

    if (me && me.id) {
      this.me = me;
      store.set(store.K.user, me).catch(() => {});
    } else if (!me) {
      this.me = null;
      store.del(store.K.user).catch(() => {});
    }

    if (rotur) {
      this.rotur = {
        linked: !!rotur.linked,
        configured: !!rotur.configured,
        rotur_id: rotur.rotur_id || null,
        rotur_username: rotur.rotur_username || null,
        session_valid: !!rotur.session_valid,
      };
    }
    if (discord) {
      this.discord = {
        linked: !!discord.linked,
        configured: !!discord.configured,
        missing: Array.isArray(discord.missing) ? discord.missing : [],
        discord_id: discord.discord_id || null,
        discord_username: discord.discord_username || null,
        session_valid: !!discord.session_valid,
      };
    }

    this._emit();
    return this.me;
  },

  get signedIn() {
    return !!(this.me && this.me.id);
  },

  get isAdmin() {
    return !!(this.me && this.me.is_admin);
  },

  async refresh() {
    try {
      const me = await api("me");
      this.me = me;
      await store.set(store.K.user, me);
      this._emit();
      return me;
    } catch (e) {
      this.me = null;
      this._emit();
      return null;
    }
  },

  async login(username, password) {
    const me = await api("login", "POST", { username, password });
    this.me = me;
    await store.set(store.K.user, me);
    this._emit();
    return me;
  },

  async register(username, password, invite) {
    const me = await api("register", "POST", { username, password, invite });
    this.me = me;
    await store.set(store.K.user, me);
    this._emit();
    return me;
  },

  async logout() {
    try {
      await api("logout", "POST");
    } catch (e) { /* offline logout still clears local state */ }
    this.me = null;
    this.rotur = { linked: false, configured: this.rotur.configured, rotur_username: null };
    this.discord = {
      linked: false,
      configured: this.discord.configured,
      missing: this.discord.missing || [],
      discord_username: null,
    };
    await store.del(store.K.user).catch(() => {});
    this._emit();
  },

  /** Full-page redirect. `next` must be a local path. */
  roturLogin(next = "/") {
    const target = next.startsWith("/") ? next : "/";
    location.assign(`/api/auth/rotur/authorize?next=${encodeURIComponent(target)}`);
  },

  async unlinkRotur() {
    const r = await api("auth/rotur/unlink", "POST");
    this.rotur = { ...this.rotur, linked: false, rotur_id: null, session_valid: false };
    await this.refresh();
    return r;
  },

  /** Full-page redirect; the server exchanges the code and links the account. */
  discordLogin(next = "/") {
    const target = next.startsWith("/") ? next : "/";
    location.assign(`/api/auth/discord/authorize?next=${encodeURIComponent(target)}`);
  },

  async unlinkDiscord() {
    const r = await api("auth/discord/unlink", "POST");
    this.discord = { ...this.discord, linked: false, discord_id: null, session_valid: false };
    await this.refresh();
    return r;
  },

  async changePassword(oldPw, newPw) {
    return api("password", "POST", { old: oldPw, new: newPw });
  },

  async setEmail(email) {
    const me = await api("auth/email", "POST", { email });
    this.me = me;
    await store.set(store.K.user, me);
    this._emit();
    return me;
  },

  /** Ask the server to mail a one-time reset link. Same reply either way. */
  async requestReset(email) {
    return api("auth/reset/request", "POST", { email });
  },

  /** True while the link can still be spent; the page checks it on open. */
  async checkReset(token) {
    return api("auth/reset/check", "POST", { token });
  },

  async confirmReset(token, password) {
    return api("auth/reset/confirm", "POST", { token, password });
  },

  onChange(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  },

  _emit() {
    for (const fn of this.listeners) {
      try {
        fn({ me: this.me, rotur: this.rotur, discord: this.discord });
      } catch (e) { /* ignore */ }
    }
  },
};

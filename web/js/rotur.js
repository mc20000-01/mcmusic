/* ==========================================================================
   mcmusic — RoturLink presentation helpers
   Auth lives in auth.js; this module only describes link state for the UI so
   the settings view has one small API and no token handling at all.
   ========================================================================== */

import { Auth } from "./auth.js";

export const RoturLink = {
  get configured() {
    return !!Auth.rotur.configured;
  },

  get linked() {
    return !!Auth.rotur.linked;
  },

  get roturId() {
    return Auth.rotur.rotur_id || null;
  },

  get username() {
    return Auth.rotur.rotur_username || null;
  },

  get healthy() {
    return !!(Auth.rotur.linked && Auth.rotur.session_valid);
  },

  /** {ready, reason} for the activity sink, as reported by the server. */
  get activity() {
    return Auth.rotur.activity || null;
  },

  /** Human-readable state for settings rows. */
  describe() {
    if (!this.configured) return "RoturLink is not configured on this server";
    if (!this.linked) return "Not linked — sign in with Rotur from the login screen";
    if (!this.healthy)    return `Linked as ${this.username || this.roturId} — session needs a refresh`;
    return `Linked as ${this.username || this.roturId}`;
  },

  signIn(next = "/") {
    Auth.roturLogin(next);
  },

  async unlink() {
    return Auth.unlinkRotur();
  },
};

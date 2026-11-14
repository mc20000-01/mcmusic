/* ==========================================================================
   mcmusic — playback engine
   Owns the single <audio> element. Everything else (deck, now view, queue,
   media keys, bots) observes this module. Playback state is persisted so a
   background update can reload the page without losing the queue.
   ========================================================================== */

import { api } from "./api.js";
import * as cache from "./cache.js";

const EV = "mcmusic:playback";
const PUBLISH_MS = 3000;
const SAVE_MS = 5000;

export const Player = {
  el: null,
  queue: [],
  qi: -1,
  shuffle: false,
  repeat: "off",          // off | all | one
  volume: 0.8,
  muted: false,
  hideExplicit: false,
  private: false,
  duration: 0,
  playing: false,
  seeking: false,
  bars: new Set(),

  _reported: false,
  _lastPaint: 0,
  _lastPublish: 0,
  _lastSave: 0,
  _scrubPct: 0,
  _wasPlaying: false,
  _ready: false,

  /* ── setup ──────────────────────────────────────────────────────────── */
  init(el) {
    if (!el) throw new Error("Player.init needs an audio element");
    this.el = el;
    el.preload = "auto";
    el.volume = this.volume;
    el.muted = this.muted;

    el.addEventListener("play", () => {
      this.playing = true;
      this._paint(true);
      this._publish(true);
      this._mediaState("playing");
      this._emit("playing");
    });
    el.addEventListener("pause", () => {
      this.playing = false;
      this._paint(true);
      this._publish(true);
      this.save();
      this._mediaState("paused");
      this._emit("paused");
    });
    el.addEventListener("timeupdate", () => {
      if (!this.seeking) this._paint();
      this._maybeReport();
      this._throttlePublish();
      this._throttleSave();
    });
    el.addEventListener("progress", () => this._paint());
    el.addEventListener("durationchange", () => {
      this.duration = el.duration || 0;
      this._paint(true);
    });
    el.addEventListener("loadedmetadata", () => {
      this.duration = el.duration || 0;
      this._ready = true;
      this._paint();
      this._publish(true);
    });
    el.addEventListener("waiting", () => this._emit("buffering", true));
    el.addEventListener("playing", () => this._emit("buffering", false));
    el.addEventListener("ended", () => {
      this._reportPlay(true);
      this.next(true);
    });
    el.addEventListener("error", () => {
      const err = el.error;
      if (!err) return;
      this._emit("error", { code: err.code, message: err.message });
    });

    this._setupMediaSession();
    const resume = this.loadState();
    if (resume) this._restore(resume);
    return this;
  },

  /* ── queue ──────────────────────────────────────────────────────────── */
  setQueue(list, index = 0, { shuffle = false } = {}) {
    if (!list || !list.length) return;
    const allowed = this.hideExplicit ? list.filter((t) => !t.explicit || list[index] === t) : [...list];
    const current = list[index];
    let q = allowed;
    let idx = Math.max(0, q.indexOf(current));

    if (shuffle) {
      this.shuffle = true;
      q = this._shuffled(q, idx);
      idx = 0;
    }
    this.queue = q;
    this.qi = idx;
    this.load(q[idx]);
  },

  play(list, index = 0, opts = {}) {
    if (!list || !list.length) return;
    this.setQueue(list, index, opts);
  },

  add(track, { next = false } = {}) {
    if (!track) return;
    if (!this.queue.length) {
      this.play([track], 0);
      return;
    }
    const at = next ? this.qi + 1 : this.queue.length;
    this.queue.splice(at, 0, track);
    this._emit("queue");
    this.save();
  },

  removeAt(index) {
    if (index < 0 || index >= this.queue.length) return false;
    if (index < this.qi) this.qi -= 1;
    const [gone] = this.queue.splice(index, 1);
    this._emit("queue");
    this.save();
    return !!gone;
  },

  current() {
    return this.queue[this.qi] || null;
  },

  upNext(limit = 10) {
    return this.queue.slice(this.qi + 1, this.qi + 1 + limit);
  },

  /* ── transport ──────────────────────────────────────────────────────── */
  load(track, { autoplay = true, position = 0 } = {}) {
    if (!track || !this.el) return;
    this._reported = false;
    this.duration = track.duration || 0;
    this.el.src = `/api/tracks/${track.id}/stream`;
    this.el.load?.();

    if (position > 0) {
      const seek = () => {
        if (!this.el.duration) return;
        this.el.currentTime = Math.min(position, this.el.duration - 0.25);
        this.el.removeEventListener("loadedmetadata", seek);
      };
      this.el.addEventListener("loadedmetadata", seek);
      if (this.el.readyState >= 1) seek();
    }

    if (autoplay) {
      const p = this.el.play();
      if (p && p.catch) {
        p.catch(() => {
          this._emit("blocked", {});
        });
      }
    }

    this._mediaMeta(track);
    this._paint();
    this._emit("track", track);
    this._publish(true);
    this._prefetchNext();
    this.save();
  },

  toggle() {
    if (!this.el) return;
    if (this.el.paused) this.el.play().catch(() => this._emit("blocked", {}));
    else this.el.pause();
  },

  pause() {
    if (this.el && !this.el.paused) this.el.pause();
  },

  next(auto = false) {
    if (!this.el) return;

    if (this.repeat === "one" && auto) {
      this.el.currentTime = 0;
      this._reported = false;
      this.el.play().catch(() => {});
      return;
    }

    if (this.qi < this.queue.length - 1) {
      this.qi += 1;
      this.load(this.queue[this.qi]);
      return;
    }

    if (this.repeat === "all" && this.queue.length) {
      this.qi = 0;
      this.load(this.queue[0]);
      return;
    }

    if (auto) this._autoplayRadio();
    else this.pause();
  },

  prev() {
    if (!this.el) return;
    if (this.el.currentTime > 3 || this.qi <= 0) {
      this.el.currentTime = 0;
      return;
    }
    this.qi -= 1;
    this.load(this.queue[this.qi]);
  },

  seekTo(seconds) {
    if (!this.el || !isFinite(seconds)) return;
    const max = this.el.duration || this.duration || 0;
    this.el.currentTime = Math.max(0, Math.min(seconds, max ? max - 0.05 : 0));
    this._paint();
    this._emit("seek");
    this._publish(true);
  },

  seekFraction(f) {
    const d = this.el?.duration || this.duration;
    if (!d) return;
    this.seekTo(f * d);
  },

  setVolume(v) {
    this.volume = Math.max(0, Math.min(1, Number(v) || 0));
    if (this.el) this.el.volume = this.volume;
    if (this.volume > 0 && this.muted) this.setMuted(false);
    this._emit("volume", { volume: this.volume, muted: this.muted });
    this.save();
  },

  setMuted(m) {
    this.muted = !!m;
    if (this.el) this.el.muted = this.muted;
    this._emit("volume", { volume: this.volume, muted: this.muted });
    this.save();
  },

  toggleMute() {
    this.setMuted(!this.muted);
  },

  toggleShuffle() {
    this.shuffle = !this.shuffle;
    if (this.shuffle && this.queue.length) {
      const head = this.queue.slice(0, this.qi + 1);
      const tail = this._shuffled(this.queue.slice(this.qi + 1), 0);
      this.queue = head.concat(tail);
      this._emit("queue");
      this.save();
    }
    this._emit("state", {});
    return this.shuffle;
  },

  cycleRepeat() {
    this.repeat = { off: "all", all: "one", one: "off" }[this.repeat] || "off";
    this._emit("state", {});
    this.save();
    return this.repeat;
  },

  /* ── progress bars ──────────────────────────────────────────────────── */
  bindProgress(root) {
    if (!root) return () => {};
    const hit = root.querySelector(".prog-hit");
    const bar = {
      root,
      hit,
      fill: root.querySelector(".prog-fill"),
      buf: root.querySelector(".prog-buf"),
      knob: root.querySelector(".prog-knob"),
      cur: root.querySelector(".prog-time"),
      dur: root.querySelector(".prog-time.right"),
    };
    this.bars.add(bar);

    if (hit) {
      const fraction = (ev) => {
        const rect = hit.getBoundingClientRect();
        const x = Math.min(Math.max(ev.clientX - rect.left, 0), rect.width);
        return rect.width ? x / rect.width : 0;
      };

      const down = (ev) => {
        if (!this.current()) return;
        ev.preventDefault();
        hit.setPointerCapture?.(ev.pointerId);
        this.seeking = true;
        this._wasPlaying = this.playing;
        this.el.pause();
        root.classList.add("seeking");
        this._scrubPct = fraction(ev);
        this._paint();
      };

      const move = (ev) => {
        if (!this.seeking) return;
        this._scrubPct = fraction(ev);
        this._paint();
      };

      const up = (ev) => {
        if (!this.seeking) return;
        this.seeking = false;
        root.classList.remove("seeking");
        const pct = ev ? fraction(ev) : this._scrubPct;
        this.seekFraction(pct);
        if (this._wasPlaying) this.el.play().catch(() => {});
        hit.releasePointerCapture?.(ev?.pointerId);
      };

      hit.addEventListener("pointerdown", down);
      hit.addEventListener("pointermove", move);
      hit.addEventListener("pointerup", up);
      hit.addEventListener("pointercancel", up);
      hit.addEventListener("keydown", (ev) => {
        const d = this.el?.duration || this.duration || 0;
        if (!d) return;
        if (ev.key === "ArrowRight") {
          ev.preventDefault();
          this.seekTo((this.el.currentTime || 0) + 5);
        } else if (ev.key === "ArrowLeft") {
          ev.preventDefault();
          this.seekTo((this.el.currentTime || 0) - 5);
        } else if (ev.key === "Home") {
          ev.preventDefault();
          this.seekTo(0);
        } else if (ev.key === "End") {
          ev.preventDefault();
          this.seekTo(d - 1);
        }
      });
    }

    this._paint();
    return () => {
      this.bars.delete(bar);
    };
  },

  _paint(force = false) {
    const now = performance.now();
    if (!force && now - this._lastPaint < 100) return;
    this._lastPaint = now;
    const el = this.el;
    if (!el) return;
    const dur = el.duration || this.duration || 0;
    const pos = this.seeking ? this._scrubPct * dur : el.currentTime || 0;
    const pct = dur ? Math.min(100, (pos / dur) * 100) : 0;

    let buffered = 0;
    try {
      if (el.buffered && el.buffered.length) {
        buffered = (el.buffered.end(el.buffered.length - 1) / (dur || 1)) * 100;
      }
    } catch (e) { /* ignore */ }

    for (const bar of this.bars) {
      if (bar.fill) bar.fill.style.transform = `scaleX(${pct / 100})`;
      if (bar.buf) bar.buf.style.transform = `scaleX(${Math.max(pct, Math.min(100, buffered)) / 100})`;
      if (bar.knob) bar.knob.style.left = `${pct}%`;
      if (bar.cur) bar.cur.textContent = fmtTime(pos);
      if (bar.dur) bar.dur.textContent = fmtTime(dur);
      if (bar.hit) {
        bar.hit.setAttribute("aria-valuenow", String(Math.round(pct)));
        bar.hit.setAttribute("aria-valuetext", `${fmtTime(pos)} of ${fmtTime(dur)}`);
      }
      if (bar.root) bar.root.dataset.playing = this.playing ? "1" : "0";
    }

    if ("mediaSession" in navigator) {
      try {
        if (dur > 0 && isFinite(dur)) {
          navigator.mediaSession.setPositionState({
            duration: dur,
            position: Math.min(pos, dur),
            playbackRate: el.playbackRate || 1,
          });
        }
      } catch (e) { /* ignore */ }
    }
  },

  /* ── media session ──────────────────────────────────────────────────── */
  _setupMediaSession() {
    if (!("mediaSession" in navigator)) return;
    const ms = navigator.mediaSession;
    const safe = (name, fn) => {
      try {
        ms.setActionHandler(name, fn);
      } catch (e) { /* unsupported action */ }
    };
    safe("play", () => this.el.play().catch(() => {}));
    safe("pause", () => this.pause());
    safe("previoustrack", () => this.prev());
    safe("nexttrack", () => this.next());
    safe("seekbackward", (d) => this.seekTo((this.el.currentTime || 0) - (d.seekOffset || 10)));
    safe("seekforward", (d) => this.seekTo((this.el.currentTime || 0) + (d.seekOffset || 10)));
    safe("seekto", (d) => this.seekTo(d.seekTime || 0));
  },

  _mediaMeta(t) {
    if (!("mediaSession" in navigator) || !t) return;
    try {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: t.title || "",
        artist: t.artist || "",
        album: t.album || "",
        artwork: [
          { src: `/api/tracks/${t.id}/cover`, sizes: "512x512", type: "image/jpeg" },
        ],
      });
    } catch (e) { /* ignore */ }
  },

  _mediaState(state) {
    if (!("mediaSession" in navigator)) return;
    try {
      navigator.mediaSession.playbackState = state;
    } catch (e) { /* ignore */ }
  },

  /* ── reporting / publishing ─────────────────────────────────────────── */
  _maybeReport() {
    const t = this.current();
    if (!t || this._reported || this.private) return;
    const d = this.el.duration || 0;
    if (!d) return;
    if (this.el.currentTime > 20 || this.el.currentTime / d > 0.4) this._reportPlay(false);
  },

  _reportPlay(completed) {
    const t = this.current();
    if (!t || this.private) return;
    if (this._reported && !completed) return;
    this._reported = true;
    const d = this.el.duration || t.duration || 1;
    api("plays", "POST", {
      track_id: t.id,
      completed: !!completed || this.el.currentTime / d > 0.8,
    }).catch(() => {});
  },

  _publish(force = false) {
    if (!this.el) return;
    const now = Date.now();
    if (!force && now - this._lastPublish < PUBLISH_MS) return;
    this._lastPublish = now;
    const t = this.current();
    api("playback", "POST", {
      track_id: t ? t.id : null,
      position: Math.round((this.el.currentTime || 0) * 10) / 10,
      duration: Math.round((this.el.duration || this.duration || 0) * 10) / 10,
      playing: this.playing,
      queue: this.queue.slice(this.qi + 1).map((x) => x.id),
      device: this.device || null,
    }).catch(() => {});
  },

  _throttlePublish() {
    if (Date.now() - this._lastPublish >= PUBLISH_MS) this._publish();
  },

  /* ── persistence ────────────────────────────────────────────────────── */
  snapshot() {
    const t = this.current();
    return {
      track: t || null,
      queue: this.queue,
      qi: this.qi,
      position: this.el ? this.el.currentTime || 0 : 0,
      duration: this.el?.duration || this.duration || 0,
      playing: this.playing,
      volume: this.volume,
      muted: this.muted,
      shuffle: this.shuffle,
      repeat: this.repeat,
      saved: Date.now(),
    };
  },

  save() {
    if (Date.now() - this._lastSave < 700 && this.playing) return;
    this._lastSave = Date.now();
    const snap = this.snapshot();
    if (!snap.track && !snap.queue.length) return;
    cache.set(cache.K.player, snap).catch(() => {});
  },

  async loadState() {
    const snap = await cache.get(cache.K.player);
    if (!snap || !snap.track) return null;
    const age = (Date.now() - (snap.saved || 0)) / 1000;
    if (age > 60 * 60 * 24 * 7) return null;
    return snap;
  },

  _restore(snap) {
    try {
      this.queue = Array.isArray(snap.queue) ? snap.queue : [snap.track];
      this.qi = Math.max(0, Math.min(snap.qi ?? 0, this.queue.length - 1));
      this.volume = typeof snap.volume === "number" ? snap.volume : this.volume;
      this.muted = !!snap.muted;
      this.shuffle = !!snap.shuffle;
      this.repeat = snap.repeat || "off";
      this.el.volume = this.volume;
      this.el.muted = this.muted;
      const stale = (Date.now() - (snap.saved || 0)) / 1000 > 60 * 30;
      const track = this.queue[this.qi];
      if (!track) return;
      this.load(track, { autoplay: false, position: stale ? 0 : snap.position || 0 });
      this._emit("restored", { track, paused: true });
      this._paint();
    } catch (e) {
      console.warn("player: restore failed", e);
    }
  },

  async clearState() {
    await cache.del(cache.K.player).catch(() => {});
  },

  /* ── prefetch ───────────────────────────────────────────────────────── */
  async _prefetchNext() {
    const upcoming = this.upNext(3);
    const t = this.current();
    const list = (t ? [t] : []).concat(upcoming);
    if (!list.length) return;
    try {
      await cache.prefetch(list, { count: 3 });
    } catch (e) { /* ignore */ }
  },

  /* ── autoplay radio ─────────────────────────────────────────────────── */
  _autoplayRadio() {
    const t = this.current();
    if (!t) return;
    api(`radio/${t.id}`)
      .then((r) => {
        const have = new Set(this.queue.map((x) => x.id));
        const add = (r.tracks || []).filter((x) => !have.has(x.id)).slice(0, 20);
        if (!add.length) return;
        this.queue.push(...add);
        this.qi += 1;
        this.load(this.queue[this.qi]);
        this._emit("info", { message: "Autoplay: similar tracks" });
      })
      .catch(() => {});
  },

  /* ── remote commands ────────────────────────────────────────────────── */
  applyCommand(cmd) {
    if (!cmd || !cmd.action) return false;
    const arg = cmd.arg || {};
    switch (cmd.action) {
      case "play":
        if (this.el?.paused) this.el.play().catch(() => {});
        return true;
      case "pause":
        this.pause();
        return true;
      case "toggle":
        this.toggle();
        return true;
      case "skip":
        this.next();
        return true;
      case "prev":
        this.prev();
        return true;
      case "remove":
        return this.removeAt(Number(arg.index));
      case "enqueue":
        return false; // the app resolves track ids and calls add()
      default:
        return false;
    }
  },

  /* ── helpers ────────────────────────────────────────────────────────── */
  _shuffled(list, keepFirst) {
    const out = [...list];
    for (let i = out.length - 1; i > keepFirst; i--) {
      const j = keepFirst + 1 + Math.floor(Math.random() * (i - keepFirst));
      [out[i], out[j]] = [out[j], out[i]];
    }
    return out;
  },

  _throttleSave() {
    if (Date.now() - this._lastSave >= SAVE_MS) this.save();
  },

  _emit(kind, detail) {
    const payload = {
      kind,
      detail,
      track: this.current(),
      playing: this.playing,
      position: this.el?.currentTime || 0,
      duration: this.el?.duration || this.duration || 0,
      queue: this.queue,
      qi: this.qi,
      shuffle: this.shuffle,
      repeat: this.repeat,
      volume: this.volume,
      muted: this.muted,
    };
    try {
      window.dispatchEvent(new CustomEvent(EV, { detail: payload }));
    } catch (e) { /* ignore */ }
    if (kind === "track" || kind === "state" || kind === "queue") this._paint();
  },
};

export function fmtTime(s) {
  s = Math.max(0, Math.round(Number(s) || 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function deviceHash() {
  const parts = [
    navigator.userAgent || "",
    navigator.platform || "",
    `${screen.width}x${screen.height}`,
    String(new Date().getTimezoneOffset()),
    navigator.language || "",
    String(navigator.hardwareConcurrency || ""),
  ];
  let h = 0;
  for (const p of parts) {
    for (let i = 0; i < p.length; i++) h = ((h << 5) - h + p.charCodeAt(i)) | 0;
  }
  return Math.abs(h).toString(36).slice(-16);
}

export function deviceName() {
  const ua = navigator.userAgent;
  if (/iPad|Tablet/.test(ua)) return "Tablet";
  if (/Mobile|Android|iPhone/.test(ua)) return "Phone";
  if (/Windows/.test(ua)) return "PC";
  if (/Macintosh/.test(ua)) return "Mac";
  if (/Linux/.test(ua)) return "Linux";
  return "Device";
}

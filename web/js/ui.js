/* ==========================================================================
   mcmusic — component library
   Every interactive primitive is built here so views stay declarative.
   Icons come from icons.js and degrade to a real fallback glyph.
   ========================================================================== */

import { api } from "./api.js";
import * as cache from "./cache.js";
import { icon } from "./icons.js";

const $ = (sel, root = document) => root.querySelector(sel);

/* ── toast ──────────────────────────────────────────────────────────────── */
export function toast(message, opts = {}) {
  const { duration = 3400, action = null, iconName = null } = opts;
  let host = document.getElementById("toasts");
  if (!host) {
    host = document.createElement("div");
    host.id = "toasts";
    document.body.appendChild(host);
  }

  const el = document.createElement("div");
  el.className = "toast";
  el.setAttribute("role", "status");

  if (iconName) el.appendChild(icon(iconName, { size: 15 }));
  const span = document.createElement("span");
  span.textContent = String(message);
  el.appendChild(span);

  if (action) {
    const btn = document.createElement("button");
    btn.className = "toast-act";
    btn.textContent = action.label;
    btn.onclick = () => {
      try { action.fn(); } finally { dismiss(); }
    };
    el.appendChild(btn);
  }

  host.appendChild(el);

  let timer = setTimeout(dismiss, duration);
  el.addEventListener("pointerenter", () => clearTimeout(timer));

  function dismiss() {
    clearTimeout(timer);
    el.classList.add("out");
    setTimeout(() => el.remove(), 200);
  }

  return dismiss;
}

/* ── overlays ───────────────────────────────────────────────────────────── */
let scrim = null;
let openSheet = null;

function ensureScrim() {
  if (scrim && document.body.contains(scrim)) return scrim;
  scrim = document.createElement("div");
  scrim.className = "scrim";
  scrim.addEventListener("click", () => closeSheet());
  document.body.appendChild(scrim);
  return scrim;
}

export function sheet(title, ...nodes) {
  closeSheet(true);
  const s = ensureScrim();
  s.classList.add("on");

  const box = document.createElement("div");
  box.className = "sheet";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");

  const head = document.createElement("div");
  head.className = "sheet-h";
  const h = document.createElement("h2");
  h.textContent = title;
  const close = document.createElement("button");
  close.className = "iconbtn";
  close.setAttribute("aria-label", "Close");
  close.appendChild(icon("x", { size: 16 }));
  close.onclick = () => closeSheet();
  head.appendChild(h);
  head.appendChild(close);

  const body = document.createElement("div");
  body.className = "sheet-b";
  nodes.filter(Boolean).forEach((n) => body.appendChild(n));

  box.appendChild(head);
  box.appendChild(body);
  document.body.appendChild(box);

  const prev = document.activeElement;
  openSheet = {
    box,
    close: () => closeSheet(),
    body,
    prev,
  };

  const focusable = box.querySelector("input, button, select, textarea, [tabindex]");
  setTimeout(() => focusable?.focus({ preventScroll: true }), 40);
  return openSheet.close;
}

export function closeSheet(immediate = false) {
  if (!openSheet) {
    scrim?.classList.remove("on");
    return;
  }
  const { box, prev } = openSheet;
  openSheet = null;
  scrim?.classList.remove("on");
  if (immediate) {
    box.remove();
    return;
  }
  box.style.transition = "opacity 140ms ease, transform 140ms ease";
  box.style.opacity = "0";
  box.style.transform += " scale(0.98)";
  setTimeout(() => box.remove(), 140);
  try { prev?.focus?.({ preventScroll: true }); } catch (e) { /* ignore */ }
}

/* ── context menu ───────────────────────────────────────────────────────── */
let currentMenu = null;

export function menu(anchor, items) {
  closeMenu();
  const list = (items || []).filter(Boolean);
  if (!list.length) return null;

  const m = document.createElement("div");
  m.className = "menu";
  m.setAttribute("role", "menu");

  for (const item of list) {
    if (item === "-" || item.sep) {
      m.appendChild(document.createElement("hr"));
      continue;
    }
    const btn = document.createElement("button");
    btn.setAttribute("role", "menuitem");
    if (item.danger) btn.className = "danger";
    if (item.iconName) btn.appendChild(icon(item.iconName, { size: 14 }));
    const label = document.createElement("span");
    label.textContent = item.label;
    btn.appendChild(label);
    btn.onclick = () => {
      closeMenu();
      try { item.fn?.(); } catch (e) { console.warn(e); }
    };
    m.appendChild(btn);
  }

  document.body.appendChild(m);

  const rect = anchor?.getBoundingClientRect
    ? anchor.getBoundingClientRect()
    : { left: 20, right: 20, top: 80, bottom: 80 };

  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const mw = m.offsetWidth;
  const mh = m.offsetHeight;
  const left = Math.min(Math.max(8, rect.right - mw), vw - mw - 8);
  const below = rect.bottom + 6;
  const top = below + mh > vh - 8 ? Math.max(8, rect.top - mh - 6) : below;
  m.style.left = `${left}px`;
  m.style.top = `${top}px`;

  currentMenu = m;
  const dismiss = (ev) => {
    if (!m.contains(ev.target)) closeMenu();
  };
  setTimeout(() => {
    document.addEventListener("pointerdown", dismiss, { once: true });
  }, 0);

  const first = m.querySelector("button");
  first?.focus({ preventScroll: true });
  return m;
}

export function closeMenu() {
  if (currentMenu) {
    currentMenu.remove();
    currentMenu = null;
  }
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeMenu();
    closeSheet();
  }
});

/* ── empty state ────────────────────────────────────────────────────────── */
export function empty(title, hint, opts = {}) {
  const { iconName = "music", action = null } = opts;
  const wrap = document.createElement("div");
  wrap.className = "empty";
  wrap.appendChild(icon(iconName, { size: 26 }));
  const h2 = document.createElement("h2");
  h2.textContent = title;
  const p = document.createElement("p");
  p.textContent = hint || "";
  wrap.appendChild(h2);
  if (hint) wrap.appendChild(p);
  if (action) {
    const btn = document.createElement("button");
    btn.className = "btn";
    btn.textContent = action.label;
    btn.onclick = action.fn;
    wrap.appendChild(btn);
  }
  return wrap;
}

export function notice(text, { actionLabel, onAction } = {}) {
  const el = document.createElement("div");
  el.className = "notice";
  el.appendChild(icon("info", { size: 15 }));
  const b = document.createElement("b");
  b.textContent = text;
  el.appendChild(b);
  if (actionLabel) {
    const btn = document.createElement("button");
    btn.className = "btn sm";
    btn.textContent = actionLabel;
    btn.onclick = onAction;
    el.appendChild(btn);
  }
  return el;
}

/* ── artwork ────────────────────────────────────────────────────────────── */
export function art(id, cls = "art-xs", { round = false } = {}) {
  const wrap = document.createElement("div");
  wrap.className = `art ${cls}${round ? " round" : ""}`;
  const coversOff = document.body?.dataset.covers === "off";
  if (id && !coversOff) {
    const img = document.createElement("img");
    img.src = `/api/tracks/${id}/cover`;
    img.alt = "";
    img.loading = "lazy";
    img.decoding = "async";
    img.onerror = () => {
      img.remove();
      wrap.appendChild(icon("disc-3", { size: 16 }));
    };
    wrap.appendChild(img);
  } else {
    wrap.appendChild(icon(round ? "users" : "disc-3", { size: 16 }));
  }
  return wrap;
}

/* ── tiles ──────────────────────────────────────────────────────────────── */
export function tile(o) {
  const el = document.createElement("button");
  el.className = `tile${o.round ? " round" : ""}`;
  el.type = "button";
  el.onclick = o.onclick || null;

  const wrap = document.createElement("div");
  wrap.className = "tile-wrap";
  wrap.appendChild(art(o.id, "art-md", { round: !!o.round }));

  if (o.play) {
    const play = document.createElement("span");
    play.className = "tile-play";
    play.setAttribute("role", "button");
    play.setAttribute("aria-label", "Play");
    play.appendChild(icon("play", { size: 15, filled: true }));
    play.onclick = (e) => {
      e.stopPropagation();
      o.play();
    };
    wrap.appendChild(play);
  }

  el.appendChild(wrap);

  const b = document.createElement("b");
  b.textContent = o.title || "";
  el.appendChild(b);

  if (o.sub) {
    const s = document.createElement("small");
    s.textContent = o.sub;
    el.appendChild(s);
  }
  return el;
}

export function albumTile(a) {
  return tile({
    id: a.cover_id,
    title: a.album,
    sub: a.artist + (a.n ? ` · ${a.n}` : ""),
    onclick: () => window.App?.go("album", a.album),
    play: async () => {
      const d = await api(`album?name=${encodeURIComponent(a.album)}`);
      window.Player?.play(d.tracks, 0);
    },
  });
}

export function artistTile(a) {
  return tile({
    id: a.cover_id,
    title: a.artist,
    sub: `${a.n || 0} tracks`,
    round: true,
    onclick: () => window.App?.go("artist", a.artist),
    play: async () => {
      const d = await api(`artist?name=${encodeURIComponent(a.artist)}`);
      window.Player?.play(d.tracks, 0);
    },
  });
}

export function playlistTile(p) {
  return tile({
    id: p.cover_id,
    title: p.name,
    sub: `${p.n || 0} tracks`,
    onclick: () => window.App?.go("playlist", p.id),
    play: async () => {
      const d = await api(`playlists/${p.id}`);
      window.Player?.play(d.tracks, 0);
    },
  });
}

/* ── shelves and grids ──────────────────────────────────────────────────── */
export function shelf(title, nodes, opts = {}) {
  const section = document.createElement("section");
  section.className = "shelf";

  const head = document.createElement("div");
  head.className = "shelf-h";
  const h2 = document.createElement("h2");
  h2.textContent = title;
  head.appendChild(h2);
  if (opts.meta) {
    const m = document.createElement("span");
    m.className = "mono";
    m.textContent = opts.meta;
    head.appendChild(m);
  }
  section.appendChild(head);

  const track = document.createElement("div");
  track.className = opts.grid ? "grid" : "shelf-track";
  nodes.filter(Boolean).forEach((n) => track.appendChild(n));
  section.appendChild(track);
  return section;
}

/* ── hero ───────────────────────────────────────────────────────────────── */
export function hero(o) {
  const wrap = document.createElement("header");
  wrap.className = "hero";

  const cover = document.createElement("div");
  cover.className = `hero-art${o.round ? " round" : ""}`;
  if (o.cover && document.body?.dataset.covers !== "off") {
    const img = document.createElement("img");
    img.src = `/api/tracks/${o.cover}/cover`;
    img.alt = "";
    img.loading = "lazy";
    img.decoding = "async";
    img.onerror = () => {
      img.remove();
      cover.appendChild(icon(o.round ? "users" : "disc-3", { size: 34 }));
    };
    cover.appendChild(img);
  } else {
    cover.appendChild(icon(o.round ? "users" : "disc-3", { size: 34 }));
  }

  const info = document.createElement("div");
  info.className = "hero-info";

  if (o.kicker) {
    const k = document.createElement("span");
    k.className = "kicker";
    k.textContent = o.kicker;
    info.appendChild(k);
  }

  const h1 = document.createElement("h1");
  h1.textContent = o.title || "";
  info.appendChild(h1);

  if (o.sub) {
    const sub = document.createElement("div");
    sub.className = "hero-sub";
    const parts = Array.isArray(o.sub) ? o.sub : [o.sub];
    parts.filter(Boolean).forEach((p) => {
      const s = document.createElement("span");
      s.textContent = p;
      sub.appendChild(s);
    });
    info.appendChild(sub);
  }

  if (o.actions && o.actions.length) {
    const acts = document.createElement("div");
    acts.className = "hero-actions";
    o.actions.filter(Boolean).forEach((a) => acts.appendChild(a));
    info.appendChild(acts);
  }

  wrap.appendChild(cover);
  wrap.appendChild(info);
  return wrap;
}

export function playButtons(tracks, opts = {}) {
  const play = document.createElement("button");
  play.className = "btn solid";
  play.appendChild(icon("play", { size: 12, filled: true }));
  const label = document.createElement("span");
  label.textContent = "Play";
  play.appendChild(label);
  play.onclick = () => window.Player?.play(tracks, 0, opts);

  const shuffle = document.createElement("button");
  shuffle.className = "btn";
  shuffle.appendChild(icon("shuffle", { size: 12 }));
  const sl = document.createElement("span");
  sl.textContent = "Shuffle";
  shuffle.appendChild(sl);
  shuffle.onclick = () => window.Player?.play(tracks, 0, { shuffle: true });

  return [play, shuffle];
}

/* ── track list ─────────────────────────────────────────────────────────── */
export function trackList(tracks, opts = {}) {
  const visible = opts.hideExplicit
    ? tracks.filter((t) => !t.explicit)
    : tracks;
  const wrap = document.createElement("div");
  wrap.className = "tracks";
  if (!visible.length) {
    wrap.appendChild(empty("No tracks here", "Try a different filter."));
    return wrap;
  }
  visible.forEach((t, i) => wrap.appendChild(trackRow(t, i, visible, opts)));
  return wrap;
}

function artistChips(t) {
  const names = Array.isArray(t.artists) && t.artists.length
    ? t.artists
    : t.artist
      ? [t.artist]
      : [];
  const box = document.createDocumentFragment();
  names.forEach((name, i) => {
    if (i) box.appendChild(document.createTextNode(" · "));
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "artistchip";
    chip.textContent = name;
    chip.onclick = (e) => {
      e.stopPropagation();
      window.App?.go("artist", name);
    };
    box.appendChild(chip);
  });
  return box;
}

export function trackRow(t, i, list, opts = {}) {
  const playing = window.Player?.current?.();
  const el = document.createElement("div");
  el.className = `trow${playing && playing.id === t.id ? " now" : ""}`;
  el.dataset.id = t.id;
  el.tabIndex = 0;
  el.setAttribute("role", "button");
  el.onclick = () => window.Player?.play(list, i);
  el.onkeydown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      window.Player?.play(list, i);
    }
  };

  const idx = document.createElement("span");
  idx.className = "idx";
  idx.textContent = String(i + 1).padStart(2, "0");
  el.appendChild(idx);

  el.appendChild(art(t.id, "art-xs"));

  const meta = document.createElement("div");
  meta.className = "meta";
  const b = document.createElement("b");
  b.appendChild(document.createTextNode(t.title || "Unknown"));
  if (t.explicit) {
    const ex = document.createElement("span");
    ex.className = "ex";
    ex.textContent = "E";
    ex.title = "Explicit";
    b.appendChild(ex);
  }
  const sub = document.createElement("small");
  sub.appendChild(artistChips(t));
  meta.appendChild(b);
  meta.appendChild(sub);
  el.appendChild(meta);

  const album = document.createElement("button");
  album.className = "album";
  album.textContent = t.album || "";
  album.onclick = (e) => {
    e.stopPropagation();
    window.App?.go("album", t.album);
  };
  el.appendChild(album);

  const likes = document.createElement("span");
  likes.className = "likes";
  likes.textContent = opts.ytStats && t.yt_likes != null ? fmtCount(t.yt_likes) : "";
  el.appendChild(likes);

  const like = document.createElement("button");
  like.className = `iconbtn${t.liked ? " liked" : ""}`;
  like.dataset.like = t.id;
  like.setAttribute("aria-label", t.liked ? "Unlike" : "Like");
  like.appendChild(icon("heart", { size: 14 }));
  like.onclick = (e) => {
    e.stopPropagation();
    toggleLike(t, like);
  };
  el.appendChild(like);

  const dur = document.createElement("span");
  dur.className = "dur";
  dur.textContent = fmtTime(t.duration);
  el.appendChild(dur);

  const more = document.createElement("button");
  more.className = "iconbtn";
  more.setAttribute("aria-label", "More actions");
  more.appendChild(icon("more-vertical", { size: 15 }));
  more.onclick = (e) => {
    e.stopPropagation();
    trackMenu(more, t, opts);
  };
  el.appendChild(more);

  return el;
}

/* ── progress bar ───────────────────────────────────────────────────────── */
export function progressBar() {
  const root = document.createElement("div");
  root.className = "prog";

  const cur = document.createElement("span");
  cur.className = "prog-time";
  cur.textContent = "0:00";

  const hit = document.createElement("div");
  hit.className = "prog-hit";
  hit.setAttribute("role", "slider");
  hit.setAttribute("tabindex", "0");
  hit.setAttribute("aria-label", "Seek");
  hit.setAttribute("aria-valuemin", "0");
  hit.setAttribute("aria-valuemax", "100");
  hit.setAttribute("aria-valuenow", "0");

  const groove = document.createElement("div");
  groove.className = "prog-groove";
  const buf = document.createElement("div");
  buf.className = "prog-buf";
  const fill = document.createElement("div");
  fill.className = "prog-fill";
  const knob = document.createElement("div");
  knob.className = "prog-knob";
  groove.appendChild(buf);
  groove.appendChild(fill);
  groove.appendChild(knob);
  hit.appendChild(groove);

  const dur = document.createElement("span");
  dur.className = "prog-time right";
  dur.textContent = "0:00";

  root.appendChild(cur);
  root.appendChild(hit);
  root.appendChild(dur);

  window.Player?.bindProgress(root);
  return root;
}

/* ── like ───────────────────────────────────────────────────────────────── */
export async function toggleLike(t, btn = null) {
  try {
    const r = await api(`like/${t.id}`, "POST");
    // A queued like is replayed later, so show the flip the listener asked for.
    const liked = r.queued ? !t.liked : r.liked;
    t.liked = liked;
    if (window.Player?.queue) {
      window.Player.queue.forEach((x) => {
        if (x.id === t.id) x.liked = liked;
      });
    }
    const selector = `[data-like="${t.id}"]`;
    document.querySelectorAll(selector).forEach((b) => {
      b.classList.toggle("liked", liked);
      b.setAttribute("aria-label", liked ? "Unlike" : "Like");
    });
    btn?.classList.toggle("liked", liked);
    window.dispatchEvent(new CustomEvent("mcmusic:like", { detail: { track: t, liked } }));
    return liked;
  } catch (e) {
    toast(e.message || "Could not update like", { iconName: "triangle-alert" });
    return false;
  }
}

/* ── track menu ─────────────────────────────────────────────────────────── */
export async function trackMenu(anchor, t, opts = {}) {
  const items = [
    { label: "Play next", iconName: "list-music", fn: () => queueNext(t) },
    { label: "Add to queue", iconName: "plus", fn: () => queueAdd(t) },
    { label: "Add to playlist…", iconName: "folder-plus", fn: () => addToPlaylist(t) },
    { label: "Start radio", iconName: "radio", fn: () => startRadio(t) },
    "-",
    { label: "Go to album", iconName: "album", fn: () => window.App?.go("album", t.album) },
    { label: "Go to artist", iconName: "users", fn: () => window.App?.go("artist", t.artists?.[0] || t.artist) },
    {
      label: t.liked ? "Remove from liked" : "Like",
      iconName: "heart",
      fn: () => toggleLike(t),
    },
    { label: "Track info", iconName: "info", fn: () => trackInfo(t) },
    { label: "Open player", iconName: "tv-2", fn: () => window.App?.go("now") },
  ];

  const offline = await cache.isDownloaded(t.id);
  items.push("-", {
    label: offline ? "Remove download" : "Download offline",
    iconName: offline ? "trash-2" : "download",
    fn: async () => {
      if (offline) {
        await cache.removeDownload(t.id);
        toast("Removed offline copy");
      } else {
        toast("Downloading…", { iconName: "download" });
        const ok = await cache.downloadTrack(t);
        toast(ok ? "Available offline" : "Download failed", {
          iconName: ok ? "check" : "triangle-alert",
        });
      }
      window.App?.draw();
    },
  });

  if (opts.extra) {
    const extra = opts.extra(t);
    if (extra) items.push("-", ...(Array.isArray(extra) ? extra : [extra]));
  }

  if (window.App?.me?.is_admin) {
    items.push("-", {
      label: t.explicit ? "Mark as clean" : "Mark as explicit",
      iconName: "triangle-alert",
      fn: async () => {
        try {
          const r = await api(`tracks/${t.id}`, "PATCH", { explicit: !t.explicit });
          t.explicit = r.explicit;
          toast("Updated");
          window.App?.draw();
        } catch (e) {
          toast(e.message);
        }
      },
    });
  }

  menu(anchor, items);
}

export function queueNext(t) {
  if (!window.Player) return;
  if (!window.Player.queue.length) {
    window.Player.play([t], 0);
    return;
  }
  window.Player.add(t, { next: true });
  toast("Playing next", { iconName: "list-music" });
}

export function queueAdd(t) {
  if (!window.Player) return;
  if (!window.Player.queue.length) {
    window.Player.play([t], 0);
    return;
  }
  window.Player.add(t);
  toast("Added to queue", { iconName: "plus" });
}

export async function startRadio(t) {
  try {
    const r = await api(`radio/${t.id}`);
    window.Player?.play([t, ...(r.tracks || [])], 0);
    toast("Radio started", { iconName: "radio" });
  } catch (e) {
    toast(e.message);
  }
}

export async function addToPlaylist(t) {
  let pls = [];
  try {
    pls = (await api("playlists")).playlists || [];
  } catch (e) {
    toast(e.message);
    return;
  }

  const list = document.createElement("div");
  list.style.display = "grid";
  list.style.gap = "4px";

  const nameInput = document.createElement("input");
  nameInput.placeholder = "New playlist name";

  const createRow = document.createElement("div");
  createRow.style.cssText = "display:flex;gap:8px;margin-top:6px";
  const createBtn = document.createElement("button");
  createBtn.className = "btn sm";
  createBtn.textContent = "Create";
  createRow.appendChild(nameInput);
  createRow.appendChild(createBtn);

  const body = [list];
  if (!pls.length) {
    const p = document.createElement("p");
    p.textContent = "You have no playlists yet — name one below.";
    body.unshift(p);
  }
  body.push(createRow);

  const close = sheet("Add to playlist", ...body);

  const addTo = async (pid) => {
    try {
      await api(`playlists/${pid}/tracks`, "POST", { track_id: t.id });
      toast("Added to playlist", { iconName: "check" });
      close();
      window.App?.refreshSide?.();
    } catch (e) {
      toast(e.message);
    }
  };

  pls.forEach((p) => {
    const row = document.createElement("button");
    row.className = "qrow";
    row.appendChild(art(p.cover_id, "art-xs"));
    const meta = document.createElement("div");
    meta.className = "meta";
    const b = document.createElement("b");
    b.textContent = p.name;
    const s = document.createElement("small");
    s.textContent = `${p.n || 0} tracks`;
    meta.appendChild(b);
    meta.appendChild(s);
    row.appendChild(meta);
    row.onclick = () => addTo(p.id);
    list.appendChild(row);
  });

  createBtn.onclick = async () => {
    const name = nameInput.value.trim();
    if (!name) return;
    try {
      const p = await api("playlists", "POST", { name });
      await api(`playlists/${p.id}/tracks`, "POST", { track_id: t.id });
      toast("Playlist created", { iconName: "check" });
      close();
      window.App?.refreshSide?.();
    } catch (e) {
      toast(e.message);
    }
  };
}

export async function trackInfo(t) {
  const left = document.createElement("div");
  left.style.cssText = "display:flex;gap:12px;align-items:center";
  left.appendChild(art(t.id, "art-lg"));

  const head = document.createElement("div");
  const b = document.createElement("b");
  b.textContent = t.title || "Unknown";
  b.style.fontSize = "1rem";
  const s = document.createElement("small");
  s.appendChild(artistChips(t));
  if (t.album) s.appendChild(document.createTextNode(` · ${t.album}`));
  head.appendChild(b);
  head.appendChild(document.createElement("br"));
  head.appendChild(s);
  left.appendChild(head);

  const rows = [
    ["Length", fmtTime(t.duration)],
    ["Track", t.track_no || "—"],
    ["Year", t.year || "—"],
    ["Genre", t.genre || "—"],
    ["Explicit", t.explicit ? "Yes" : "No"],
  ];
  if (t.yt_channel) rows.push(["Channel", t.yt_channel]);
  if (t.yt_likes != null) rows.push(["YT likes", fmtCount(t.yt_likes)]);
  if (t.yt_views != null) rows.push(["YT views", fmtCount(t.yt_views)]);
  if (t.yt_date) rows.push(["Uploaded", t.yt_date]);

  const kv = document.createElement("div");
  kv.className = "kv";
  rows.forEach(([k, v]) => {
    const kk = document.createElement("span");
    kk.textContent = k;
    const vv = document.createElement("b");
    vv.textContent = String(v);
    kv.appendChild(kk);
    kv.appendChild(vv);
  });

  const nodes = [left, kv];
  if (t.yt_id) {
    const a = document.createElement("a");
    a.className = "btn sm";
    a.href = `https://www.youtube.com/watch?v=${t.yt_id}`;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.appendChild(icon("arrow-up-right", { size: 12 }));
    const label = document.createElement("span");
    label.textContent = "Open on YouTube";
    a.appendChild(label);
    a.style.justifySelf = "start";
    nodes.push(a);
  }

  sheet("Track info", ...nodes);
}

/* ── formatters ─────────────────────────────────────────────────────────── */
export function fmtTime(seconds) {
  const s = Math.max(0, Math.round(Number(seconds) || 0));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function fmtCount(n) {
  if (n == null) return "";
  const v = Number(n);
  if (!isFinite(v)) return "";
  if (v >= 1e9) return (v / 1e9).toFixed(1).replace(/\.0$/, "") + "B";
  if (v >= 1e6) return (v / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
  if (v >= 1e3) return (v / 1e3).toFixed(v >= 1e4 ? 0 : 1).replace(/\.0$/, "") + "K";
  return String(v);
}

export function fmtTotal(seconds) {
  const m = Math.round((Number(seconds) || 0) / 60);
  if (m < 60) return `${m} min`;
  return `${Math.floor(m / 60)} hr ${m % 60} min`;
}

export function fmtBytes(bytes) {
  const b = Number(bytes) || 0;
  if (b < 1024) return `${b} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let v = b / 1024;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(v >= 10 ? 0 : 1)} ${units[i]}`;
}

/* keyboard: keep one global listener for the sheet focus trap */
document.addEventListener("keydown", (e) => {
  if (e.key !== "Tab" || !openSheet) return;
  const f = openSheet.box.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  if (!f.length) return;
  const first = f[0];
  const last = f[f.length - 1];
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
});

export { $, icon };

/* ==========================================================================
   mcmusic — views
   Pure renderers. They read state from window.App / window.Player and write
   DOM into the container they are given; the router owns when that happens.
   ========================================================================== */

import { api, flushOutbox, pendingWrites } from "./api.js";
import { Auth } from "./auth.js";
import { RealGlass } from "./glass.js";
import { Gfx, GFX_LEVELS } from "./gfx.js";
import * as cache from "./cache.js";
import { icon } from "./icons.js";
import { RoturLink } from "./rotur.js";
import {
  toast, sheet, closeSheet, empty, notice, art, tile, albumTile, artistTile,
  playlistTile, shelf, hero, playButtons, trackList, progressBar, toggleLike,
  startRadio, fmtTime, fmtCount, fmtTotal, fmtBytes,
} from "./ui.js";

const app = () => window.App;
const player = () => window.Player;

function heading(text, meta, actions = []) {
  const ph = document.createElement("div");
  ph.className = "ph";
  const left = document.createElement("div");
  const h1 = document.createElement("h1");
  h1.className = "big";
  h1.textContent = text;
  left.appendChild(h1);
  if (meta) {
    const m = document.createElement("div");
    m.className = "ph-meta";
    m.textContent = meta;
    left.appendChild(m);
  }
  ph.appendChild(left);
  if (actions.length) {
    const acts = document.createElement("div");
    acts.style.cssText = "display:flex;gap:8px;flex-wrap:wrap";
    actions.filter(Boolean).forEach((a) => acts.appendChild(a));
    ph.appendChild(acts);
  }
  return ph;
}

function sumDur(tracks) {
  return tracks.reduce((a, t) => a + (Number(t.duration) || 0), 0);
}

/** Keep a whole album, artist or playlist on the device. */
function downloadAllButton(tracks, label = "Download") {
  const b = document.createElement("button");
  b.className = "btn";
  b.type = "button";
  b.appendChild(icon("download", { size: 12 }));
  const span = document.createElement("span");
  span.textContent = label;
  b.appendChild(span);
  b.onclick = async () => {
    const list = (tracks || []).filter((t) => t && t.id);
    if (!list.length) return;
    b.disabled = true;
    let last = 0;
    const done = await cache.downloadMany(list, (n, total) => {
      const now = Date.now();
      if (now - last > 800) {
        last = now;
        span.textContent = `${n}/${total}`;
      }
    });
    span.textContent = label;
    b.disabled = false;
    toast(
      done ? `${done} of ${list.length} songs saved for offline listening` : "Couldn’t download those songs right now",
      { iconName: done ? "check" : "triangle-alert" }
    );
    if (app()?.view === "downloads") app()?.draw();
  };
  return b;
}

/** Queue a collection on the server for download, not just this browser. */
function queueServerButton(kind, id, label = "Queue on server") {
  const b = document.createElement("button");
  b.className = "btn";
  b.type = "button";
  b.appendChild(icon("download", { size: 12 }));
  const span = document.createElement("span");
  span.textContent = label;
  b.appendChild(span);
  b.onclick = async () => {
    b.disabled = true;
    try {
      const body = { kind };
      if (id != null) body.id = Number(id);
      const r = await api("download/collection", "POST", body);
      toast(
        r.queued
          ? `Queued ${r.queued} download${r.queued === 1 ? "" : "s"}`
          : "Nothing new to download"
      );
    } catch (e) {
      toast(e.message);
    }
    b.disabled = false;
  };
  return b;
}

/* ── home ───────────────────────────────────────────────────────────────── */
async function home(container) {
  const d = await api("home");
  const sections = d.sections || [];
  const albums = d.albums || [];

  if (!sections.length && !albums.length) {
    container.appendChild(
      empty(
        "Your library is waiting for its first song",
        "Add music by requesting a YouTube video or playlist, and it’ll show up here once it’s ready.",
        { iconName: "library", action: { label: "Add some music", fn: () => app()?.navTo("requests") } }
      )
    );
    return;
  }

  const hour = new Date().getHours();
  const greet = hour < 5 ? "Still awake" : hour < 12 ? "Good morning"
    : hour < 18 ? "Good afternoon" : "Good evening";

  const unique = new Map();
  sections.forEach((s) => (s.tracks || []).forEach((t) => unique.set(t.id, t)));
  const allTracks = [...unique.values()];

  const lead = document.createElement("div");
  lead.className = "home-lead";
  const leadCopy = document.createElement("div");
  const h = document.createElement("h1");
  h.className = "big";
  const name = app()?.me?.username || "there";
  h.textContent = `${greet}, ${name}`;
  const sub = document.createElement("p");
  sub.className = "home-sub";
  const bits = [`${allTracks.length} ${allTracks.length === 1 ? "song" : "songs"}`];
  if (albums.length) bits.push(`${albums.length} ${albums.length === 1 ? "album" : "albums"}`);
  sub.textContent = `You’ve got ${bits.join(" and ")} in your library. Ready to press play?`;
  leadCopy.appendChild(h);
  leadCopy.appendChild(sub);
  const shuffle = document.createElement("button");
  shuffle.className = "btn ghost";
  shuffle.type = "button";
  shuffle.appendChild(icon("shuffle", { size: 13 }));
  const shuffleLabel = document.createElement("span");
  shuffleLabel.textContent = "Shuffle all songs";
  shuffle.appendChild(shuffleLabel);
  shuffle.onclick = () => {
    const list = [...allTracks];
    for (let i = list.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [list[i], list[j]] = [list[j], list[i]];
    }
    if (list.length) player()?.play(list, 0);
  };
  lead.appendChild(leadCopy);
  lead.appendChild(shuffle);
  container.appendChild(lead);

  const summary = document.createElement("div");
  summary.className = "home-summary";
  [
    ["music", `${allTracks.length} songs`],
    ["disc-3", `${albums.length} albums`],
    ["list-music", `${sections.length} mixes`],
  ].forEach(([ic, label]) => {
    const chip = document.createElement("span");
    chip.className = "home-chip";
    chip.appendChild(icon(ic, { size: 13 }));
    const t = document.createElement("span");
    t.textContent = label;
    chip.appendChild(t);
    summary.appendChild(chip);
  });
  container.appendChild(summary);

  const hideEx = !!app()?.set?.hide_explicit;
  const first = sections.find((s) => (s.tracks || []).length);
  if (first) {
    const picks = first.tracks.slice(0, 6);
    const quickLabel = document.createElement("div");
    quickLabel.className = "quick-label";
    quickLabel.textContent = "Pick up where you left off";
    container.appendChild(quickLabel);
    const quick = document.createElement("div");
    quick.className = "quick";
    picks.forEach((t, i) => {
      const row = document.createElement("button");
      row.className = "qk";
      row.type = "button";
      row.appendChild(art(t.id, "art-xs"));
      const b = document.createElement("b");
      b.textContent = t.title;
      row.appendChild(b);
      const play = document.createElement("span");
      play.className = "iconbtn";
      play.appendChild(icon("play", { size: 13, filled: true }));
      row.appendChild(play);
      row.onclick = () => player()?.play(picks, i);
      quick.appendChild(row);
    });
    container.appendChild(quick);
  }

  sections.forEach((s) => {
    let tracks = s.tracks || [];
    if (hideEx) tracks = tracks.filter((t) => !t.explicit);
    if (!tracks.length) return;
    const nodes = tracks.map((t) =>
      tile({
        id: t.id,
        title: t.title,
        sub: t.artist,
        onclick: () => player()?.play(tracks, tracks.indexOf(t)),
        play: () => player()?.play(tracks, tracks.indexOf(t)),
      })
    );
    container.appendChild(shelf(s.title, nodes, { meta: `${nodes.length}` }));
  });

  if (albums.length) {
    container.appendChild(
      shelf("Recent albums", albums.map(albumTile), { grid: true })
    );
  }
}

/* ── search ─────────────────────────────────────────────────────────────── */
async function search(container) {
  const box = document.createElement("div");
  box.id = "sres";
  container.appendChild(box);
  await renderSearch(box, app()?.q || "");
}

export async function renderSearch(box, q) {
  if (!box) return;
  const query = (q || "").trim();
  if (!query) {
    box.replaceChildren(
      empty("Find something to play", "Search by song, album, or artist.", { iconName: "search" })
    );
    return;
  }

  const seq = (renderSearch._seq = (renderSearch._seq || 0) + 1);
  try {
    const d = await api(`search?q=${encodeURIComponent(query)}`);
    if (seq !== renderSearch._seq) return;

    const hideEx = !!app()?.set?.hide_explicit;
    const tracks = hideEx ? (d.tracks || []).filter((t) => !t.explicit) : d.tracks || [];

    if (!tracks.length && !(d.albums || []).length && !(d.artists || []).length) {
      box.replaceChildren(
        empty("No matches", `We couldn’t find anything for “${query}”. Try a different name or spelling.`, { iconName: "search" })
      );
      return;
    }

    box.replaceChildren();
    if ((d.artists || []).length) {
      box.appendChild(shelf("Artists", d.artists.map(artistTile), { meta: `${d.artists.length}` }));
    }
    if ((d.albums || []).length) {
      box.appendChild(shelf("Albums", d.albums.map(albumTile), { meta: `${d.albums.length}` }));
    }
    if (tracks.length) {
      box.appendChild(
        heading("Tracks", `${tracks.length} match${tracks.length === 1 ? "" : "es"}`)
      );
      box.appendChild(trackList(tracks, { ytStats: app()?.set?.yt_stats }));
    }
  } catch (e) {
    box.replaceChildren(
      empty("Search failed", e.message, { iconName: "wifi-off" })
    );
  }
}

/* ── library ────────────────────────────────────────────────────────────── */
async function library(container) {
  const state = app();
  const tabs = document.createElement("div");
  tabs.className = "seg";
  [["songs", "Songs"], ["albums", "Albums"], ["artists", "Artists"], ["playlists", "Playlists"], ["liked", "Liked"]].forEach(([k, label]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = state?.lib === k ? "on" : "";
    b.textContent = label;
    b.onclick = () => {
      if (state) state.lib = k;
      app()?.draw();
    };
    tabs.appendChild(b);
  });

  container.appendChild(heading("Your library", "Everything in your collection, in one place", [tabs]));

  if (state?.lib === "albums") {
    const d = await api("albums");
    const grid = document.createElement("div");
    grid.className = "grid";
    (d.albums || []).forEach((a) => grid.appendChild(albumTile(a)));
    container.appendChild(grid);
    return;
  }

  if (state?.lib === "artists") {
    const d = await api("artists");
    const grid = document.createElement("div");
    grid.className = "grid";
    (d.artists || []).forEach((a) => grid.appendChild(artistTile(a)));
    container.appendChild(grid);
    return;
  }

  if (state?.lib === "playlists") {
    await playlists(container);
    return;
  }

  if (state?.lib === "liked") {
    await likes(container);
    return;
  }

  const d = await api("tracks?limit=2000");
  const all = d.tracks || [];

  const out = document.createElement("div");
  const paint = () => {
    const list = [...all];
    const sort = app()?.sort || "artist";
    if (sort === "title") list.sort((a, b) => (a.title || "").localeCompare(b.title || ""));
    else if (sort === "recent") list.sort((a, b) => (b.added || 0) - (a.added || 0));
    else if (sort === "popular") list.sort((a, b) => (b.yt_likes || 0) - (a.yt_likes || 0));
    else {
      list.sort((a, b) => {
        const aw = (a.artist || "").localeCompare(b.artist || "");
        if (aw !== 0) return aw;
        return (a.album || "").localeCompare(b.album || "");
      });
    }
    out.replaceChildren(
      list.length
        ? trackList(list, { ytStats: app()?.set?.yt_stats })
        : empty("No songs in your library yet", "Add some music and it’ll show up here, ready to play.", {
            iconName: "music",
            action: { label: "Add music", fn: () => app()?.navTo("requests") },
          })
    );
  };

  const ctrl = document.createElement("div");
  ctrl.style.cssText = "display:flex;align-items:center;gap:10px;margin:0 0 10px";
  const count = document.createElement("span");
  count.className = "ph-meta";
  count.textContent = `${all.length} tracks · ${fmtTotal(sumDur(all))}`;
  ctrl.appendChild(count);

  const spacer = document.createElement("span");
  spacer.style.flex = "1";
  ctrl.appendChild(spacer);

  const sel = document.createElement("select");
  sel.style.width = "auto";
  [["artist", "Artist"], ["title", "Title"], ["recent", "Recently added"], ["popular", "YouTube likes"]]
    .forEach(([v, label]) => {
      const o = document.createElement("option");
      o.value = v;
      o.textContent = `Sort · ${label}`;
      o.selected = (app()?.sort || "artist") === v;
      sel.appendChild(o);
    });
  sel.onchange = (e) => {
    if (app()) app().sort = e.target.value;
    paint();
  };
  ctrl.appendChild(sel);

  container.appendChild(ctrl);
  container.appendChild(out);
  paint();
}

/* ── album / artist ─────────────────────────────────────────────────────── */
async function album(container, name) {
  const d = await api(`album?name=${encodeURIComponent(name)}`);
  const tracks = d.tracks || [];
  const artist = tracks[0]?.artist || "";
  const years = [...new Set(tracks.map((t) => t.year).filter(Boolean))];
  const genres = [...new Set(tracks.map((t) => t.genre).filter(Boolean))];
  const actions = tracks.length ? [...playButtons(tracks), downloadAllButton(tracks)] : [];
  if (artist) {
    const go = document.createElement("button");
    go.type = "button";
    go.className = "btn";
    const lbl = document.createElement("span");
    lbl.textContent = artist;
    go.appendChild(lbl);
    go.onclick = () => window.App?.go("artist", tracks[0]?.artists?.[0] || artist);
    actions.push(go);
  }
  container.appendChild(
    hero({
      cover: tracks[0]?.id,
      kicker: "Album",
      title: name,
      sub: [
        `${tracks.length} tracks`,
        fmtTotal(sumDur(tracks)),
        artist,
        years.join(" / "),
        genres.join(", "),
      ].filter(Boolean),
      actions,
    })
  );
  container.appendChild(trackList(tracks, { ytStats: app()?.set?.yt_stats }));
}

async function artist(container, name) {
  const d = await api(`artist?name=${encodeURIComponent(name)}`);
  const tracks = d.tracks || [];
  const byAlbum = new Map();
  tracks.forEach((t) => {
    const hit = byAlbum.get(t.album);
    if (hit) hit.n += 1;
    else byAlbum.set(t.album, { album: t.album, artist: t.artist, n: 1, cover_id: t.id });
  });
  const albums = [...byAlbum.values()];
  container.appendChild(
    hero({
      cover: tracks[0]?.id,
      kicker: "Artist",
      title: name,
      sub: [
        `${tracks.length} tracks`,
        fmtTotal(sumDur(tracks)),
        `${albums.length} album${albums.length === 1 ? "" : "s"}`,
      ],
      round: true,
      actions: tracks.length ? [...playButtons(tracks), downloadAllButton(tracks)] : [],
    })
  );
  if (albums.length > 1) {
    container.appendChild(shelf("Albums", albums.map(albumTile), { grid: true }));
  }
  container.appendChild(trackList(tracks, { ytStats: app()?.set?.yt_stats }));
}

/* ── likes ──────────────────────────────────────────────────────────────── */
async function likes(container) {
  const d = await api("likes");
  const tracks = d.tracks || [];
  if (!tracks.length) {
    container.appendChild(
      heading("Liked songs", null, [queueServerButton("likes")])
    );
    container.appendChild(
      empty("No liked songs yet", "Tap the heart on any song to save it here for later.", {
        iconName: "heart",
        action: { label: "Browse your library", fn: () => app()?.navTo("library") },
      })
    );
    return;
  }
  container.appendChild(
    hero({
      cover: tracks[0].id,
      kicker: "Collection",
      title: "Liked songs",
      sub: [`${tracks.length} tracks`, fmtTotal(sumDur(tracks))],
      actions: [
        ...playButtons(tracks, { shuffle: true }),
        downloadAllButton(tracks),
        queueServerButton("likes"),
      ],
    })
  );
  container.appendChild(trackList(tracks, { ytStats: app()?.set?.yt_stats }));
}

/* ── playlists ──────────────────────────────────────────────────────────── */
async function playlists(container) {
  const d = await api("playlists");
  const pls = d.playlists || [];

  const newBtn = document.createElement("button");
  newBtn.className = "btn solid";
  newBtn.appendChild(icon("plus", { size: 12 }));
  const lbl = document.createElement("span");
  lbl.textContent = "New playlist";
  newBtn.appendChild(lbl);
  newBtn.onclick = newPlaylist;

  container.appendChild(heading("Playlists", `${pls.length} total`, [newBtn]));

  if (!pls.length) {
    container.appendChild(
      empty("No playlists yet", "Make a playlist for a mood, a road trip, or anything you like — then add songs from any track menu.", {
        iconName: "folder-plus",
        action: { label: "Create your first playlist", fn: newPlaylist },
      })
    );
    return;
  }

  const grid = document.createElement("div");
  grid.className = "grid";
  pls.forEach((p) => grid.appendChild(playlistTile(p)));
  container.appendChild(grid);
}

export function newPlaylist() {
  const input = document.createElement("input");
  input.placeholder = "Playlist name";
  input.maxLength = 100;

  const create = async () => {
    const name = input.value.trim();
    if (!name) return;
    try {
      const p = await api("playlists", "POST", { name });
      closeSheet();
      await app()?.refreshSide();
      app()?.go("playlist", p.id);
    } catch (e) {
      toast(e.message);
    }
  };

  input.onkeydown = (e) => {
    if (e.key === "Enter") create();
  };

  const btn = document.createElement("button");
  btn.className = "btn solid";
  btn.textContent = "Create";
  btn.onclick = create;

  sheet("New playlist", input, btn);
  setTimeout(() => input.focus(), 60);
}

async function playlist(container, id) {
  const p = await api(`playlists/${id}`);
  const tracks = p.tracks || [];

  const dlPl = document.createElement("button");
  dlPl.className = "btn";
  dlPl.appendChild(icon("download", { size: 12 }));
  const dlPlLabel = document.createElement("span");
  dlPlLabel.textContent = "Download";
  dlPl.appendChild(dlPlLabel);
  dlPl.onclick = async () => {
    try {
      const r = await api("download/collection", "POST", {
        kind: p.name === "Faves" ? "faves" : "playlist",
        id: Number(id),
      });
      toast(`Queued ${r.queued} download${r.queued === 1 ? "" : "s"}`);
    } catch (e) {
      toast(e.message);
    }
  };

  const rename = document.createElement("button");
  rename.className = "btn";
  rename.textContent = "Rename";
  rename.onclick = () => {
    const input = document.createElement("input");
    input.value = p.name;
    const save = document.createElement("button");
    save.className = "btn solid";
    save.textContent = "Save";
    const close = sheet("Rename playlist", input, save);
    save.onclick = async () => {
      try {
        await api(`playlists/${id}`, "PATCH", { name: input.value });
        close();
        await app()?.refreshSide();
        app()?.draw();
      } catch (e) {
        toast(e.message);
      }
    };
  };

  const del = document.createElement("button");
  del.className = "btn danger";
  del.appendChild(icon("trash-2", { size: 12 }));
  const dl = document.createElement("span");
  dl.textContent = "Delete";
  del.appendChild(dl);
  del.onclick = async () => {
    if (!confirm(`Delete “${p.name}”? This cannot be undone.`)) return;
    try {
      await api(`playlists/${id}`, "DELETE");
      await app()?.refreshSide();
      app()?.navTo("playlists");
    } catch (e) {
      toast(e.message);
    }
  };

  container.appendChild(
    hero({
      cover: tracks[0]?.id,
      kicker: "Playlist",
      title: p.name,
      sub: [`${tracks.length} tracks`, fmtTotal(sumDur(tracks))],
      actions: [
        ...(tracks.length ? playButtons(tracks) : []),
        tracks.length ? downloadAllButton(tracks) : null,
        tracks.length ? dlPl : null,
        rename,
        del,
      ].filter(Boolean),
    })
  );

  if (!tracks.length) {
    container.appendChild(
      empty("This playlist is empty", "Find a song you love, open its menu, and choose “Add to playlist”.", {
        iconName: "folder-plus",
        action: { label: "Browse your library", fn: () => app()?.navTo("library") },
      })
    );
    return;
  }

  container.appendChild(
    trackList(tracks, {
      ytStats: app()?.set?.yt_stats,
      extra: (t) => ({
        label: "Remove from playlist",
        iconName: "x",
        danger: true,
        fn: async () => {
          try {
            await api(`playlists/${id}/tracks/${t.id}`, "DELETE");
            await app()?.refreshSide();
            app()?.draw();
          } catch (e) {
            toast(e.message);
          }
        },
      }),
    })
  );
}

/* ── requests ───────────────────────────────────────────────────────────── */
async function requests(container, embedded = false) {
  const input = document.createElement("input");
  input.placeholder = "Paste a YouTube video or playlist link…";

  const list = document.createElement("div");

  const send = async () => {
    const url = input.value.trim();
    if (!url) return;
    try {
      const r = await api("requests", "POST", { url });
      input.value = "";
      toast(r.status === "pending" ? "Request sent — it’ll be reviewed soon" : "Got it — your music will start downloading", {
        iconName: "download",
      });
      paint();
    } catch (e) {
      toast(e.message);
    }
  };

  input.onkeydown = (e) => {
    if (e.key === "Enter") send();
  };

  const btn = document.createElement("button");
  btn.className = "btn solid";
  btn.appendChild(icon("download", { size: 12 }));
  const bl = document.createElement("span");
  bl.textContent = "Request";
  btn.appendChild(bl);
  btn.onclick = send;

  const bar = document.createElement("div");
  bar.style.cssText = "display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap";
  bar.appendChild(input);
  bar.appendChild(btn);
  input.style.flex = "1";

  if (!embedded) container.appendChild(heading("Add music", "Paste a link and we’ll download it in the background"));
  container.appendChild(bar);
  container.appendChild(list);

  const paint = async () => {
    let r;
    try {
      r = await api("requests");
    } catch (e) {
      list.replaceChildren(empty("Could not load requests", e.message, { iconName: "wifi-off" }));
      return;
    }
    if (app()?.view !== "requests") return;
    list.replaceChildren();

    if (!(r.requests || []).length) {
      list.appendChild(empty("No requests yet", "Paste a YouTube link above and we’ll take it from here.", { iconName: "download" }));
      return;
    }

    r.requests.forEach((q) => {
      const row = document.createElement("div");
      row.className = "req";

      const meta = document.createElement("div");
      meta.className = "meta";
      const b = document.createElement("b");
      b.textContent = q.url;
      const s = document.createElement("small");
      s.textContent = `${q.username} · ${new Date((q.created || 0) * 1000).toLocaleString()}`;
      meta.appendChild(b);
      meta.appendChild(s);
      row.appendChild(meta);

      const st = document.createElement("span");
      st.className = `st ${q.status}`;
      st.textContent = q.status;
      row.appendChild(st);

      if (r.is_admin && ["pending", "failed"].includes(q.status)) {
        const acts = document.createElement("div");
        acts.style.cssText = "display:flex;gap:4px";
        const ok = document.createElement("button");
        ok.className = "btn sm";
        ok.textContent = "Approve";
        ok.onclick = async () => {
          try {
            await api(`requests/${q.id}/approve`, "POST");
            paint();
          } catch (e) { toast(e.message); }
        };
        const no = document.createElement("button");
        no.className = "btn ghost sm";
        no.textContent = "Reject";
        no.onclick = async () => {
          try {
            await api(`requests/${q.id}/reject`, "POST");
            paint();
          } catch (e) { toast(e.message); }
        };
        acts.appendChild(ok);
        acts.appendChild(no);
        row.appendChild(acts);
      }

      list.appendChild(row);
    });
  };

  await paint();
  app().timer = setInterval(paint, 5000);
}

/* ── now playing ────────────────────────────────────────────────────────── */
function now(container) {
  const t = player()?.current();
  if (!t) {
    container.appendChild(heading("Now playing"));
    container.appendChild(
      empty("Nothing’s playing right now", "Pick a song from your library and it’ll show up here.", {
        iconName: "disc-3",
        action: { label: "Browse your library", fn: () => app()?.navTo("library") },
      })
    );
    return;
  }

  const wrap = document.createElement("div");
  wrap.className = "now";

  const top = document.createElement("div");
  top.className = "now-top";

  const cover = document.createElement("div");
  cover.className = "now-art";
  const img = document.createElement("img");
  if (document.body?.dataset.covers !== "off") img.src = `/api/tracks/${t.id}/cover`;
  img.alt = "";
  img.loading = "lazy";
  img.decoding = "async";
  img.onerror = () => {
    img.remove();
    cover.appendChild(icon("disc-3", { size: 42 }));
  };
  cover.appendChild(img);

  const meta = document.createElement("div");
  meta.className = "now-meta";
  const kick = document.createElement("span");
  kick.className = "kicker";
  kick.textContent = player()?.playing ? "Now playing" : "Paused";
  const h1 = document.createElement("h1");
  h1.textContent = t.title || "Unknown";
  const sub = document.createElement("div");
  sub.className = "now-sub";
  sub.textContent = [t.artist, t.album].filter(Boolean).join(" · ");
  meta.appendChild(kick);
  meta.appendChild(h1);
  meta.appendChild(sub);

  const controls = document.createElement("div");
  controls.className = "now-controls";
  controls.appendChild(deckButton("shuffle", () => app()?.toggleShuffle()));
  controls.appendChild(deckButton("skip-back", () => player()?.prev()));
  const playBtn = document.createElement("button");
  playBtn.className = "iconbtn play";
  playBtn.setAttribute("aria-label", "Play or pause");
  playBtn.appendChild(icon(player()?.playing ? "pause" : "play", { size: 18, filled: true }));
  playBtn.onclick = () => player()?.toggle();
  controls.appendChild(playBtn);
  controls.appendChild(deckButton("skip-forward", () => player()?.next()));
  controls.appendChild(deckButton("repeat", () => app()?.cycleRepeat()));

  meta.appendChild(controls);
  top.appendChild(cover);
  top.appendChild(meta);
  wrap.appendChild(top);
  wrap.appendChild(progressBar());

  const up = player()?.upNext(12) || [];
  if (up.length) {
    const next = document.createElement("div");
    next.className = "now-next";
    next.appendChild(heading("Up next", `${up.length} queued`));
    next.appendChild(trackList(up, { ytStats: app()?.set?.yt_stats }));
    wrap.appendChild(next);
  }

  container.appendChild(wrap);
}

function deckButton(name, fn) {
  const b = document.createElement("button");
  b.className = "iconbtn";
  b.appendChild(icon(name, { size: 18 }));
  b.onclick = fn;
  return b;
}

/* ── downloads · requests ───────────────────────────────────────────────── */
async function downloads(container) {
  const state = app();
  const tabs = document.createElement("div");
  tabs.className = "seg";
  [["files", "Downloads"], ["requests", "Requests"]].forEach(([k, label]) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = (state?.dl || "files") === k ? "on" : "";
    b.textContent = label;
    b.onclick = () => {
      if (state) state.dl = k;
      app()?.draw();
    };
    tabs.appendChild(b);
  });

  container.appendChild(heading("Downloads", "Music saved on this device and requests from the server", [tabs]));

  const body = document.createElement("div");
  container.appendChild(body);

  if ((state?.dl || "files") === "requests") {
    await requests(body, true);
    return;
  }
  await downloadsBody(body);
}

async function downloadsBody(container) {
  const [list, st] = await Promise.all([cache.listDownloads(), cache.stats()]);
  const total = list.reduce((a, d) => a + (d.bytes || 0), 0);

  const keep = document.createElement("button");
  keep.className = "btn";
  keep.textContent = st.persisted ? "Storage persistent" : "Keep offline";
  keep.disabled = st.persisted;
  keep.onclick = async () => {
    const ok = await cache.requestPersistence();
    toast(ok ? "Storage is now persistent" : "The browser declined persistence");
    app()?.draw();
  };

  const clear = document.createElement("button");
  clear.className = "btn danger";
  clear.appendChild(icon("trash-2", { size: 12 }));
  const cl = document.createElement("span");
  cl.textContent = "Clear all";
  clear.appendChild(cl);
  clear.onclick = async () => {
    if (!list.length) return;
    if (!confirm("Remove every downloaded track from this device?")) return;
    const n = await cache.clearDownloads();
    toast(`Freed ${n} download${n === 1 ? "" : "s"}`, { iconName: "trash-2" });
    app()?.draw();
  };

  container.appendChild(heading("Saved on this device", `${list.length} song${list.length === 1 ? "" : "s"} · ${fmtBytes(total)}`, [keep, clear]));

  if (!list.length) {
    container.appendChild(
      empty("No offline music yet", "Open the ⋮ menu on any song to save a copy to this device for listening without internet.", {
        iconName: "download",
        action: { label: "Browse your library", fn: () => app()?.navTo("library") },
      })
    );
    return;
  }

  const panel = document.createElement("div");
  panel.className = "panel";
  const used = document.createElement("span");
  used.className = "ph-meta";
  used.textContent = `${list.length} tracks`;
  panel.appendChild(
    row(
      "Device storage",
      `${fmtBytes(st.bytes)} used of ${fmtBytes(st.quota)}${st.persisted ? " · persistent" : ""}`,
      used
    )
  );
  container.appendChild(panel);

  const tracks = list.map((d) => ({
    id: d.id, title: d.title, artist: d.artist, album: d.album, duration: d.duration,
  }));
  container.appendChild(
    trackList(tracks, {
      ytStats: app()?.set?.yt_stats,
      extra: (t) => ({
        label: "Remove download",
        iconName: "trash-2",
        danger: true,
        fn: async () => {
          await cache.removeDownload(t.id);
          toast("Removed from offline");
          app()?.draw();
        },
      }),
    })
  );
}

/** Explain the activity toggle in terms of what the server can actually do. */
function discordPresenceHint(presence) {
  if (!presence) return "Shows what you're playing in your Discord profile";
  if (!presence.configured) {
    return "Needs a Discord application id on the server (DISCORD_CLIENT_ID is enough)";
  }
  if (!presence.available) {
    return "The Discord desktop app has to run on the server — it isn't running right now";
  }
  return "Shows what you're playing in your Discord profile, with a link to the track";
}

/* ── settings ───────────────────────────────────────────────────────────── */
const THEMES = [
  ["dusk", "Night"],
  ["paper", "Paper"],
  ["ink", "Ink"],
  ["tide", "Tide"],
  ["copper", "Copper"],
  ["forest", "Forest"],
  ["rose", "Rose"],
  ["auto", "Auto"],
];

const ACCENTS = ["#b080ea", "#9a7cf0", "#d29cf0", "#79d8a5", "#77cfa3", "#ecc665", "#ea90b8", "#e8737a", "#89cee1", "#f2edf7"];

async function settings(container) {
  const state = app();
  const s = state?.set || {};
  const me = state?.me;

  container.appendChild(heading("Settings", "Personalise how mcmusic looks and sounds"));

  /* appearance */
  const p1 = document.createElement("div");
  p1.className = "panel";
  p1.appendChild(Object.assign(document.createElement("h2"), { textContent: "Appearance" }));

  const themes = document.createElement("div");
  themes.className = "themes";
  THEMES.forEach(([key, label]) => {
    const card = document.createElement("button");
    card.className = `theme-card${s.theme === key ? " sel" : ""}`;
    card.type = "button";
    card.setAttribute("aria-label", `${label} theme`);
    const swatch = document.createElement("i");
    swatch.className = `swatch-preview th-${key}`;
    const span = document.createElement("span");
    span.textContent = label;
    card.appendChild(swatch);
    card.appendChild(span);
    card.onclick = () => {
      app()?.setPref("theme", key);
      themes.querySelectorAll(".theme-card").forEach((c) => c.classList.remove("sel"));
      card.classList.add("sel");
    };
    themes.appendChild(card);
  });
  p1.appendChild(themes);

  p1.appendChild(
    row("Accent colour", "Pick a colour for controls and focus", accentPicker(s.accent, (v) => app()?.setPref("accent", v)))
  );

  p1.appendChild(
    row("Density", "Tighter rows, same information", segmented(
      [["comfy", "Comfortable"], ["compact", "Compact"]],
      s.density,
      (v) => app()?.setPref("density", v)
    ))
  );

  p1.appendChild(
    row("Surface style", "Choose the feel of panels and chrome", segmented(
      [["glass", "Glass"], ["metal", "Metal"], ["solid", "Solid"], ["plane", "Plane"]],
      s.material || "plane",
      (v) => app()?.setPref("material", v)
    ))
  );

  p1.appendChild(gfxControl());

  const glassMode = s.real_glass || "auto";
  const glassRow = row(
    "Real glass",
    glassMode === "on" && !RealGlass.supported
      ? "Not supported on this browser"
      : "Uses extra GPU. Falls back to simple blur if your browser can't do it.",
    segmented(
      [["auto", "Auto"], ["on", "On"], ["off", "Off"]],
      glassMode,
      async (v) => {
        await app()?.setPref("real_glass", v);
        const hint = glassRow.querySelector("small");
        if (hint) {
          hint.textContent = v === "on" && !RealGlass.supported
            ? "Not supported on this browser"
            : "Uses extra GPU. Falls back to simple blur if your browser can't do it.";
        }
      }
    )
  );
  p1.appendChild(glassRow);

  p1.appendChild(row("Cover art", "Hide artwork to load faster", toggle(s.covers, (v) => app()?.setPref("covers", v))));
  container.appendChild(p1);

  /* playback */
  const p2 = document.createElement("div");
  p2.className = "panel";
  p2.appendChild(Object.assign(document.createElement("h2"), { textContent: "Playback" }));
  p2.appendChild(row("Autoplay", "Keep similar tracks playing after the queue",
    toggle(s.autoplay, (v) => app()?.setPref("autoplay", v))));
  p2.appendChild(row("Hide explicit tracks", "Skip tracks marked explicit",
    toggle(s.hide_explicit, async (v) => {
      await app()?.setPref("hide_explicit", v);
      app()?.draw();
    })));
  p2.appendChild(row("Show YouTube stats", "Show likes beside tracks",
    toggle(s.yt_stats, async (v) => {
      await app()?.setPref("yt_stats", v);
      app()?.draw();
    })));
  p2.appendChild(row("Remember volume", null,
    toggle(s.remember_volume, (v) => app()?.setPref("remember_volume", v))));
  p2.appendChild(row("Private session", "Don’t record plays for recommendations",
    toggle(s.private, (v) => app()?.setPref("private", v))));
  container.appendChild(p2);

  /* offline + updates */
  const p3 = document.createElement("div");
  p3.className = "panel";
  p3.appendChild(Object.assign(document.createElement("h2"), { textContent: "Offline and updates" }));

  p3.appendChild(row("Prefetch queued audio", "Cache the next tracks for gapless, offline playback",
    toggle(s.prefetch, (v) => app()?.setPref("prefetch", v))));

  const usage = document.createElement("div");
  usage.className = "prow";
  const left = document.createElement("div");
  const ub = document.createElement("b");
  ub.textContent = "Offline storage";
  const us = document.createElement("small");
  us.textContent = "Checking…";
  left.appendChild(ub);
  left.appendChild(us);
  usage.appendChild(left);
  const clearBtn = document.createElement("button");
  clearBtn.className = "btn ghost sm";
  clearBtn.textContent = "Clear";
  clearBtn.onclick = async () => {
    await cache.clearMedia();
    toast("Offline audio cleared", { iconName: "trash-2" });
    app()?.draw();
  };
  usage.appendChild(clearBtn);
  p3.appendChild(usage);

  cache.stats().then((st) => {
    us.textContent = `${st.audio} cached track${st.audio === 1 ? "" : "s"} · ${fmtBytes(st.bytes)}` +
      (st.persisted ? " · persistent" : "");
    if (!st.persisted && navigator.storage?.persist) {
      const keep = document.createElement("button");
      keep.className = "btn ghost sm";
      keep.textContent = "Keep offline";
      keep.onclick = async () => {
        const ok = await cache.requestPersistence();
        toast(ok ? "Storage is now persistent" : "The browser declined persistence");
        app()?.draw();
      };
      usage.appendChild(keep);
    }
  }).catch(() => { us.textContent = "Unavailable"; });

  const pending = document.createElement("div");
  pending.className = "prow";
  const pleft = document.createElement("div");
  const pb = document.createElement("b");
  pb.textContent = "Pending changes";
  const ps = document.createElement("small");
  ps.textContent = "Checking…";
  pleft.appendChild(pb);
  pleft.appendChild(ps);
  pending.appendChild(pleft);

  const syncBtn = document.createElement("button");
  syncBtn.className = "btn ghost sm";
  syncBtn.textContent = "Sync now";
  syncBtn.disabled = true;
  pending.appendChild(syncBtn);
  p3.appendChild(pending);

  const refreshPending = async () => {
    const n = await pendingWrites();
    ps.textContent = n
      ? `${n} change${n === 1 ? "" : "s"} waiting for a connection`
      : "Everything is saved";
    syncBtn.disabled = n === 0 || !navigator.onLine;
  };
  const refreshQuietly = () => { refreshPending().catch(() => {}); };

  // The queue can change while this panel is on screen (a sync finishing, a
  // tab going offline), so keep the row live. The listeners remove themselves
  // once the view has been replaced, so redraws cannot pile them up.
  const watched = ["mc:queued", "mc:synced", "mc:syncfail", "online", "offline"];
  const stopWatching = () => {
    watched.forEach((name) => window.removeEventListener(name, onQueueChange));
  };
  const onQueueChange = () => {
    if (!pending.isConnected) {
      stopWatching();
      return;
    }
    refreshQuietly();
  };
  watched.forEach((name) => window.addEventListener(name, onQueueChange));

  syncBtn.onclick = async () => {
    syncBtn.disabled = true;
    const sent = await flushOutbox();
    toast(sent ? `All caught up — synced ${sent} change${sent === 1 ? "" : "s"}` : "Everything’s already in sync",
      { iconName: sent ? "check" : "info" });
    refreshQuietly();
  };
  refreshPending().catch(() => { ps.textContent = "Unavailable"; });

  p3.appendChild(row("Version", `Build ${state?.build || "dev"}`,
    (() => {
      const b = document.createElement("button");
      b.className = "btn ghost sm";
      b.textContent = state?.updateReady ? "Apply update" : "Check now";
      b.onclick = () => (state?.updateReady ? app()?.applyUpdate() : app()?.checkForUpdates(true));
      return b;
    })()
  ));

  p3.appendChild(row("Devices", "Sync and playback devices can get stuck after updates",
    (() => {
      const b = document.createElement("button");
      b.className = "btn danger sm";
      b.textContent = "Reset devices";
      b.onclick = async () => {
        if (!confirm("Clear all your device records? They will re-register automatically.")) return;
        try {
          await api("devices/clear", "POST");
          toast("Devices cleared", { iconName: "check" });
          app()?._syncDevices?.();
          app()?._startHeartbeat?.();
        } catch (e) {
          toast(e.message);
        }
      };
      return b;
    })()
  ));
  container.appendChild(p3);

  /* rotur */
  const p4 = document.createElement("div");
  p4.className = "panel";
  p4.appendChild(Object.assign(document.createElement("h2"), { textContent: "RoturLink" }));

  const rot = document.createElement("div");
  rot.className = "prow";
  const rl = document.createElement("div");
  const rb = document.createElement("b");
  rb.textContent = "Rotur account";
  const rs = document.createElement("small");
  rs.textContent = RoturLink.describe();
  rl.appendChild(rb);
  rl.appendChild(rs);
  rot.appendChild(rl);

  const racts = document.createElement("div");
  racts.style.cssText = "display:flex;gap:6px";
  if (!RoturLink.linked) {
    const link = document.createElement("button");
    link.className = "btn solid sm";
    link.textContent = RoturLink.configured ? "Sign in" : "Unavailable";
    link.disabled = !RoturLink.configured;
    link.onclick = () => RoturLink.signIn("/");
    racts.appendChild(link);
  } else {
    const un = document.createElement("button");
    un.className = "btn ghost sm";
    un.textContent = "Unlink";
    un.onclick = async () => {
      if (!confirm("Unlink this Rotur account?")) return;
      try {
        await RoturLink.unlink();
        toast("Rotur account unlinked");
        app()?.draw();
      } catch (e) {
        toast(e.message);
      }
    };
    racts.appendChild(un);
  }
  rot.appendChild(racts);
  p4.appendChild(rot);
  p4.appendChild(
    row("Share as Rotur activity", "Shows what you're playing on your Rotur profile",
      toggle(s.rotur_activity, (v) => app()?.setPref("rotur_activity", v)))
  );
  p4.appendChild(
    row("Room link", s.room_url || "Start a room to get a link",
      (() => {
        const copy = document.createElement("button");
        copy.className = "btn ghost sm";
        copy.textContent = "Copy";
        copy.disabled = !s.room_url;
        copy.onclick = async () => {
          try {
            await navigator.clipboard.writeText(s.room_url);
            toast("Room link copied", { iconName: "check" });
          } catch (e) {
            toast("Copy failed — long-press the link", { iconName: "triangle-alert" });
          }
        };
        return copy;
      })())
  );
  p4.appendChild(
    row("Show room link", "Adds the listen-along link to the activity",
      toggle(s.show_room_url, (v) => app()?.setPref("show_room_url", v)))
  );

  container.appendChild(p4);

  /* discord */
  const dc = Auth.discord || {};
  const pDc = document.createElement("div");
  pDc.className = "panel";
  pDc.appendChild(Object.assign(document.createElement("h2"), { textContent: "Discord" }));
  const dRow = document.createElement("div");
  dRow.className = "prow";
  const dText = document.createElement("div");
  const dB = document.createElement("b");
  dB.textContent = "Discord account";
  const dS = document.createElement("small");
  dS.textContent = !dc.configured
    ? `Discord linking needs ${(dc.missing?.length ? dc.missing : ["DISCORD_CLIENT_SECRET"]).join(" and ")} in the server environment`
    : dc.linked
      ? `Linked as ${dc.discord_username || dc.discord_id}`
      : "Not linked — control channels can still use /login";
  dText.appendChild(dB);
  dText.appendChild(dS);
  dRow.appendChild(dText);
  const dActs = document.createElement("div");
  dActs.style.cssText = "display:flex;gap:6px";
  if (dc.linked) {
    const un = document.createElement("button");
    un.className = "btn ghost sm";
    un.textContent = "Unlink";
    un.onclick = async () => {
      if (!confirm("Unlink this Discord account?")) return;
      try {
        await Auth.unlinkDiscord();
        toast("Discord account unlinked");
        app()?.draw();
      } catch (e) {
        toast(e.message);
      }
    };
    dActs.appendChild(un);
  } else {
    const link = document.createElement("button");
    link.className = "btn solid sm";
    link.textContent = dc.configured ? "Link" : "Unavailable";
    link.disabled = !dc.configured;
    link.onclick = () => Auth.discordLogin("/");
    dActs.appendChild(link);
  }
  dRow.appendChild(dActs);
  pDc.appendChild(dRow);
  pDc.appendChild(
    row("Share as Discord activity", discordPresenceHint(dc.presence),
      toggle(s.discord_activity, (v) => app()?.setPref("discord_activity", v)))
  );
  container.appendChild(pDc);

  /* account */
  const pAcct = document.createElement("div");
  pAcct.className = "panel";
  pAcct.appendChild(Object.assign(document.createElement("h2"), { textContent: "Account" }));

  pAcct.appendChild(row("Signed in as", me?.username || "—", (() => {
    const wrap = document.createElement("div");
    wrap.className = "row-actions";
    if (me?.pw !== false) {
      const pw = document.createElement("button");
      pw.className = "btn ghost sm";
      pw.textContent = "Password";
      pw.onclick = () => passwordSheet();
      wrap.appendChild(pw);
    }
    const out = document.createElement("button");
    out.className = "btn ghost sm";
    out.textContent = "Sign out";
    out.onclick = () => app()?.logout();
    wrap.appendChild(out);
    return wrap;
  })()));

  pAcct.appendChild(row("Email", me?.email || "Not set — needed for password resets", (() => {
    const b = document.createElement("button");
    b.className = "btn ghost sm";
    b.textContent = me?.email ? "Change" : "Add";
    b.onclick = () => emailSheet();
    return b;
  })()));

  const publicProfileUrl = `${location.origin}/u/${encodeURIComponent(me?.username || "")}`;
  pAcct.appendChild(row("Public profile", "No sign-in needed — use it in statuses", (() => {
    const b = document.createElement("button");
    b.className = "btn ghost sm";
    b.textContent = "Copy link";
    b.disabled = !me?.username;
    b.onclick = async () => {
      try {
        await navigator.clipboard.writeText(publicProfileUrl);
        toast("Public profile link copied", { iconName: "check" });
      } catch (e) {
        toast("Copy failed — long-press the link", { iconName: "triangle-alert" });
      }
    };
    return b;
  })()));

  /* the public embed gallery: copy-paste player cards for a site or README */
  pAcct.appendChild(row("Embed widgets", "Player cards for a site, README or bio", (() => {
    const a = document.createElement("a");
    a.className = "btn ghost sm";
    a.href = "/embeds";
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = "Open demo";
    return a;
  })()));
  container.appendChild(pAcct);

  /* apps — every build we publish, pulled from the server so this list can't
     go stale the way a hand-written one does */
  const pApps = document.createElement("div");
  pApps.className = "panel";
  pApps.appendChild(Object.assign(document.createElement("h2"), { textContent: "Get the app" }));
  pApps.appendChild(Object.assign(document.createElement("p"), {
    className: "panel-note",
    textContent: "The same library on every screen. Every build here is the newest one we made.",
  }));

  const builds = document.createElement("div");
  builds.className = "build-list";
  builds.appendChild(Object.assign(document.createElement("div"), {
    className: "prow",
    innerHTML: '<div><b>Looking for builds…</b><small>One moment</small></div>',
  }));
  pApps.appendChild(builds);
  container.appendChild(pApps);

  api("builds")
    .then((r) => {
      if (!pApps.isConnected) return;
      builds.replaceChildren();
      const list = (r?.builds || []).filter((b) => b.available);
      if (!list.length) {
        builds.appendChild(notice("No builds are published yet — check back soon."));
        return;
      }
      list.forEach((b) => builds.appendChild(buildRow(b)));
    })
    .catch(() => {
      if (!pApps.isConnected) return;
      builds.replaceChildren(
        notice("Couldn't reach the build list — the direct download below still works.")
      );
      builds.appendChild(buildRow({ kind: "android", label: "Android", hint: "Signed APK", url: "/apps/android/mainbuild.apk", bytes: 0 }));
    });

  /* admin */
  if (me?.is_admin) {
    const p5 = document.createElement("div");
    p5.className = "panel";
    p5.appendChild(Object.assign(document.createElement("h2"), { textContent: "Server" }));
    p5.appendChild(row("Library scan", "Pick up files added outside of requests", (() => {
      const b = document.createElement("button");
      b.className = "btn ghost sm";
      b.textContent = "Rescan";
      b.onclick = async () => {
        try {
          const r = await api("admin/scan", "POST");
          toast(`Scanned ${r.tracks} tracks`, { iconName: "check" });
        } catch (e) {
          toast(e.message);
        }
      };
      return b;
    })()));
    p5.appendChild(row("Control channels", "Discord and OriginChats dashboards", (() => {
      const b = document.createElement("button");
      b.className = "btn ghost sm";
      b.textContent = "Manage";
      b.onclick = () => app()?.navTo("admin");
      return b;
    })()));
    container.appendChild(p5);
  }

  /* keyboard */
  const p6 = document.createElement("div");
  p6.className = "panel";
  p6.appendChild(Object.assign(document.createElement("h2"), { textContent: "Keyboard" }));
  [["Play / pause", "Space"], ["Seek", "← →"], ["Next / previous", "Shift + → / ←"],
   ["Search", "/"], ["Like · Queue · Mute", "L · Q · M"]]
    .forEach(([label, keys]) => {
      p6.appendChild(row(label, null, (() => {
        const k = document.createElement("span");
        k.className = "kbd";
        k.textContent = keys;
        return k;
      })()));
    });
  container.appendChild(p6);
}

function gfxControl() {
  const wrap = document.createElement("div");
  wrap.className = "gfx-row";

  const head = document.createElement("div");
  head.className = "gfx-head";
  const title = document.createElement("div");
  const b = document.createElement("b");
  b.textContent = "Graphics quality";
  const device = document.createElement("small");
  device.textContent = "This device only. Auto starts at a safe level and lowers it if frames get slow.";
  title.appendChild(b);
  title.appendChild(device);
  head.appendChild(title);

  const autoLabel = document.createElement("label");
  autoLabel.className = "gfx-auto";
  const auto = document.createElement("input");
  auto.type = "checkbox";
  const autoText = document.createElement("span");
  autoText.textContent = "Auto";
  autoLabel.appendChild(auto);
  autoLabel.appendChild(autoText);
  head.appendChild(autoLabel);
  wrap.appendChild(head);

  const slider = document.createElement("input");
  slider.type = "range";
  slider.className = "gfx-range";
  slider.min = "0";
  slider.max = String(Gfx.state.manualMax);
  slider.step = "1";
  slider.setAttribute("aria-label", "Graphics quality");
  wrap.appendChild(slider);

  const scale = document.createElement("div");
  scale.className = "gfx-scale";
  GFX_LEVELS.forEach((level) => {
    const span = document.createElement("span");
    span.textContent = level.label;
    scale.appendChild(span);
  });
  wrap.appendChild(scale);

  const desc = document.createElement("p");
  desc.className = "gfx-desc";
  wrap.appendChild(desc);

  const readout = document.createElement("div");
  readout.className = "gfx-readout mono";
  wrap.appendChild(readout);

  const warning = document.createElement("p");
  warning.className = "gfx-warning";
  wrap.appendChild(warning);

  const sync = () => {
    const state = Gfx.state;
    slider.max = String(state.manualMax);
    slider.value = String(state.level);
    slider.disabled = false;
    auto.checked = state.auto;
    const level = GFX_LEVELS[state.level] || GFX_LEVELS[0];
    desc.textContent = state.auto
      ? `${level.label}: ${level.blurb}`
      : level.blurb;
    readout.textContent = state.frameMs == null
      ? "Current: — ms/frame"
      : `Current: ~${state.frameMs.toFixed(1)} ms/frame`;
    warning.hidden = !state.software;
    warning.textContent = state.software
      ? "Software rendering detected. Graphics are set to Off. Enable GPU acceleration in your browser for better quality."
      : "";
  };

  slider.oninput = () => {
    Gfx.setLevel(Number(slider.value));
    sync();
  };
  auto.onchange = () => {
    Gfx.setAuto(auto.checked);
    sync();
  };

  const onGfx = () => {
    if (!readout.isConnected) {
      window.removeEventListener("mc:gfx", onGfx);
      return;
    }
    sync();
  };
  window.addEventListener("mc:gfx", onGfx);
  sync();
  Gfx.activity();
  return wrap;
}

function row(label, hint, control) {
  const el = document.createElement("div");
  el.className = "prow";
  const left = document.createElement("div");
  const b = document.createElement("b");
  b.textContent = label;
  left.appendChild(b);
  if (hint) {
    const s = document.createElement("small");
    s.textContent = hint;
    left.appendChild(s);
  }
  el.appendChild(left);
  if (control) el.appendChild(control);
  return el;
}

function toggle(value, onchange) {
  const btn = document.createElement("button");
  btn.className = `switch${value ? " on" : ""}`;
  btn.setAttribute("role", "switch");
  btn.setAttribute("aria-checked", value ? "true" : "false");
  btn.onclick = async () => {
    const next = !btn.classList.contains("on");
    btn.classList.toggle("on", next);
    btn.setAttribute("aria-checked", next ? "true" : "false");
    await onchange(next);
  };
  return btn;
}

function segmented(options, current, onchange) {
  const seg = document.createElement("div");
  seg.className = "seg";
  options.forEach(([value, label]) => {
    const b = document.createElement("button");
    b.textContent = label;
    b.className = current === value ? "on" : "";
    b.onclick = () => {
      seg.querySelectorAll("button").forEach((x) => x.classList.remove("on"));
      b.classList.add("on");
      onchange(value);
    };
    seg.appendChild(b);
  });
  return seg;
}

function accentPicker(current, onchange) {
  const wrap = document.createElement("div");
  wrap.className = "swatches";
  ACCENTS.forEach((color) => {
    const b = document.createElement("button");
    b.className = `swatch${current === color ? " sel" : ""}`;
    b.style.background = color;
    b.setAttribute("aria-label", `Accent ${color}`);
    b.onclick = () => {
      wrap.querySelectorAll(".swatch").forEach((x) => x.classList.remove("sel"));
      b.classList.add("sel");
      onchange(color);
    };
    wrap.appendChild(b);
  });
  const picker = document.createElement("input");
  picker.type = "color";
  picker.value = current || "#d98a3d";
  picker.oninput = (e) => onchange(e.target.value);
  wrap.appendChild(picker);
  return wrap;
}

function emailSheet() {
  const input = document.createElement("input");
  input.type = "email";
  input.placeholder = "you@example.com";
  input.autocomplete = "email";
  input.value = app()?.me?.email || "";

  const save = document.createElement("button");
  save.className = "btn solid";
  save.textContent = "Save";
  const close = sheet("Account email", input, save);

  save.onclick = async () => {
    try {
      await Auth.setEmail(input.value.trim());
      toast("Email saved — reset links go there", { iconName: "check" });
      close();
      app()?.draw();
    } catch (e) {
      toast(e.message);
    }
  };
}

function passwordSheet() {
  const oldPw = document.createElement("input");
  oldPw.type = "password";
  oldPw.placeholder = "Current password";
  oldPw.autocomplete = "current-password";
  const newPw = document.createElement("input");
  newPw.type = "password";
  newPw.placeholder = "New password (6+ characters)";
  newPw.autocomplete = "new-password";

  const save = document.createElement("button");
  save.className = "btn solid";
  save.textContent = "Save";
  const close = sheet("Change password", oldPw, newPw, save);

  save.onclick = async () => {
    try {
      await api("password", "POST", { old: oldPw.value, new: newPw.value });
      toast("Password changed", { iconName: "check" });
      close();
    } catch (e) {
      toast(e.message);
    }
  };
}

/* ── admin / control channels ───────────────────────────────────────────── */
async function admin(container) {
  if (!app()?.me?.is_admin) {
    container.appendChild(empty("Admins only", "Your account does not have access.", { iconName: "triangle-alert" }));
    return;
  }

  const [stats, channels, users, roomData, deviceData, adminReqs, enrich] = await Promise.all([
    api("admin/stats").catch(() => ({})),
    api("channels").catch(() => ({ channels: [] })),
    api("admin/users").catch(() => ({ users: [] })),
    api("admin/rooms").catch(() => ({ rooms: [] })),
    api("admin/devices").catch(() => ({ devices: [] })),
    api("admin/requests").catch(() => ({ requests: [] })),
    api("admin/enrich").catch(() => ({})),
  ]);

  container.appendChild(heading("Server", "Live state and control channels"));

  const grid = document.createElement("div");
  grid.className = "admin-grid";
  [
    ["Users", stats.users], ["Admins", stats.admins], ["Tracks", stats.tracks],
    ["Albums", stats.albums], ["Playlists", stats.playlists], ["Plays", stats.plays],
    ["Requests", stats.requests ? Object.values(stats.requests).reduce((a, b) => a + b, 0) : null],
    ["Download queue", stats.queue], ["Rooms", stats.rooms],
    ["Library", stats.music_bytes ? fmtBytes(stats.music_bytes) : "—"],
    ["Free disk", stats.disk_free ? fmtBytes(stats.disk_free) : "—"],
    ["Uptime", stats.uptime ? fmtUptime(stats.uptime) : "—"],
  ].forEach(([label, value]) => {
    const card = document.createElement("div");
    card.className = "stat";
    const b = document.createElement("b");
    b.textContent = value == null ? "—" : String(value);
    const s = document.createElement("small");
    s.textContent = label;
    card.appendChild(b);
    card.appendChild(s);
    grid.appendChild(card);
  });
  container.appendChild(grid);

  /* friend codes */
  const invPanel = document.createElement("div");
  invPanel.className = "panel";
  invPanel.appendChild(Object.assign(document.createElement("h2"), { textContent: "Friend codes" }));

  const invForm = document.createElement("div");
  invForm.className = "prow";
  const invFormText = document.createElement("div");
  const invFormB = document.createElement("b");
  invFormB.textContent = "Generate a code";
  const invFormS = document.createElement("small");
  invFormS.textContent = "1 use, # uses, or expiring after N hours";
  invFormText.append(invFormB, invFormS);
  invForm.appendChild(invFormText);

  const invCtl = document.createElement("div");
  invCtl.style.cssText = "display:flex;gap:6px;align-items:center;flex-wrap:wrap";
  const usesIn = document.createElement("input");
  usesIn.type = "number";
  usesIn.min = "1";
  usesIn.max = "100";
  usesIn.value = "1";
  usesIn.title = "How many people can use this code";
  usesIn.style.width = "62px";
  const hoursIn = document.createElement("input");
  hoursIn.type = "number";
  hoursIn.min = "0";
  hoursIn.value = "0";
  hoursIn.title = "Expires after this many hours (0 = never)";
  hoursIn.style.width = "62px";
  const noteIn = document.createElement("input");
  noteIn.placeholder = "note (optional)";
  noteIn.style.width = "140px";
  const genBtn = document.createElement("button");
  genBtn.className = "btn solid sm";
  genBtn.textContent = "Generate";
  invCtl.append(usesIn, hoursIn, noteIn, genBtn);
  invForm.appendChild(invCtl);
  invPanel.appendChild(invForm);

  const invList = document.createElement("div");
  invPanel.appendChild(invList);
  container.appendChild(invPanel);

  const paintInvites = async () => {
    const d = await api("admin/invite-codes").catch(() => ({ codes: [] }));
    invList.replaceChildren();
    const codes = d.codes || [];
    if (!codes.length) {
      invList.appendChild(row("No codes yet", "Generate one above and send it to a friend", document.createElement("span")));
      return;
    }
    codes.forEach((c) => {
      const line = document.createElement("div");
      line.className = "prow";
      const info = document.createElement("div");
      const codeB = document.createElement("b");
      codeB.textContent = c.code;
      codeB.style.fontFamily = "var(--font-mono)";
      const meta = document.createElement("small");
      const bits = [`${c.uses}/${c.max_uses} used`];
      if (c.expires) {
        bits.push(c.expired ? "expired" : `expires ${new Date(c.expires * 1000).toLocaleString()}`);
      } else bits.push("no expiry");
      if (c.note) bits.push(c.note);
      if (c.created_by_name) bits.push(`by ${c.created_by_name}`);
      if (c.used_by?.length) bits.push(`used by ${c.used_by.map((u) => u.username).join(", ")}`);
      if (!c.active) bits.push("revoked");
      meta.textContent = bits.join(" · ");
      info.append(codeB, meta);
      line.appendChild(info);

      const acts = document.createElement("div");
      acts.style.cssText = "display:flex;gap:6px";
      const copy = document.createElement("button");
      copy.className = "btn ghost sm";
      copy.textContent = "Copy";
      copy.onclick = async () => {
        const link = `${location.origin}/?invite=${encodeURIComponent(c.code)}`;
        try {
          await navigator.clipboard.writeText(link);
          toast("Invite link copied");
        } catch (e) {
          sheet("Invite link", Object.assign(document.createElement("input"), { value: link, readOnly: true }));
        }
      };
      acts.appendChild(copy);
      if (c.active) {
        const rev = document.createElement("button");
        rev.className = "btn ghost sm";
        rev.textContent = "Revoke";
        rev.onclick = async () => {
          await api(`admin/invite-codes/${c.id}`, "DELETE").catch((e) => toast(e.message));
          paintInvites();
        };
        acts.appendChild(rev);
      }
      line.appendChild(acts);
      invList.appendChild(line);
    });
  };

  genBtn.onclick = async () => {
    genBtn.disabled = true;
    try {
      const r = await api("admin/invite-codes", "POST", {
        uses: Number(usesIn.value) || 1,
        hours: Number(hoursIn.value) || 0,
        note: noteIn.value.trim(),
      });
      toast(`Code ${r.code} created`);
      noteIn.value = "";
      paintInvites();
    } catch (e) {
      toast(e.message);
    } finally {
      genBtn.disabled = false;
    }
  };
  paintInvites();

  /* control channels */
  const chPanel = document.createElement("div");
  chPanel.className = "panel";
  chPanel.appendChild(Object.assign(document.createElement("h2"), { textContent: "Music control channels" }));

  const list = channels.channels || [];
  if (!list.length) {
    chPanel.appendChild(
      row("No channels bound",
        "Run /setmusicchannel in Discord, or start the OriginChats bridge with a channel id",
        (() => {
          const hint = document.createElement("span");
          hint.className = "ph-meta";
          hint.textContent = "waiting";
          return hint;
        })())
    );
  }

  list.forEach((ch) => {
    const un = document.createElement("button");
    un.className = "btn ghost sm";
    un.textContent = "Unbind";
    un.onclick = async () => {
      if (!confirm(`Unbind ${ch.platform} channel ${ch.channel_id}?`)) return;
      try {
        await api(`channels/${ch.id}`, "DELETE");
        toast("Channel unbound");
        app()?.draw();
      } catch (e) {
        toast(e.message);
      }
    };
    chPanel.appendChild(
      row(
        `${ch.platform} · ${ch.channel_id}`,
        `${ch.mode} · owner #${ch.owner_user_id ?? "—"} · dashboard ${ch.dashboard_id ? "live" : "pending"}`,
        un
      )
    );
  });
  container.appendChild(chPanel);

  /* users */
  const uPanel = document.createElement("div");
  uPanel.className = "panel";
  uPanel.appendChild(Object.assign(document.createElement("h2"), { textContent: "Accounts" }));
  const scroll = document.createElement("div");
  scroll.className = "scroll";
  const table = document.createElement("table");
  table.className = "admin";
  table.innerHTML = "<thead><tr><th>User</th><th>Email</th><th>Admin</th><th>Plays</th><th>Requests</th><th>Created</th><th></th></tr></thead>";
  const tbody = document.createElement("tbody");
  (users.users || []).forEach((u) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${escapeHtml(u.username)}</td>
      <td>${u.email ? escapeHtml(u.email) : "—"}</td>
      <td>${u.is_admin ? "yes" : "no"}</td>
      <td>${u.plays ?? 0}</td>
      <td>${u.requests ?? 0}</td>
      <td>${u.created ? new Date(u.created * 1000).toLocaleDateString() : "—"}</td>`;
    const actions = document.createElement("td");
    const roleBtn = document.createElement("button");
    roleBtn.className = "btn ghost sm";
    roleBtn.textContent = u.is_admin ? "Demote" : "Promote";
    roleBtn.onclick = async () => {
      try {
        await api(`admin/users/${u.id}/admin`, "POST", { is_admin: !u.is_admin });
        app()?.draw();
      } catch (e) {
        toast(e.message);
      }
    };
    actions.appendChild(roleBtn);

    if (u.id !== app()?.me?.id) {
      const del = document.createElement("button");
      del.className = "btn danger sm";
      del.textContent = "Delete";
      del.onclick = async () => {
        if (!confirm(`Delete ${u.username}? Their plays, likes and playlists go with them.`)) return;
        try {
          await api(`admin/users/${u.id}`, "DELETE");
          toast(`${u.username} deleted`);
          app()?.draw();
        } catch (e) {
          toast(e.message);
        }
      };
      actions.appendChild(del);
    }
    actions.style.cssText = "display:flex;gap:4px;justify-content:flex-end";
    tr.appendChild(actions);
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  scroll.appendChild(table);
  uPanel.appendChild(scroll);
  container.appendChild(uPanel);

  /* download requests — polled live while this view is open */
  const qPanel = document.createElement("div");
  qPanel.className = "panel";
  const qHead = document.createElement("h2");
  qHead.textContent = "Download requests";
  const liveChip = document.createElement("span");
  liveChip.className = "mono";
  liveChip.style.cssText = "font-size:10px;color:var(--dim);margin-left:8px;letter-spacing:.06em";
  liveChip.textContent = "live";
  qHead.appendChild(liveChip);
  qPanel.appendChild(qHead);

  const qList = document.createElement("div");
  qPanel.appendChild(qList);
  container.appendChild(qPanel);

  const rank = { running: 0, approved: 1, pending: 2, failed: 3, cancelled: 4, done: 5, rejected: 6 };

  const paintRequests = async () => {
    if (!qList.isConnected) return;
    let data;
    try {
      data = await api("admin/requests");
    } catch (e) {
      qList.replaceChildren(row("Could not load requests", e.message, metaChip("offline")));
      return;
    }
    const rows = data.requests || [];
    const queued = rows.filter((q) => q.status === "approved").length;
    const busy = rows.filter((q) => q.running).length;
    liveChip.textContent = busy || queued ? `live · ${busy} running · ${queued} queued` : "live";

    qList.replaceChildren();
    if (!rows.length) {
      qList.appendChild(row("Nothing requested", "Links pasted on the Requests page land here", metaChip("empty")));
      return;
    }

    rows.sort((a, b) => (rank[a.status] ?? 9) - (rank[b.status] ?? 9) || b.id - a.id);
    rows.slice(0, 25).forEach((q) => {
      const acts = document.createElement("div");
      acts.style.cssText = "display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end";

      const logBtn = document.createElement("button");
      logBtn.className = "btn ghost sm";
      logBtn.textContent = "Log";
      logBtn.onclick = () => requestLogSheet(q.id, q.status);
      acts.appendChild(logBtn);

      const act = (label, path, method, cls) => {
        const b = document.createElement("button");
        b.className = `btn ${cls || "ghost"} sm`;
        b.textContent = label;
        b.onclick = async () => {
          b.disabled = true;
          try {
            await api(path, method);
            toast(`${label} · #${q.id}`);
            paintRequests();
          } catch (e) {
            toast(e.message);
            b.disabled = false;
          }
        };
        acts.appendChild(b);
      };

      if (["pending", "failed"].includes(q.status)) {
        act("Approve", `requests/${q.id}/approve`, "POST", "solid");
        act("Reject", `requests/${q.id}/reject`, "POST");
      }
      if (q.running || q.status === "running") act("Cancel", `admin/requests/${q.id}/cancel`, "POST");
      if (["failed", "cancelled", "done"].includes(q.status)) act("Retry", `admin/requests/${q.id}/retry`, "POST");
      if (!q.running && q.status !== "running") act("Delete", `admin/requests/${q.id}`, "DELETE", "danger");

      const lastLine = String(q.log || "").trim().split("\n").pop() || "";
      const detail = q.running || q.status === "running"
        ? `running · ${fmtSecs(q.elapsed)}${lastLine ? " · " + lastLine.slice(0, 70) : ""}`
        : `${q.username || "—"} · ${String(q.url || "").slice(0, 58)}`;

      qList.appendChild(row(`#${q.id} · ${q.status}`, detail, acts));
    });
  };

  await paintRequests();
  app().timer = setInterval(paintRequests, 5000);

  /* live rooms */
  const rPanel = document.createElement("div");
  rPanel.className = "panel";
  rPanel.appendChild(Object.assign(document.createElement("h2"), { textContent: "Listen-along rooms" }));
  const rooms = roomData.rooms || [];
  if (!rooms.length) {
    rPanel.appendChild(row("No live rooms", "Open one from the player with Listen along", (() => {
      const s = document.createElement("span");
      s.className = "ph-meta";
      s.textContent = "idle";
      return s;
    })()));
  }
  rooms.forEach((rm) => {
    const end = document.createElement("button");
    end.className = "btn danger sm";
    end.textContent = "End";
    end.onclick = async () => {
      if (!confirm(`End room ${rm.code}?`)) return;
      try {
        await api(`admin/rooms/${rm.code}`, "DELETE");
        toast("Room ended");
        app()?.draw();
      } catch (e) {
        toast(e.message);
      }
    };
    const track = rm.track ? `${rm.track.title} · ${rm.track.artist}` : "no track";
    rPanel.appendChild(
      row(
        `${rm.host} · ${rm.code}`,
        `${track} · ${rm.playing ? "playing" : "paused"} · idle ${Math.round(rm.idle || 0)}s${rm.away ? " · away" : ""}`,
        end
      )
    );
  });
  container.appendChild(rPanel);

  /* devices */
  const dPanel = document.createElement("div");
  dPanel.className = "panel";
  dPanel.appendChild(Object.assign(document.createElement("h2"), { textContent: "Devices" }));
  const devs = (deviceData.devices || []).slice(0, 40);
  if (!devs.length) {
    dPanel.appendChild(row("No devices yet", "A device registers on its first heartbeat", (() => {
      const s = document.createElement("span");
      s.className = "ph-meta";
      s.textContent = "none";
      return s;
    })()));
  }
  devs.forEach((d) => {
    const chip = document.createElement("span");
    chip.className = "ph-meta";
    chip.textContent = d.is_active ? "active" : "idle";
    dPanel.appendChild(
      row(
        `${d.username} · ${d.name || d.device_hash.slice(0, 8)}`,
        `${d.ip || "—"} · seen ${d.last_seen ? fmtAgo(d.last_seen) : "never"}`,
        chip
      )
    );
  });
  container.appendChild(dPanel);

  /* maintenance */
  const mPanel = document.createElement("div");
  mPanel.className = "panel";
  mPanel.appendChild(Object.assign(document.createElement("h2"), { textContent: "Maintenance" }));
  const scanBtn = document.createElement("button");
  scanBtn.className = "btn solid sm";
  scanBtn.textContent = "Rescan library";
  scanBtn.onclick = async () => {
    scanBtn.disabled = true;
    try {
      const r = await api("admin/scan", "POST");
      toast(`Scanned · ${r.tracks} tracks in ${r.albums} albums`);
      app()?.draw();
    } catch (e) {
      toast(e.message);
    } finally {
      scanBtn.disabled = false;
    }
  };
  mPanel.appendChild(row("Library index", `${stats.tracks || 0} tracks on disk`, scanBtn));
  mPanel.appendChild(
    row(
      "YouTube links",
      `${enrich.linked || 0} of ${enrich.total || 0} tracks linked · ${enrich.fetched || 0} enriched`,
      (() => {
        const b = document.createElement("button");
        b.className = "btn ghost sm";
        b.textContent = "Recheck";
        b.onclick = () => {
          toast("Metadata enrichment runs during the next scan");
        };
        return b;
      })()
    )
  );
  mPanel.appendChild(
    row(
      "Server process",
      `pid ${stats.pid ?? "—"} · up ${stats.uptime ? fmtUptime(stats.uptime) : "—"}`,
      (() => {
        const s = document.createElement("span");
        s.className = "ph-meta";
        s.textContent = stats.disk_total ? `${fmtBytes(stats.disk_used)} / ${fmtBytes(stats.disk_total)}` : "disk —";
        return s;
      })()
    )
  );
  container.appendChild(mPanel);
}

function fmtAgo(ts) {
  const secs = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  if (secs < 60) return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

function fmtUptime(seconds) {
  const s = Math.max(0, Math.floor(seconds || 0));
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (d) return `${d}d ${h}h`;
  if (h) return `${h}h ${m}m`;
  return `${m}m`;
}

function metaChip(text) {
  const s = document.createElement("span");
  s.className = "ph-meta";
  s.textContent = text;
  return s;
}

function fmtSecs(seconds) {
  const s = Math.max(0, Math.round(Number(seconds) || 0));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${s % 60}s`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

/** Tail the worker log of one request while it runs. */
function requestLogSheet(id, status) {
  const pre = document.createElement("pre");
  pre.style.cssText = "margin:0;max-height:46vh;overflow:auto;white-space:pre-wrap;" +
    "font-family:var(--font-mono);font-size:11px;line-height:1.55;background:var(--bg);" +
    "border:1px solid var(--line);border-radius:var(--r-2);padding:10px";
  pre.textContent = "loading…";

  const closeBtn = document.createElement("button");
  closeBtn.className = "btn ghost";
  closeBtn.textContent = "Close";
  const close = sheet(`Request #${id} · ${status || ""}`, pre, closeBtn);
  closeBtn.onclick = () => close();

  let timer = null;
  const tick = async () => {
    if (!pre.isConnected) {
      if (timer) clearInterval(timer);
      timer = null;
      return;
    }
    try {
      const r = await api(`admin/requests/${id}/log?tail=20000`);
      pre.textContent = r.log || "(no output yet)";
      pre.scrollTop = pre.scrollHeight;
      if (!r.running && timer) {
        clearInterval(timer);
        timer = null;
      }
    } catch (e) {
      pre.textContent = e.message;
    }
  };
  tick();
  timer = setInterval(tick, 2000);
  return close;
}

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function buildRow(b) {
  const el = document.createElement("div");
  el.className = "prow build-row";

  const left = document.createElement("div");
  const name = document.createElement("b");
  name.textContent = b.name || b.label;
  left.appendChild(name);
  const meta = document.createElement("small");
  const bits = [b.hint];
  if (b.bytes) bits.push(fmtBytes(b.bytes));
  if (b.built) bits.push(`built ${b.built}`);
  meta.textContent = bits.filter(Boolean).join(" · ");
  left.appendChild(meta);
  el.appendChild(left);

  const acts = document.createElement("div");
  acts.className = "row-actions";

  const dl = document.createElement("a");
  dl.className = "btn solid sm";
  dl.textContent = "Download";
  dl.href = b.url || "#";
  dl.setAttribute("download", "");
  acts.appendChild(dl);

  const mail = document.createElement("button");
  mail.className = "btn ghost sm";
  mail.textContent = "Email it";
  mail.onclick = () => buildEmailSheet(b);
  acts.appendChild(mail);

  el.appendChild(acts);
  return el;
}

/** Ask for an address and post the actual file, not a link to it. */
function buildEmailSheet(b) {
  const hint = document.createElement("p");
  hint.className = "panel-note";
  hint.textContent = `We'll email you a download button and the file itself. Gmail blocks ` +
    ".apk attachments, so if you're on Gmail, tap the button in the message — " +
    "it installs the same build.";

  const input = document.createElement("input");
  input.type = "email";
  input.placeholder = "you@example.com";
  input.autocomplete = "email";
  input.value = app()?.me?.email || "";

  const send = document.createElement("button");
  send.className = "btn solid";
  send.textContent = "Send the file";

  const close = sheet(`Email the ${b.label} build`, hint, input, send);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") send.click();
  });

  send.onclick = async () => {
    const email = input.value.trim();
    if (!email) {
      toast("Add an email address first");
      input.focus();
      return;
    }
    send.disabled = true;
    send.textContent = "Sending…";
    try {
      const r = await fetch("/api/builds/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, build: b.kind }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok || !data.ok) throw new Error(data.error || "The mail server said no");
      close();
      toast(`Sent to ${email} — open it on your phone`, { iconName: "check" });
    } catch (err) {
      toast(err.message, { iconName: "triangle-alert" });
      send.disabled = false;
      send.textContent = "Try again";
    }
  };
}
export const Views = {
  home, search, library, album, artist, likes, playlists, playlist,
  requests, downloads, settings, admin, now,
};

export function hasView(name) {
  return Object.prototype.hasOwnProperty.call(Views, name);
}

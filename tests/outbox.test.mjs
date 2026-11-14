/* Browser-side outbox suite.
 *
 * api.js has no build step and this repo ships no browser test runner, so the
 * offline queue is exercised under Node with IndexedDB, fetch and a minimal
 * window stubbed out. tests/test_outbox.py invokes this file, which keeps
 * `python -m unittest discover -s tests` a single command for the whole repo.
 *
 * The sources are ES modules; because the repo has no package.json, Node only
 * treats them as modules if a copy sits next to a module-typed one.
 */
import { copyFileSync, mkdtempSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.join(path.dirname(HERE), "web", "js");
const work = mkdtempSync(path.join(tmpdir(), "mcm-outbox-"));
for (const name of readdirSync(SRC).filter((n) => n.endsWith(".js"))) {
  copyFileSync(path.join(SRC, name), path.join(work, name));
}
writeFileSync(path.join(work, "package.json"), '{"type":"module"}');

let fails = 0;
function ok(name, cond, extra = "") {
  if (cond) {
    console.log(`ok   ${name}`);
  } else {
    fails += 1;
    console.log(`FAIL ${name} ${extra}`);
  }
}
function done() {
  rmSync(work, { recursive: true, force: true });
  console.log(fails === 0 ? "OUTBOX-TEST-PASS" : `OUTBOX-TEST-FAIL (${fails})`);
  process.exit(fails === 0 ? 0 : 1);
}

/* ── IndexedDB stub (single kv store, one transaction per call) ───────────── */
const store = new Map();
class FakeRequest { constructor() { this.result = undefined; } }
class FakeStore {
  get(k) { const r = new FakeRequest(); r.result = store.get(k); return r; }
  put(v, k) { store.set(k, v); return new FakeRequest(); }
  delete(k) { store.delete(k); return new FakeRequest(); }
}
class FakeTx {
  objectStore() { return new FakeStore(); }
  set oncomplete(fn) { setTimeout(fn, 0); }
  set onerror(_fn) {}
  set onabort(_fn) {}
}
const db = {
  objectStoreNames: { contains: () => true },
  createObjectStore() {},
  transaction() { return new FakeTx(); },
};

/* ── window stub with a real listener table, so lifecycle hooks are testable ─ */
const listeners = new Map();
const win = {
  addEventListener(name, fn) {
    if (!listeners.has(name)) listeners.set(name, []);
    listeners.get(name).push(fn);
  },
  removeEventListener(name, fn) {
    const list = listeners.get(name) || [];
    listeners.set(name, list.filter((f) => f !== fn));
  },
  dispatchEvent(ev) {
    (listeners.get(ev && ev.type) || []).slice().forEach((fn) => fn(ev));
    return true;
  },
};
win.indexedDB = {
  open() {
    const req = {};
    Object.defineProperty(req, "onsuccess", {
      set(fn) { setTimeout(() => { req.result = db; fn(); }, 0); },
    });
    return req;
  },
};
globalThis.window = win;
globalThis.indexedDB = win.indexedDB;

/* ── fetch stub: offline throws like a dropped connection ─────────────────── */
const net = { down: true, status: 200, calls: [] };
const headers = { get: (k) => (k.toLowerCase() === "content-type" ? "application/json" : null) };
globalThis.fetch = async (url, opts = {}) => {
  if (net.down) throw new TypeError("Failed to fetch");
  net.calls.push(`${opts.method || "GET"} ${url}`);
  if (net.status >= 400) {
    return { ok: false, status: net.status, headers, json: async () => ({ error: "nope" }) };
  }
  return { ok: true, status: 200, headers, json: async () => ({ ok: true }) };
};

const { api, flushOutbox, pendingWrites } = await import(
  pathToFileURL(path.join(work, "api.js")).href
);

/* ── queueing and replay ─────────────────────────────────────────────────── */
const like = await api("like/7", "POST");
ok("like is queued while offline", like.queued === true);
await api("playlists/3/tracks", "POST", { track_id: 9 });

let threw = null;
try { await api("settings", "PUT", { volume: 0.4 }); } catch (e) { threw = e; }
ok("non-replayable write still fails loudly", !!threw);
ok("queue depth counts both writes", (await pendingWrites()) === 2);

net.down = false;
ok("queued writes are replayed", (await flushOutbox()) === 2);
ok("queue drains after replay", (await pendingWrites()) === 0);
ok("replay keeps each method", net.calls.join("|") === "POST /api/like/7|POST /api/playlists/3/tracks",
  net.calls.join("|"));

/* ── playlist edits and deletes ──────────────────────────────────────────── */
net.down = true; net.calls = [];
await api("playlists/3", "PATCH", { name: "Renamed" });
await api("playlists/3/tracks/9", "DELETE");
await api("playlists/3", "DELETE");
ok("playlist edits and deletes queue", (await pendingWrites()) === 3);
net.down = false; net.status = 200;
ok("playlist edits replay in order", (await flushOutbox()) === 3);
ok("playlist replay keeps methods",
  net.calls.join("|") === "PATCH /api/playlists/3|DELETE /api/playlists/3/tracks/9|DELETE /api/playlists/3",
  net.calls.join("|"));

net.down = true; await api("playlists/4", "DELETE");
net.down = false; net.status = 404; net.calls = [];
ok("deleting a row that is already gone is satisfied",
  (await flushOutbox()) === 0 && (await pendingWrites()) === 0);

/* ── failure handling ───────────────────────────────────────────────────── */
net.down = true; await api("like/8", "POST");
net.down = false; net.status = 403;
ok("a permanent rejection is dropped", (await flushOutbox()) === 0 && (await pendingWrites()) === 0);

net.down = true; await api("like/9", "POST");
net.status = 500;
ok("a server error keeps the write queued",
  (await flushOutbox()) === 0 && (await pendingWrites()) === 1);
net.status = 200; net.down = false;
ok("the queue drains once the server recovers",
  (await flushOutbox()) === 1 && (await pendingWrites()) === 0);

/* ── a like is a toggle, so repeats are meaningful ──────────────────────── */
net.down = true; net.calls = [];
await api("like/42", "POST");
await api("like/42", "POST");
ok("repeated toggles are not collapsed", (await pendingWrites()) === 2);
net.down = false;
ok("both toggles are replayed", (await flushOutbox()) === 2);
ok("toggle order is preserved",
  net.calls.join("|") === "POST /api/like/42|POST /api/like/42", net.calls.join("|"));
ok("toggle queue drains", (await pendingWrites()) === 0);

/* ── identical playlist adds are a server-side no-op, so they collapse ──── */
net.down = true; net.calls = [];
await api("playlists/5/tracks", "POST", { track_id: 9 });
await api("playlists/5/tracks", "POST", { track_id: 9 });
ok("a repeated playlist add collapses", (await pendingWrites()) === 1);
await api("playlists/5/tracks", "POST", { track_id: 10 });
ok("adds of different tracks stay separate", (await pendingWrites()) === 2);
net.down = false;
ok("both collapsing and distinct adds replay", (await flushOutbox()) === 2);

/* ── a queue left over from a previous session flushes on boot ──────────── */
net.down = true; await api("like/11", "POST");
net.down = false; net.calls = [];
ok("a leftover write is pending before boot", (await pendingWrites()) === 1);
win.dispatchEvent({ type: "load" });
await new Promise((r) => setTimeout(r, 80));
ok("boot flushes the leftover queue", (await pendingWrites()) === 0);
ok("boot replays the right write", net.calls.join("|") === "POST /api/like/11", net.calls.join("|"));

/* ── a flush already under way is joined, not reported as empty ────────── */
net.down = true; await api("like/12", "POST");
net.down = false; net.calls = [];
const [first, second] = await Promise.all([flushOutbox(), flushOutbox()]);
ok("a second flush joins the run in progress", first === 1 && second === 1, `${first}/${second}`);
ok("the joined run sends the write once", net.calls.length === 1, net.calls.join("|"));
ok("joining leaves the queue drained", (await pendingWrites()) === 0);

/* ── the queue is bounded, dropping the oldest writes ───────────────────── */
net.down = true; net.calls = [];
for (let i = 0; i < 105; i += 1) await api(`like/${1000 + i}`, "POST");
ok("the queue is capped at 100 writes", (await pendingWrites()) === 100);
net.down = false;
ok("a capped queue replays everything it kept", (await flushOutbox()) === 100);
ok("the oldest writes are the ones dropped",
  net.calls[0] === "POST /api/like/1005" && net.calls.length === 100, net.calls[0]);

done();

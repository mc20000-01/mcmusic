"""
mcmusic OriginChats bridge — the same control-channel contract, over REST.

OriginChats deployments differ, so this bridge talks to a small, documented
message API instead of guessing at a protocol. Configure:

  ORIGINCHATS_BASE     https://chat.example.com/api
  ORIGINCHATS_TOKEN    bearer token with read/write/delete on the channel
  ORIGINCHATS_CHANNEL  channel id to bind
  MCMUSIC_BOT_TOKEN    credential for mcmusic (shared with the Discord bot)

Expected endpoints (all JSON, Authorization: Bearer <ORIGINCHATS_TOKEN>):

  GET    {base}/channels/{channel}/messages?after=<id>&limit=50
         -> {"messages": [{"id": "…", "content": "…",
                           "author": {"id": "…", "name": "…", "bot": false}}]}
  POST   {base}/channels/{channel}/messages   {"content": "…"}
         -> {"id": "…"}
  PATCH  {base}/channels/{channel}/messages/{id}  {"content": "…"}
  DELETE {base}/channels/{channel}/messages/{id}

If your deployment uses different paths, point the variables below at a thin
adapter — nothing else in mcmusic needs to change. The bridge is inert unless
all three ORIGINCHATS_* values are set.
"""
import asyncio
import json
import os
import threading

import aiohttp

MCMUSIC_BASE = os.environ.get("MCMUSIC_BASE", "http://127.0.0.1:8000").rstrip("/")
BOT_TOKEN = os.environ.get("MCMUSIC_BOT_TOKEN") or os.environ.get("DISCORD_ADMIN_TOKEN", "")
BASE = os.environ.get("ORIGINCHATS_BASE", "").rstrip("/")
TOKEN = os.environ.get("ORIGINCHATS_TOKEN", "")
CHANNEL = os.environ.get("ORIGINCHATS_CHANNEL", "")
INTERVAL = float(os.environ.get("DASHBOARD_INTERVAL", "4"))

COMMANDS = {
    "login": "link your Rotur account",
    "addtoqueue": "queue a link or track",
    "removefromqueue": "drop a queued track",
    "skip": "next track",
    "pause": "pause / resume",
    "np": "what is playing",
    "queue": "show the queue",
    "help": "this list",
}


class OriginChatsBridge:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.bound_row = None
        self.dashboard_id = None
        self.last_seen = None
        self.seen: set[str] = set()

    # ---------------------------------------------------------------- transport
    async def _oc(self, method, path, body=None, params=None):
        headers = {"Authorization": f"Bearer {TOKEN}"}
        url = f"{BASE}{path}"
        async with self.session.request(
            method, url, json=body, params=params, headers=headers,
            timeout=aiohttp.ClientTimeout(total=20),
        ) as r:
            text = await r.text()
            if r.status >= 400:
                raise RuntimeError(f"OriginChats {method} {path} -> {r.status}: {text[:200]}")
            if not text:
                return {}
            try:
                return json.loads(text)
            except ValueError:
                return {}

    async def _mcmusic(self, method, path, body=None, params=None):
        headers = {"X-MCMUSIC-BOT": BOT_TOKEN}
        async with self.session.request(
            method, f"{MCMUSIC_BASE}/api/{path}", json=body, params=params,
            headers=headers, timeout=aiohttp.ClientTimeout(total=20),
        ) as r:
            data = await r.json(content_type=None)
            if r.status >= 400:
                raise RuntimeError(data.get("error") or f"mcmusic {r.status}")
            return data

    async def _send(self, content, message_id=None):
        if message_id:
            await self._oc("PATCH", f"/channels/{CHANNEL}/messages/{message_id}",
                           {"content": content})
            return message_id
        data = await self._oc("POST", f"/channels/{CHANNEL}/messages", {"content": content})
        return str(data.get("id") or "") or None

    # ---------------------------------------------------------------- setup
    async def bind(self):
        data = await self._mcmusic("POST", "channels", {
            "platform": "originchats", "channel_id": CHANNEL, "mode": "control",
        })
        self.bound_row = data["channel"]
        self.dashboard_id = self.bound_row.get("dashboard_id")
        print(f"[originchats] channel {CHANNEL} bound (row {self.bound_row['id']})", flush=True)

    async def purge(self):
        """Delete existing messages so the channel starts as a control surface."""
        try:
            data = await self._oc("GET", f"/channels/{CHANNEL}/messages",
                                  params={"limit": 50})
        except Exception as e:
            print(f"[originchats] purge skipped: {e}", flush=True)
            return 0
        removed = 0
        for msg in reversed(data.get("messages") or []):
            author = msg.get("author") or {}
            if author.get("bot"):
                continue
            try:
                await self._oc("DELETE", f"/channels/{CHANNEL}/messages/{msg['id']}")
                removed += 1
            except Exception:
                pass
        self.dashboard_id = None
        return removed

    # ---------------------------------------------------------------- dashboard
    async def paint(self):
        if not self.bound_row:
            return
        state = await self._mcmusic("GET", f"channels/{self.bound_row['id']}/state")
        text = state.get("text") or ""
        if not text:
            from music_channels import render_text
            text = render_text(state)
        text = text[:MAX_TEXT]
        try:
            self.dashboard_id = await self._send(text, self.dashboard_id)
        except Exception as e:
            if self.dashboard_id:
                # The dashboard was probably deleted; post a fresh one.
                self.dashboard_id = None
                try:
                    self.dashboard_id = await self._send(text)
                except Exception as e2:
                    print(f"[originchats] dashboard post failed: {e2}", flush=True)
                    return
            else:
                print(f"[originchats] dashboard edit failed: {e}", flush=True)
                return
        try:
            await self._mcmusic("POST", f"channels/{self.bound_row['id']}/dashboard",
                                {"message_id": self.dashboard_id})
        except Exception:
            pass

    # ---------------------------------------------------------------- commands
    async def poll(self):
        params = {"limit": 50}
        if self.last_seen:
            params["after"] = self.last_seen
        try:
            data = await self._oc("GET", f"/channels/{CHANNEL}/messages", params=params)
        except Exception as e:
            print(f"[originchats] poll failed: {e}", flush=True)
            return
        msgs = data.get("messages") or []
        for msg in msgs:
            mid = str(msg.get("id") or "")
            if mid:
                self.last_seen = mid
            if mid in self.seen:
                continue
            self.seen.add(mid)
            author = msg.get("author") or {}
            if author.get("bot"):
                continue
            content = (msg.get("content") or "").strip()
            if not content.startswith("/"):
                await self._delete(mid)
                continue
            await self._handle(content, author, mid)

    async def _delete(self, mid):
        try:
            await self._oc("DELETE", f"/channels/{CHANNEL}/messages/{mid}")
        except Exception:
            pass

    async def _reply(self, text):
        try:
            await self._oc("POST", f"/channels/{CHANNEL}/messages", {"content": text[:MAX_TEXT]})
        except Exception as e:
            print(f"[originchats] reply failed: {e}", flush=True)

    async def _handle(self, content, author, mid):
        parts = content.split()
        cmd = parts[0].lstrip("/").lower()
        args = parts[1:]
        who = str(author.get("id") or "")
        display = author.get("name") or who

        if cmd in ("help", "commands"):
            await self._delete(mid)
            await self._reply("**mcmusic**\n" + "\n".join(
                f"`/{k}` — {v}" for k, v in COMMANDS.items()))
            return

        if cmd == "login":
            await self._delete(mid)
            try:
                data = await self._mcmusic("POST", "bot/rotur-ticket",
                                           {"platform": "originchats", "platform_user": who})
            except Exception as e:
                await self._reply(f"Login failed: {e}")
                return
            await self._reply(f"{display}: sign in with Rotur (10 min, single use): {data['url']}")
            return

        try:
            ctx = await self._mcmusic("GET", "bot/context",
                                      params={"platform": "originchats", "platform_user": who})
        except Exception as e:
            await self._reply(f"mcmusic error: {e}")
            return
        uid = (ctx.get("me") or {}).get("id")
        if not uid:
            await self._reply(f"{display}: link your account first — `/login`")
            return

        if cmd == "addtoqueue":
            query = " ".join(args).strip()
            if not query:
                await self._reply("Usage: `/addtoqueue <url or track>`")
                return
            payload = {"platform": "originchats", "platform_user": who}
            payload["url" if query.startswith("http") else "query"] = query
            try:
                data = await self._mcmusic("POST", "bot/enqueue", payload)
            except Exception as e:
                await self._reply(f"Could not queue: {e}")
                return
            await self._reply(f"{display}: queued {data.get('track', {}).get('title') or 'download'}")
            await self.paint()

        elif cmd == "removefromqueue":
            if not args or not args[0].isdigit():
                await self._reply("Usage: `/removefromqueue <position>`")
                return
            await self._control(uid, "remove", index=int(args[0]) - 1)
            await self._reply(f"{display}: removed position {args[0]}")

        elif cmd == "skip":
            await self._control(uid, "skip")
            await self._reply(f"{display}: skipped")

        elif cmd == "pause":
            await self._control(uid, "toggle")
            await self._reply(f"{display}: toggled playback")

        elif cmd in ("np", "nowplaying"):
            pb = ctx.get("playback") or {}
            t = pb.get("track")
            if not t:
                await self._reply("Nothing playing.")
            else:
                await self._reply(
                    f"**{t['title']}** — {t['artist']} · "
                    f"`{clock(pb.get('position'))}/{clock(pb.get('duration'))}`")

        elif cmd == "queue":
            try:
                data = await self._mcmusic("GET", "queue")
            except Exception as e:
                await self._reply(f"mcmusic error: {e}")
                return
            q = data.get("queue") or []
            await self._reply("Queue is empty." if not q else "\n".join(
                f"{i}. {t['title']} — {t['artist']}" for i, t in enumerate(q[:12], 1)))

        else:
            await self._reply(f"Unknown command `/{cmd}`. Try `/help`.")

    async def _control(self, uid, action, **arg):
        try:
            await self._mcmusic("POST", "playback/command",
                                {"user_id": uid, "action": action, **arg})
        except Exception as e:
            print(f"[originchats] control {action} failed: {e}", flush=True)

    # ---------------------------------------------------------------- loop
    async def run(self):
        await self.bind()
        removed = await self.purge()
        print(f"[originchats] purged {removed} message(s)", flush=True)
        await self.paint()
        while True:
            await self.poll()
            await self.paint()
            await asyncio.sleep(INTERVAL)


MAX_TEXT = 1900


def clock(v):
    v = max(0, int(round(float(v or 0))))
    return f"{v // 60}:{v % 60:02d}"


def configured():
    return bool(BASE and TOKEN and CHANNEL)


async def _main():
    if not configured():
        print("[originchats] ORIGINCHATS_BASE/TOKEN/CHANNEL not set — not starting", flush=True)
        return
    async with aiohttp.ClientSession() as session:
        await OriginChatsBridge(session).run()


def start_in_background():
    """Run the bridge on its own event loop thread (used by discord_bot)."""
    if not configured():
        return None

    def _runner():
        try:
            asyncio.run(_main())
        except Exception as e:
            print(f"[originchats] stopped: {e}", flush=True)

    t = threading.Thread(target=_runner, daemon=True, name="originchats")
    t.start()
    return t


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass

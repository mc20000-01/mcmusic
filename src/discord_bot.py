"""
mcmusic Discord bot — music control channels.

A guild manager binds one text channel with /setmusicchannel. From then on that
channel is a control surface, not a chat:

  * existing history is purged on setup;
  * any casual message is deleted immediately (commands are slash commands, so
    they never appear as messages);
  * one sticky dashboard message is kept up to date with now playing, progress,
    the queue and the command legend;
  * /login links a Discord user to their Rotur-backed mcmusic account, and the
    music commands act as that user.

Env: DISCORD_BOT_TOKEN, DISCORD_GUILD_ID (optional fast sync),
     MCMUSIC_BASE, DISCORD_ADMIN_TOKEN / MCMUSIC_BOT_TOKEN.

Runs as a separate process (started automatically by mcmusic.py).
"""
import os

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

MCMUSIC_BASE = os.environ.get("MCMUSIC_BASE", "http://127.0.0.1:8000").rstrip("/")
BOT_TOKEN = os.environ.get("MCMUSIC_BOT_TOKEN") or os.environ.get("DISCORD_ADMIN_TOKEN", "")
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "")
DASHBOARD_INTERVAL = float(os.environ.get("DASHBOARD_INTERVAL", "4"))

MAX_DASHBOARD = 1900  # stay under Discord's 2000 char message limit

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="\u0000", intents=intents)
session: aiohttp.ClientSession | None = None
# channel_id -> {"id": row id, "dashboard": message id, "mode": ...}
bound: dict[int, dict] = {}


# --------------------------------------------------------------------------- API helper
class ApiError(Exception):
    pass


async def api(method, path, body=None, params=None):
    if session is None:
        raise ApiError("http session not ready")
    headers = {"X-MCMUSIC-BOT": BOT_TOKEN}
    async with session.request(
        method, f"{MCMUSIC_BASE}/api/{path.lstrip('/')}",
        json=body, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=20),
    ) as r:
        text = await r.text()
        try:
            data = await r.json()
        except Exception:
            raise ApiError(f"HTTP {r.status}: {text[:200]}")
        if r.status >= 400:
            raise ApiError(data.get("error") or f"HTTP {r.status}")
        return data


async def refresh_bindings():
    """Load bound channels from the server (survives bot restarts)."""
    try:
        data = await api("GET", "channels", params={"platform": "discord"})
    except Exception as e:
        print(f"[discord] could not load channels: {e}", flush=True)
        return
    bound.clear()
    for ch in data.get("channels", []):
        try:
            cid = int(ch["channel_id"])
        except (TypeError, ValueError):
            continue
        bound[cid] = {"id": ch["id"], "dashboard": ch.get("dashboard_id"),
                      "mode": ch.get("mode")}
    print(f"[discord] {len(bound)} control channel(s) bound", flush=True)


# --------------------------------------------------------------------------- dashboard
def dashboard_embed(state: dict) -> discord.Embed:
    t = state.get("now")
    if t:
        title = ("▶  " if state.get("playing") else "❚❚  ") + t["title"]
        desc = f"**{t['artist']}**"
        if t.get("album"):
            desc += f"  ·  *{t['album']}*"
        desc += (
            f"\n`{clock(state['position'])}` "
            f"{bar(state['progress'], 18)} "
            f"`{clock(state['duration'])}`"
        )
    else:
        title = "Nothing playing right now"
        desc = "Queue something with `/addtoqueue` to get things started."

    embed = discord.Embed(title=title[:256], description=desc, colour=0xD98A3D)
    queue = state.get("queue") or []
    if queue:
        embed.add_field(
            name="Up next",
            value="\n".join(
                f"`{i:>2}.` {q['title']} — {q['artist']}" for i, q in enumerate(queue[:8], 1)
            )[:1024],
            inline=False,
        )
    embed.add_field(
        name="Commands",
        value=" · ".join(f"`{i['command']}`" for i in state.get("legend", []))[:1024],
        inline=False,
    )
    embed.set_footer(text="mcmusic · control channel")
    return embed


def bar(pct, width=18):
    filled = int(round((pct or 0) * width))
    return "▰" * filled + "▱" * (width - filled)


def clock(v):
    v = max(0, int(round(v or 0)))
    return f"{v // 60}:{v % 60:02d}"


async def paint(channel_id: int):
    meta = bound.get(channel_id)
    if not meta:
        return
    channel = bot.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return
    try:
        state = await api("GET", f"channels/{meta['id']}/state")
    except Exception:
        return

    embed = dashboard_embed(state)
    mid = meta.get("dashboard")
    if mid:
        try:
            await channel.get_partial_message(int(mid)).edit(embed=embed)
            return
        except discord.NotFound:
            meta["dashboard"] = None
        except discord.Forbidden:
            return
        except Exception:
            meta["dashboard"] = None

    try:
        msg = await channel.send(embed=embed)
    except Exception as e:
        print(f"[discord] dashboard post failed in {channel_id}: {e}", flush=True)
        return
    meta["dashboard"] = msg.id
    try:
        await api("POST", f"channels/{meta['id']}/dashboard", {"message_id": str(msg.id)})
    except Exception:
        pass
    try:
        await msg.pin(reason="mcmusic dashboard")
    except Exception:
        pass


@tasks.loop(seconds=DASHBOARD_INTERVAL)
async def dashboard_loop():
    for cid in list(bound):
        await paint(cid)


@dashboard_loop.before_loop
async def before_dashboard():
    await bot.wait_until_ready()


# --------------------------------------------------------------------------- lifecycle
@bot.event
async def setup_hook():
    global session
    session = aiohttp.ClientSession()
    await refresh_bindings()
    if DISCORD_GUILD_ID:
        guild = discord.Object(id=int(DISCORD_GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
    else:
        await bot.tree.sync()


@bot.event
async def on_ready():
    print(f"[discord] logged in as {bot.user} ({bot.user.id})", flush=True)
    if not dashboard_loop.is_running():
        dashboard_loop.start()


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    meta = bound.get(message.channel.id)
    if meta:
        # Control channels are not chat. Slash commands never land here, so any
        # human message is noise and is removed immediately when we may.
        try:
            await message.delete()
        except discord.Forbidden:
            print(f"[discord] missing Manage Messages in {message.channel.id}", flush=True)
        except discord.NotFound:
            pass
        except Exception:
            pass
    await bot.process_commands(message)


@bot.event
async def on_guild_channel_delete(channel):
    meta = bound.pop(channel.id, None)
    if meta:
        try:
            await api("DELETE", f"channels/{meta['id']}")
        except Exception:
            pass


# --------------------------------------------------------------------------- helpers
async def guild_channel(interaction, channel):
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message("Pick a normal text channel.", ephemeral=True)
        return None
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "You need **Manage Server** to bind a music channel.", ephemeral=True)
        return None
    return channel


async def linked_uid(interaction):
    """Return the mcmusic user id linked to this Discord user, or None."""
    try:
        ctx = await api("GET", "bot/context",
                        params={"platform": "discord", "platform_user": str(interaction.user.id)})
    except ApiError as e:
        await interaction.followup.send(f"mcmusic error: {e}", ephemeral=True)
        return None
    if not ctx.get("linked"):
        await interaction.followup.send(
            "Link your account first with `/login`.", ephemeral=True)
        return None
    return ctx["me"]["id"]


async def control(interaction, action, **arg):
    uid = await linked_uid(interaction)
    if uid is None:
        return False
    try:
        await api("POST", "playback/command",
                  {"user_id": uid, "action": action, "track_id": arg.get("track_id"),
                   "index": arg.get("index")})
    except ApiError as e:
        await interaction.followup.send(f"Could not {action}: {e}", ephemeral=True)
        return False
    return True


async def bind_channel(interaction, channel, mode):
    channel = await guild_channel(interaction, channel)
    if channel is None:
        return
    await interaction.response.defer(ephemeral=True)

    uid = None
    try:
        ctx = await api("GET", "bot/context",
                        params={"platform": "discord", "platform_user": str(interaction.user.id)})
        if ctx.get("linked"):
            uid = ctx["me"]["id"]
    except Exception:
        pass

    try:
        data = await api("POST", "channels", {
            "platform": "discord", "channel_id": str(channel.id),
            "guild_id": str(channel.guild.id), "mode": mode,
            "owner_user_id": uid,
        })
    except ApiError as e:
        await interaction.followup.send(f"Could not bind: {e}", ephemeral=True)
        return

    row = data["channel"]
    bound[channel.id] = {"id": row["id"], "dashboard": None, "mode": mode}

    # Auto-purge: clear the backlog before the dashboard appears.
    purged = 0
    try:
        await channel.purge(limit=None, reason="mcmusic: music control channel")
        purged = -1
    except discord.Forbidden:
        pass
    except Exception:
        try:
            async for m in channel.history(limit=500):
                await m.delete()
                purged += 1
        except Exception:
            pass

    await paint(channel.id)
    label = "music control" if mode == "control" else "history"
    extra = "Cleared the existing history." if purged else "Couldn't clear history (missing permissions)."
    await interaction.followup.send(
        f"✅ {channel.mention} is now the {label} channel. {extra} "
        f"Casual messages here are deleted automatically.",
        ephemeral=True,
    )


# --------------------------------------------------------------------------- commands
@bot.tree.command(name="setmusicchannel", description="Bind a channel as the music control surface")
@app_commands.describe(channel="Text channel to turn into the mcmusic dashboard")
async def setmusicchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    await bind_channel(interaction, channel, "control")


@bot.tree.command(name="sethistorychannel", description="Bind a channel as the listening history surface")
@app_commands.describe(channel="Text channel to use for history and the dashboard")
async def sethistorychannel(interaction: discord.Interaction, channel: discord.TextChannel):
    await bind_channel(interaction, channel, "history")


@bot.tree.command(name="login", description="Link your Rotur account to mcmusic")
async def login_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        data = await api("POST", "bot/rotur-ticket",
                         {"platform": "discord", "platform_user": str(interaction.user.id)})
    except ApiError as e:
        await interaction.followup.send(f"Could not start login: {e}", ephemeral=True)
        return
    if data.get("already_linked"):
        note = "You are already linked. Re-run this to refresh the session if it expired.\n"
    else:
        note = ""
    await interaction.followup.send(
        f"{note}**Sign in with Rotur** (link expires in 10 minutes, single use):\n{data['url']}",
        ephemeral=True,
    )


@bot.tree.command(name="addtoqueue", description="Queue a YouTube link or a track from the library")
@app_commands.describe(query="YouTube URL or a track/artist name")
async def addtoqueue(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    payload = {"platform": "discord", "platform_user": str(interaction.user.id)}
    if query.startswith("http://") or query.startswith("https://"):
        payload["url"] = query
    else:
        payload["query"] = query
    try:
        data = await api("POST", "bot/enqueue", payload)
    except ApiError as e:
        await interaction.followup.send(f"❌ {e}")
        return
    if data.get("queued") == "download":
        await interaction.followup.send(f"⬇️ Downloading and queueing: <{query}>")
    else:
        t = data.get("track") or {}
        await interaction.followup.send(f"➕ Queued **{t.get('title','?')}** — {t.get('artist','')}")
    await paint(interaction.channel_id)


@bot.tree.command(name="removefromqueue", description="Remove an upcoming track by its position")
@app_commands.describe(position="1 for the next track, 2 for the one after, etc.")
async def removefromqueue(interaction: discord.Interaction, position: int):
    await interaction.response.defer()
    if position < 1:
        await interaction.followup.send("Position starts at 1.")
        return
    if await control(interaction, "remove", index=position - 1):
        await interaction.followup.send(f"✂️ Removed queue position {position}")
        await paint(interaction.channel_id)


@bot.tree.command(name="skip", description="Skip the current track")
async def skip_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    if await control(interaction, "skip"):
        await interaction.followup.send("⏭️ Skipped")
        await paint(interaction.channel_id)


@bot.tree.command(name="pause", description="Pause or resume playback")
async def pause_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    if await control(interaction, "toggle"):
        await interaction.followup.send("⏯️ Toggled playback")
        await paint(interaction.channel_id)


@bot.tree.command(name="np", description="Show what is playing right now")
async def np_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        ctx = await api("GET", "bot/context",
                        params={"platform": "discord", "platform_user": str(interaction.user.id)})
    except ApiError as e:
        await interaction.followup.send(f"mcmusic error: {e}")
        return
    pb = ctx.get("playback")
    if not pb or not pb.get("track"):
        await interaction.followup.send("Nothing’s playing right now. Try `/addtoqueue` to line something up.")
        return
    t = pb["track"]
    state_word = "playing" if pb["playing"] else "paused"
    await interaction.followup.send(
        f"**{t['title']}** — {t['artist']}\n"
        f"`{clock(pb['position'])} / {clock(pb['duration'])}` · {state_word}"
    )


@bot.tree.command(name="queue", description="Show the upcoming queue")
async def queue_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        data = await api("GET", "queue")
    except ApiError as e:
        await interaction.followup.send(f"mcmusic error: {e}")
        return
    q = data.get("queue") or []
    if not q:
        await interaction.followup.send("The queue is empty.")
        return
    lines = [f"`{i:>2}.` {t['title']} — {t['artist']}" for i, t in enumerate(q[:15], 1)]
    await interaction.followup.send("**Queue**\n" + "\n".join(lines))


@bot.tree.command(name="rescan", description="Ask mcmusic to rescan the library")
async def rescan_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("Manage Server required.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        data = await api("POST", "admin/scan")
    except ApiError as e:
        await interaction.followup.send(f"Scan failed: {e}", ephemeral=True)
        return
    await interaction.followup.send(
        f"Scanned: {data.get('tracks', 0)} tracks, {data.get('albums', 0)} albums.", ephemeral=True)


def main():
    if not DISCORD_BOT_TOKEN:
        print("[discord] DISCORD_BOT_TOKEN not set — not starting", flush=True)
        return
    if not BOT_TOKEN:
        print("[discord] MCMUSIC_BOT_TOKEN not set — API calls will be refused", flush=True)
    if os.environ.get("ORIGINCHATS_BASE"):
        from originchats import start_in_background
        start_in_background()
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        pass
    except discord.errors.PrivilegedIntentsRequired:
        print(
            "[discord] login refused: enable Message Content Intent under "
            "Bot -> Privileged Gateway Intents in the Discord Developer Portal.",
            flush=True,
        )


if __name__ == "__main__":
    main()

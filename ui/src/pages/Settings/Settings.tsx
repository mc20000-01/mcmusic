import { useCallback, useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import {
    Button, Container, Content, FormalInput, Header2, Header3, Input, Loading,
    Seperator, Slider, Text, TextIconButton, TextIconLinkButton, WrapList
} from "flufi-ui/components";
import {
    BookOpen, Check, CircleCheck, CircleDashed, Download, ExternalLink, KeyRound,
    Link2, LogOut, Mail, RefreshCw, Save, Send, Settings as SettingsGlyph,
    Smartphone, Sparkles, Unlink, WifiOff,
} from "lucide-preact";
import { API, userFromJson } from "../../common/net/api";
import { SELFHOST_GUIDE } from "../../common/links";
import type { DiscordStatus, RoturStatus } from "../../common/net/types";
import { currentUser, logout } from "../../common/auth";
import { activityError } from "../../common/player";
import { flushOutbox, pendingWrites } from "../../common/net/api";
import { PasswordInput } from "../../components/PasswordInput/PasswordInput";
import {
    applyPrefs, loadPrefs, playfulMotion, setAccentPreference, setAutoplayPreference,
    setIconFilledPreference, setIconStrokePreference, setPalettePreference,
    setPlayfulMotionPreference, type Settings as Prefs,
} from "../../common/prefs";
import {
    DEFAULT_ICON_STROKE, ICON_STROKE_CHOICES, PALETTE_FAMILIES, resolvePalette,
} from "../../common/theme";

import "./style.css";

// Every checkbox the legacy client exposed, as (server key, label) pairs.
// They are still stored server-side so Android/Qt keep honouring them.
const TOGGLES: [string, string][] = [
    ["covers", "Show cover art"],
    ["hide_explicit", "Hide explicit tracks"],
    ["autoplay", "Autoplay"],
    ["prefetch", "Prefetch the next track"],
    ["offline_audio", "Keep audio offline (downloads)"],
    ["remember_volume", "Remember volume"],
    ["private", "Private listening"],
    ["yt_stats", "Show YouTube stats"],
    ["rotur_activity", "Share as Rotur activity"],
    ["discord_activity", "Share as Discord activity"],
    ["show_room_url", "Show my room URL"],
];

/**
 * Settings page: account, linked services (Rotur + Discord), password, email,
 * builds/version, offline sync, volume and the server-stored preferences.
 */
export function SettingsPage() {
    const [settings, setSettings] = useState<Prefs | null>(null);
    const [loadFailed, setLoadFailed] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [dirty, setDirty] = useState(false);
    const [saving, setSaving] = useState(false);
    const oldPw = useSignal("");
    const newPw = useSignal("");
    const email = useSignal("");

    const [rotur, setRotur] = useState<RoturStatus | null>(null);
    const [roturError, setRoturError] = useState<string | null>(null);
    const [discord, setDiscord] = useState<DiscordStatus | null>(null);
    const [discordError, setDiscordError] = useState<string | null>(null);
    const [builds, setBuilds] = useState<any[]>([]);
    const [version, setVersion] = useState<any>(null);
    const [ping, setPing] = useState<any>(null);
    const [publicUrl, setPublicUrl] = useState<string | null>(null);
    const [pending, setPending] = useState(0);
    const [emailTarget, setEmailTarget] = useState("");

    const loadRotur = useCallback(async () => {
        try {
            setRotur(await API.roturStatus());
            setRoturError(null);
        } catch (e) {
            setRoturError(e instanceof Error ? e.message : String(e));
        }
    }, []);

    const loadDiscord = useCallback(async () => {
        try {
            setDiscord(await API.discordStatus() as DiscordStatus);
            setDiscordError(null);
        } catch (e) {
            setDiscordError(e instanceof Error ? e.message : String(e));
        }
    }, []);

    const loadMeta = useCallback(async () => {
        try {
            const [b, v, p, pg, pub] = await Promise.all([
                API.builds().catch(() => ({ builds: [] })),
                API.version().catch(() => null),
                pendingWrites().catch(() => 0),
                API.ping().catch(() => null),
                API.publicListening().catch(() => null),
            ]);
            setBuilds(b.builds ?? []);
            setVersion(v);
            setPing(pg);
            setPublicUrl(pub?.base_url ?? null);
            setPending(p);
        } catch { /* all sources are optional */ }
    }, []);

    useEffect(() => {
        loadPrefs().then(s => {
            setSettings(s ?? {});
            if (s == null) {
                setLoadFailed(true);
                setError("Could not load preferences. Saving is disabled so nothing is overwritten.");
            }
        });
        email.value = currentUser.value?.email ?? "";
        void loadMeta();
    }, []);

    // The OAuth redirect returns here; refresh both link states on focus and
    // visibility so neither is ever stale after a hand-off.
    useEffect(() => {
        void loadRotur();
        void loadDiscord();
        const refresh = () => {
            if (document.visibilityState === "visible") {
                void loadRotur();
                void loadDiscord();
                void loadMeta();
            }
        };
        document.addEventListener("visibilitychange", refresh);
        window.addEventListener("focus", refresh);
        return () => {
            document.removeEventListener("visibilitychange", refresh);
            window.removeEventListener("focus", refresh);
        };
    }, [loadRotur, loadDiscord, loadMeta]);

    function set(key: string, value: unknown) {
        setSettings(s => ({ ...(s ?? {}), [key]: value }));
        // Preview appearance changes before Save; Save mirrors them to the server.
        if (key === "theme") setPalettePreference(String(value));
        if (key === "accent") setAccentPreference(String(value ?? ""));
        if (key === "iconStroke") setIconStrokePreference(value);
        if (key === "iconFilled") setIconFilledPreference(value);
        setDirty(true);
        setMessage(null);
    }

    async function save() {
        if (loadFailed) return;
        setError(null);
        setMessage(null);
        setSaving(true);
        try {
            await API.saveSettings(settings ?? {});
            applyPrefs(settings ?? {});
            // Autoplay is mirrored locally for instant queue-toggle behavior.
            if (settings && "autoplay" in settings)
                setAutoplayPreference(settings.autoplay !== false);
            setDirty(false);
            setMessage("Preferences saved.");
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setSaving(false);
        }
    }

    async function changePassword() {
        setError(null);
        setMessage(null);
        try {
            await API.changePassword(oldPw.peek(), newPw.peek());
            oldPw.value = "";
            newPw.value = "";
            setMessage("Password changed.");
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function saveEmail() {
        setError(null);
        setMessage(null);
        try {
            const me = await API.setEmail(email.peek().trim());
            currentUser.value = userFromJson(me);
            setMessage("Email saved — password resets go there.");
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function unlinkRotur() {
        if (!window.confirm("Unlink Rotur from this account?")) return;
        setRoturError(null);
        try {
            await API.roturUnlink();
            await loadRotur();
            setMessage("Rotur account unlinked.");
        } catch (e) {
            setRoturError(e instanceof Error ? e.message : String(e));
        }
    }

    async function unlinkDiscord() {
        if (!window.confirm("Unlink Discord from this account?")) return;
        setDiscordError(null);
        try {
            await API.discordUnlink();
            await loadDiscord();
            setMessage("Discord account unlinked.");
        } catch (e) {
            setDiscordError(e instanceof Error ? e.message : String(e));
        }
    }

    async function emailBuild(kind: string) {
        setError(null);
        const target = emailTarget.trim() || email.peek().trim() || currentUser.value?.email || "";
        if (!target) {
            setError("Set an email address above first.");
            return;
        }
        try {
            await API.emailBuild(target, kind);
            setMessage(`Build link sent to ${target}.`);
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function syncNow() {
        try {
            const n = await flushOutbox();
            setPending(await pendingWrites());
            setMessage(n ? `Synced ${n} offline change${n === 1 ? "" : "s"}.` : "Everything is up to date.");
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    const roturLinked = rotur?.linked ?? false;
    const roturLabel = describeRotur(rotur);
    const roturDetail = activityError.value
        ? `Activity error: ${activityError.value}`
        : !rotur?.activity?.ready && roturLinked
            ? (rotur?.activity?.reason ?? "Activity is not ready.")
            : roturDetailReady(rotur);
    const discordLinked = discord?.linked ?? false;
    const discordLabel = describeDiscord(discord);
    const discordDetail = discordPresenceHint(discord?.presence ?? null);

    return (
        <Content class="settings">
            <Loading loaded={settings != null}>
                {() => (
                    <Container extra_gap>
                        <Header2>Settings</Header2>
                        {(message || error) && (
                            <span class={error ? "error status-line" : "status status-line"} role="status">
                                {error ?? message}
                            </span>
                        )}

                        <Container class="settings-card">
                            <Header3>Account</Header3>
                            <Text content={currentUser.value?.username ?? "—"} />
                            <Text dim content={currentUser.value?.is_admin ? "Administrator" : "Listener"} />
                            <TextIconButton onClick={() => logout().then(() => { window.location.href = "/auth"; })}>
                                <LogOut size={18} /> Log out
                            </TextIconButton>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Appearance</Header3>
                            <Text dim content="Palettes follow your device's light or dark setting. Pick a colour family, then save preferences." />
                            <WrapList min_size={150}>
                                {PALETTE_FAMILIES.map(f => {
                                    const active = resolvePalette(settings!.theme);
                                    const selected = active.family === f.id;
                                    const preview = f[active.mode];
                                    return (
                                        <Button
                                            key={f.id}
                                            class="palette-card"
                                            variant={selected ? "accent-subtle" : "panel"}
                                            title={`Use ${f.name} palette`}
                                            onClick={() => set("theme", f.id)}
                                        >
                                            <span
                                                class="palette-card-swatch"
                                                style={{ background: preview.bg, borderColor: preview.line }}
                                            >
                                                <span style={{ background: preview.accent }} />
                                            </span>
                                            <Text content={f.name} />
                                            {selected && <Check size={16} class="palette-card-check" />}
                                        </Button>
                                    );
                                })}
                            </WrapList>

                            <Text dim content="Icon width scales Lucide outlines. Filled mode fills circles and squares only; paths stay outlined." />
                            <WrapList min_size={110}>
                                {ICON_STROKE_CHOICES.map(choice => {
                                    const selected =
                                        Number(settings!.iconStroke ?? DEFAULT_ICON_STROKE) === choice;
                                    return (
                                        <Button
                                            key={choice}
                                            class="icon-choice"
                                            variant={selected ? "accent-subtle" : "panel"}
                                            title={`Use ${choice}x Lucide icons`}
                                            onClick={() => set("iconStroke", choice)}
                                        >
                                            <SettingsGlyph
                                                size={18}
                                                class="icon-choice-sample"
                                            />
                                            <Text content={`${choice}x`} />
                                            {selected && (
                                                <Check size={15} class="palette-card-check" />
                                            )}
                                        </Button>
                                    );
                                })}
                            </WrapList>
                            <Button
                                class="icon-toggle"
                                variant={settings!.iconFilled ? "accent-subtle" : "panel"}
                                onClick={() => set("iconFilled", !settings!.iconFilled)}
                            >
                                <CircleCheck size={16} />
                                <Text content="Filled icons" />
                                {!!settings!.iconFilled && (
                                    <Check size={15} class="palette-card-check" />
                                )}
                            </Button>
                            <Button
                                class="icon-toggle"
                                variant={playfulMotion.value ? "accent-subtle" : "panel"}
                                title="Stored on this device; reduced-motion settings still win"
                                onClick={() => setPlayfulMotionPreference(!playfulMotion.value)}
                            >
                                <Sparkles size={16} />
                                <Text content="Playful motion" />
                                {playfulMotion.value && (
                                    <Check size={15} class="palette-card-check" />
                                )}
                            </Button>
                            <Text dim content="Springs, shape morphs and the wavy progress bar follow this switch; your device's reduced-motion setting always wins." />
                        </Container>

                        <Seperator />

                        <Container class="settings-card selfhost-panel">
                            <Header3>Server &amp; self-hosting</Header3>
                            <Text dim content="This server's details and the guide to running your own." />
                            <div class="server-facts">
                                <Text content={location.origin} />
                                {publicUrl && publicUrl !== location.origin && (
                                    <Text dim content={`Public URL: ${publicUrl}`} />
                                )}
                                {settings!.room_url && (
                                    <Text dim content={`Room: ${settings!.room_url}`} />
                                )}
                                {ping && (
                                    <Text dim content={`${ping.service ?? "mcmusic"} API ${ping.api ?? 3} · uptime ${Math.round((ping.uptime ?? 0) / 60)} min`} />
                                )}
                                {version && (
                                    <Text dim content={`Build ${version.build ?? "?"} · shell ${version.shell ?? "?"}`} />
                                )}
                            </div>
                            <a class="selfhost-link" href={SELFHOST_GUIDE} target="_blank" rel="noopener noreferrer">
                                <BookOpen size={16} /> Self-hosting guide <ExternalLink size={13} />
                            </a>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Email</Header3>
                            <Text dim content="Password reset links and app downloads are sent here." />
                            <FormalInput label="Email address">
                                <Input
                                    value={email}
                                    placeholder="you@example.com"
                                    onInput={(v: string) => { email.value = v; }}
                                />
                            </FormalInput>
                            <TextIconButton variant="accent" onClick={saveEmail}>
                                <Mail size={16} /> Save email
                            </TextIconButton>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Rotur status</Header3>
                            <Container horizontal centered_y class="status-line" other={{ role: "status" }}>
                                {roturLinked && rotur?.session_valid
                                    ? <CircleCheck size={18} class="status-ok" />
                                    : <CircleDashed size={18} class="status-idle" />}
                                <Text content={roturLabel} />
                                <TextIconButton title="Refresh Rotur status" onClick={loadRotur}>
                                    <RefreshCw size={14} />
                                </TextIconButton>
                            </Container>
                            <Text dim class={roturLinked && !rotur?.activity?.ready ? "warning" : ""}
                                content={roturError ?? roturDetail} />
                            <Container horizontal centered_y wrap class="status-actions">
                                <TextIconLinkButton variant="accent" href={API.roturAuthorizeUrl()}>
                                    <Link2 size={16} /> {roturLinked ? "Reconnect Rotur" : "Sign in with Rotur"}
                                </TextIconLinkButton>
                                {roturLinked && (
                                    <TextIconButton variant="danger-subtle" onClick={unlinkRotur}>
                                        <Unlink size={16} /> Unlink
                                    </TextIconButton>
                                )}
                            </Container>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Discord</Header3>
                            <Container horizontal centered_y class="status-line" other={{ role: "status" }}>
                                {discordLinked && discord?.session_valid
                                    ? <CircleCheck size={18} class="status-ok" />
                                    : <CircleDashed size={18} class="status-idle" />}
                                <Text content={discordLabel} />
                                <TextIconButton title="Refresh Discord status" onClick={loadDiscord}>
                                    <RefreshCw size={14} />
                                </TextIconButton>
                            </Container>
                            <Text dim content={discordError ?? discordDetail} />
                            <Container horizontal centered_y wrap class="status-actions">
                                {discord?.configured ? (
                                    <TextIconLinkButton variant="accent" href={API.discordAuthorizeUrl()}>
                                        <Link2 size={16} /> {discordLinked ? "Reconnect Discord" : "Link Discord"}
                                    </TextIconLinkButton>
                                ) : (
                                    <TextIconButton
                                        variant="accent"
                                        disabled
                                        title="Set DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET on the server to enable linking"
                                    >
                                        <Link2 size={16} /> Link Discord
                                    </TextIconButton>
                                )}
                                {discordLinked && (
                                    <TextIconButton variant="danger-subtle" onClick={unlinkDiscord}>
                                        <Unlink size={16} /> Unlink
                                    </TextIconButton>
                                )}
                            </Container>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Change password</Header3>
                            <FormalInput label="Current password">
                                <PasswordInput value={oldPw} />
                            </FormalInput>
                            <FormalInput label="New password">
                                <PasswordInput value={newPw} />
                            </FormalInput>
                            <TextIconButton
                                variant="accent"
                                disabled={oldPw.value == "" || newPw.value.length < 6}
                                onClick={changePassword}
                            >
                                <KeyRound size={18} /> Change password
                            </TextIconButton>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Offline sync</Header3>
                            <Text dim content={`${pending} change${pending === 1 ? "" : "s"} waiting to sync.`} />
                            <Container horizontal centered_y wrap class="status-actions">
                                <TextIconButton variant="panel" disabled={pending === 0} onClick={syncNow}>
                                    <RefreshCw size={15} /> Sync now
                                </TextIconButton>
                                <WifiOff size={14} />
                                <Text dim content="Likes and playlist edits made offline are replayed." />
                            </Container>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Get the app</Header3>
                            {builds.length === 0
                                ? <Text dim content="No builds are published yet." />
                                : builds.map(b => (
                                    <Container horizontal centered_y wrap class="build-row" key={b.kind}>
                                        <Smartphone size={16} />
                                        <Container vertical class="build-meta">
                                            <Text content={b.label} />
                                            <Text dim content={b.available
                                                ? `${b.version || "latest"} · ${b.note || ""}`
                                                : "Not built yet"} />
                                        </Container>
                                        {b.available && (
                                            <>
                                                <a href={b.url} class="build-link" download>
                                                    <Download size={14} /> Download
                                                </a>
                                                <TextIconButton
                                                    title={`Email ${b.label} to ${emailTarget || "your address"}`}
                                                    onClick={() => emailBuild(b.kind)}
                                                >
                                                    <Send size={14} /> Email
                                                </TextIconButton>
                                            </>
                                        )}
                                    </Container>
                                ))}
                            <FormalInput label="Send a build to (optional)">
                                <Input value={emailTarget} placeholder="you@example.com"
                                    onInput={(v: string) => setEmailTarget(v)} />
                            </FormalInput>
                            <Text dim content="No build for your device? The self-hosting guide explains how to serve the web app and install clients yourself." />
                            <a class="selfhost-link compact" href={SELFHOST_GUIDE} target="_blank" rel="noopener noreferrer">
                                <BookOpen size={14} /> Read the guide <ExternalLink size={12} />
                            </a>
                        </Container>

                        <Seperator />

                        <Container class="settings-card">
                            <Header3>Playback</Header3>
                            <Container horizontal centered_y>
                                <Text content={`Volume ${Math.round(Number(settings!.volume ?? 0.8) * 100)}%`} />
                                <Slider
                                    value={Number(settings!.volume ?? 0.8)}
                                    start={0} end={1} step={0.01}
                                    onChange={(v) => set("volume", v)}
                                    class="grow"
                                />
                            </Container>
                            <WrapList min_size={160}>
                                {TOGGLES.map(([key, label]) => (
                                    <Button
                                        key={key}
                                        variant={settings![key] ? "accent-subtle" : "panel"}
                                        title={settings![key] ? "On" : "Off"}
                                        onClick={() => set(key, !settings![key])}
                                    >
                                        {settings![key] && <Check size={15} />}
                                        {label}
                                    </Button>
                                ))}
                            </WrapList>
                            <Container horizontal centered_y class="save-row">
                                <TextIconButton
                                    variant="accent"
                                    disabled={saving || !dirty || loadFailed}
                                    onClick={save}
                                >
                                    <Save size={18} /> {saving ? "Saving…" : "Save preferences"}
                                </TextIconButton>
                                {dirty && !loadFailed && <Text dim content="Unsaved changes" />}
                            </Container>
                            <Text dim content="Stored on the server and shared with the Android/Qt clients." />
                        </Container>

                        {settings!.room_url && (
                            <Container class="settings-card">
                                <Header3>Listen along</Header3>
                                <Text selectable content={String(settings!.room_url)} />
                            </Container>
                        )}
                    </Container>
                )}
            </Loading>
        </Content>
    )
}

/** Legacy RoturLink.describe(): explain what the server can actually do. */
function describeRotur(s: RoturStatus | null): string {
    if (!s) return "Checking link status…";
    if (!s.configured) return "RoturLink is not configured on this server.";
    if (!s.linked) return "Not linked — sign in with Rotur to share activity.";
    if (!s.session_valid) return "Linked, but the session needs a refresh — sign in again.";
    return `Linked as @${s.rotur_username || s.rotur_id || "Rotur"}`;
}

function roturDetailReady(s: RoturStatus | null): string {
    if (!s) return "Checking link status…";
    if (!s.linked) return "Linking shares what you play as Rotur activity.";
    if (!s.activity.ready) return s.activity.reason;
    return "Activity sharing is ready.";
}

function describeDiscord(s: DiscordStatus | null): string {
    if (!s) return "Checking link status…";
    if (!s.configured)
        return `Discord linking needs ${(s.missing?.length ? s.missing : ["DISCORD_CLIENT_SECRET"]).join(" and ")}`;
    if (!s.linked) return "Not linked — control channels can still use /login";
    if (!s.session_valid) return `Linked as ${s.discord_username || s.discord_id} (refresh needed)`;
    return `Linked as ${s.discord_username || s.discord_id}`;
}

function discordPresenceHint(presence: DiscordStatus["presence"]): string {
    if (!presence) return "Shares what you play in your Discord profile when the toggle is on.";
    if (!presence.configured)
        return "Needs a Discord application id on the server (DISCORD_CLIENT_ID is enough).";
    if (!presence.available)
        return "The Discord desktop app has to run on the server — it isn't running right now.";
    return "Shares what you play in your Discord profile, with a link to the track.";
}

import { useCallback, useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import {
    Button, Container, Content, FormalInput, Header2, Header3, Loading,
    Seperator, Slider, Text, TextIconButton, TextIconLinkButton, WrapList
} from "flufi-ui/components";
import {
    Check, CircleCheck, CircleDashed, KeyRound, Link2, LogOut, RefreshCw,
    Save, Unlink,
} from "lucide-preact";
import { API } from "../../common/net/api";
import type { RoturStatus } from "../../common/net/types";
import { currentUser, logout } from "../../common/auth";
import { activityError } from "../../common/player";
import { PasswordInput } from "../../components/PasswordInput/PasswordInput";
import { applyPrefs, loadPrefs, type Settings as Prefs } from "../../common/prefs";

import "./style.css";

// Every checkbox the legacy client exposed, as (server key, label) pairs.
// They are still stored server-side so Android/Qt keep honouring them.
const TOGGLES: [string, string][] = [
    ["covers", "Show cover art"],
    ["hide_explicit", "Hide explicit tracks"],
    ["autoplay", "Autoplay"],
    ["prefetch", "Prefetch the next track"],
    ["offline_audio", "Keep audio offline (legacy client)"],
    ["remember_volume", "Remember volume"],
    ["private", "Private listening"],
    ["yt_stats", "Show YouTube stats"],
    ["rotur_activity", "Share as Rotur activity"],
    ["discord_activity", "Share as Discord activity"],
    ["show_room_url", "Show my room URL"],
];

/**
 * Settings page: account, linked services, password, volume and the
 * server-stored preference flags.
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

    const [rotur, setRotur] = useState<RoturStatus | null>(null);
    const [roturError, setRoturError] = useState<string | null>(null);

    const loadRotur = useCallback(async () => {
        try {
            setRotur(await API.roturStatus());
            setRoturError(null);
        } catch (e) {
            setRoturError(e instanceof Error ? e.message : String(e));
        }
    }, []);

    useEffect(() => {
        loadPrefs().then(s => {
            setSettings(s ?? {});
            if (s == null) {
                setLoadFailed(true);
                setError("Could not load preferences. Saving is disabled so nothing is overwritten.");
            }
        });
    }, []);

    // The OAuth redirect returns here; refresh the status when the tab is
    // visible or focused again so the link state is never stale.
    useEffect(() => {
        void loadRotur();
        const refresh = () => {
            if (document.visibilityState === "visible") void loadRotur();
        };
        document.addEventListener("visibilitychange", refresh);
        window.addEventListener("focus", refresh);
        return () => {
            document.removeEventListener("visibilitychange", refresh);
            window.removeEventListener("focus", refresh);
        };
    }, [loadRotur]);

    function set(key: string, value: unknown) {
        setSettings(s => ({ ...(s ?? {}), [key]: value }));
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

    const roturLinked = rotur?.linked ?? false;
    const roturLabel = roturLinked
        ? `Linked as @${rotur?.rotur_username || rotur?.rotur_id || "Rotur"}`
        : "Not linked";
    const roturDetail = activityError.value
        ? `Activity error: ${activityError.value}`
        : !rotur
            ? "Checking link status…"
            : !rotur.configured
                ? "RoturLink is not configured on this server."
                : rotur.activity.ready
                    ? "Activity sharing is ready."
                    : rotur.activity.reason;

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

                        <Container>
                            <Header3>Account</Header3>
                            <Text content={currentUser.value?.username ?? "—"} />
                            {currentUser.value?.email && <Text dim content={currentUser.value.email} />}
                            <Text dim content={currentUser.value?.is_admin ? "Administrator" : "Listener"} />
                            <TextIconButton onClick={() => logout().then(() => { window.location.href = "/auth"; })}>
                                <LogOut size={18} /> Log out
                            </TextIconButton>
                        </Container>

                        <Seperator />

                        <Container>
                            <Header3>Rotur status</Header3>
                            <Container horizontal centered_y class="status-line" other={{ role: "status" }}>
                                {roturLinked
                                    ? <CircleCheck size={18} class="status-ok" />
                                    : <CircleDashed size={18} class="status-idle" />}
                                <Text content={roturLabel} />
                                <TextIconButton title="Refresh Rotur status" onClick={loadRotur}>
                                    <RefreshCw size={14} />
                                </TextIconButton>
                            </Container>
                            <Text dim class={roturLinked && !rotur?.activity.ready ? "warning" : ""}
                                content={roturError ?? roturDetail} />
                            <Container horizontal centered_y wrap class="status-actions">
                                <TextIconLinkButton
                                    variant="accent"
                                    href={`/api/auth/rotur/authorize?next=${encodeURIComponent("/settings")}`}
                                >
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

                        <Container>
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

                        <Container>
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
                            <Text dim content="Stored on the server and shared with the Android/Qt/legacy clients." />
                        </Container>

                        {settings!.room_url && (
                            <Container>
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

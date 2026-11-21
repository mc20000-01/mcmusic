import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import {
    Button, Container, Content, FormalInput, Header2, Header3, Loading,
    Seperator, Slider, Text, TextIconButton, WrapList
} from "flufi-ui/components";
import { Check, KeyRound, LogOut, Save } from "lucide-preact";
import { API } from "../../common/net/api";
import { currentUser, logout } from "../../common/auth";
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
 * Settings page: account, password, volume and the server-stored preference
 * flags. Only flufi-ui primitives are used here, so the page inherits the
 * package's spacing, colours and focus rings.
 */
export function SettingsPage() {
    const [settings, setSettings] = useState<Prefs | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [dirty, setDirty] = useState(false);
    const [saving, setSaving] = useState(false);
    const oldPw = useSignal("");
    const newPw = useSignal("");

    useEffect(() => {
        loadPrefs()
            .then(s => setSettings(s ?? {}))
            .catch(e => {
                // Render the form with defaults rather than an endless spinner;
                // saving will surface the real error if the server is down.
                setSettings({});
                setError(e instanceof Error ? e.message : String(e));
            });
    }, []);

    function set(key: string, value: unknown) {
        setSettings(s => ({ ...(s ?? {}), [key]: value }));
        setDirty(true);
        setMessage(null);
    }

    async function save() {
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

    return (
        <Content class="settings">
            <Loading loaded={settings != null}>
                {() => (
                    <Container extra_gap>
                        <Header2>Settings</Header2>
                        {(message || error) && (
                            <Text
                                class={error ? "error" : "status"}
                                role="status"
                                content={error ?? message!}
                            />
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
                                    disabled={saving || !dirty}
                                    onClick={save}
                                >
                                    <Save size={18} /> {saving ? "Saving…" : "Save preferences"}
                                </TextIconButton>
                                {dirty && <Text dim content="Unsaved changes" />}
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

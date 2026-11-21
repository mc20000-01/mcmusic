/** Device pairing: mint a one-time code, list the account's devices and
 * long-lived tokens, and let the user promote, rename or forget them.
 *
 * Devices are de-duplicated by their stable device_hash (the identity a
 * paired client re-uses on every heartbeat). A device counts as "online" when
 * it was seen in the last 60 s. The list refreshes on a poll while the page
 * is open.
 */
import { useEffect, useState, useRef } from "preact/hooks";
import {
    Container, Content, Header2, Header3, IconButton, Loading, Seperator, Text, TextIconButton
} from "flufi-ui/components";
import { Check, Copy, KeyRound, MonitorSmartphone, RefreshCw, Trash2, X } from "lucide-preact";
import { API } from "../../common/net/api";
import { formatTime } from "../../common/player";

import "./style.css";

/** Relative "x ago" label; under 7 days relative, otherwise an absolute date.
   The full ISO timestamp goes in a tooltip. */
function when(ts?: number | null): { label: string; title: string } {
    if (!ts) return { label: "—", title: "never seen" };
    const now = Date.now() / 1000;
    const diff = now - ts;
    const date = new Date(ts * 1000);
    const title = date.toLocaleString();
    if (diff < 90) return { label: "just now", title };
    if (diff < 3600) return { label: `${Math.round(diff / 60)} min ago`, title };
    if (diff < 86400) return { label: `${Math.round(diff / 3600)} h ago`, title };
    if (diff < 7 * 86400) return { label: `${Math.round(diff / 86400)} d ago`, title };
    return { label: date.toLocaleDateString(), title };
}

function countdown(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
}

/** Guess a short OS/browser label from the user agent. */
function deviceLabel(ua?: string | null): string {
    const u = (ua || "").toLowerCase();
    if (u.includes("iphone") || u.includes("ipad")) return "iOS";
    if (u.includes("android")) return "Android";
    if (u.includes("windows")) return "Windows";
    if (u.includes("macintosh") || u.includes("mac os")) return "Mac";
    if (u.includes("linux")) return "Linux";
    if (u.includes("chromebook") || u.includes("cros")) return "ChromeOS";
    return "Device";
}

export function DevicesPage() {
    const [code, setCode] = useState<{ code: string; expires: number; hint?: string } | null>(null);
    const [devices, setDevices] = useState<any[] | null>(null);
    const [tokens, setTokens] = useState<any[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);
    const [now, setNow] = useState(() => Date.now());
    const [activating, setActivating] = useState<number | null>(null);
    const [renaming, setRenaming] = useState<number | null>(null);
    const renameInput = useRef<HTMLInputElement>(null);

    // De-duplicate devices by their stable device_hash so the same phone
    // doesn't appear twice under slightly different names.
    function dedupe(list: any[]): any[] {
        const seen = new Set<string>();
        return list.filter(d => {
            const key = d.device_hash || String(d.id);
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    }

    function load() {
        setLoading(true);
        setError(null);
        Promise.all([
            API.devices().then(d => setDevices(dedupe(d.devices ?? []))),
            API.deviceTokens().then(d => setTokens(d.tokens ?? [])),
        ])
            .catch(e => {
                setError(e instanceof Error ? e.message : String(e));
                setDevices(d => d ?? []);
                setTokens(t => t ?? []);
            })
            .finally(() => setLoading(false));
    }
    useEffect(load, []);

    // Re-poll every ~10 s so presence and "now playing" stay fresh.
    useEffect(() => {
        const timer = setInterval(load, 10000);
        return () => clearInterval(timer);
    }, []);

    // The pairing code only lives five minutes; tick so the countdown and the
    // "expired" state are truthful without a refresh.
    useEffect(() => {
        if (!code) return;
        setNow(Date.now());
        const timer = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(timer);
    }, [code]);

    const remaining = code ? Math.max(0, Math.round(code.expires - now / 1000)) : 0;
    const expired = code != null && remaining <= 0;

    async function act(fn: () => Promise<unknown>) {
        setError(null);
        try { await fn(); load(); }
        catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    }

    function confirmAct(message: string, fn: () => Promise<unknown>) {
        if (window.confirm(message)) act(fn);
    }

    async function copyCode() {
        if (!code) return;
        try {
            await navigator.clipboard.writeText(code.code);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch {
            // Clipboard access can be denied; the code is selectable anyway.
        }
    }

    async function renameDevice(id: number) {
        const input = renameInput.current;
        const name = (input?.value ?? "").trim();
        if (!name) return;
        setRenaming(id);
        try {
            await API.renameDevice(id, name);
            input.value = "";
            setRenaming(null);
            load();
        } catch (e) {
            setRenaming(null);
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function forgetDevice(id: number) {
        if (!window.confirm("Forget this device? It will need to be paired again.")) return;
        try {
            await API.forgetDevice(id);
            load();
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function activateDevice(id: number) {
        setActivating(id);
        try {
            await API.activateDevice(id);
            setActivating(null);
            load();
        } catch (e) {
            setActivating(null);
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    return (
        <Content class="devices">
            <Container extra_gap>
                <Header2>Devices</Header2>
                {error && <Text class="error" role="status" content={error} />}

                <Container>
                    <Header3>Pair a device</Header3>
                    <Text dim content="Mint a one-time code, then enter it in the app you want to sign in. It works once, for five minutes." />
                    <Container horizontal centered_y wrap class="pair-row">
                        <TextIconButton
                            variant="accent"
                            onClick={async () => {
                                setError(null);
                                try {
                                    setCode(await API.deviceCode());
                                    setCopied(false);
                                } catch (e) {
                                    setError(e instanceof Error ? e.message : String(e));
                                }
                            }}
                        >
                            <KeyRound size={18} /> Get pairing code
                        </TextIconButton>
                        {code && (
                            <Container horizontal centered_y class="pair-code">
                                <Text
                                    selectable
                                    extra_big
                                    class={expired ? "code expired" : "code"}
                                    content={code.code}
                                />
                                <IconButton
                                    title="Copy pairing code"
                                    onClick={copyCode}
                                    disabled={expired}
                                >
                                    {copied ? <Check size={15} /> : <Copy size={15} />}
                                </IconButton>
                                <Text
                                    dim
                                    class="code-ttl"
                                    content={expired
                                        ? "Expired — get a new code"
                                        : `Expires in ${countdown(remaining)}`}
                                />
                            </Container>
                        )}
                        {code?.hint && <Text dim content={code.hint} />}
                    </Container>
                </Container>

                <Seperator />

                <Container>
                    <Container horizontal centered_y wrap class="section-head">
                        <Header3>This account's devices</Header3>
                        <IconButton title="Refresh devices" onClick={load}>
                            <RefreshCw size={15} />
                        </IconButton>
                        <TextIconButton
                            onClick={() => confirmAct(
                                "Remove devices not seen in 30+ days?",
                                () => API.cleanupDevices(),
                            )}
                        >
                            Clean up stale
                        </TextIconButton>
                        <TextIconButton
                            onClick={() => confirmAct(
                                "Forget every device? You will need to pair them again.",
                                () => API.clearDevices(),
                            )}
                        >
                            Forget all
                        </TextIconButton>
                    </Container>
                    <Loading loaded={!loading || devices != null}>
                        {() => {
                            const list = devices == null ? [] : devices;
                            if (list.length == 0) return <Text dim content="No devices yet." />;
                            return (
                                <>
                                    {list.map(d => {
                                        const { label, title } = when(d.last_seen);
                                        const online = d.last_seen && (Date.now() / 1000 - d.last_seen) < 60;
                                        const isActive = d.is_active;
                                        const track = d.track_title ? ` · ${d.track_title}` : "";
                                        const displayName = d.name || d.user_agent || "Unknown device";
                                        return (
                                            <Container box key={d.id} class="device">
                                                <Container horizontal centered_y wrap class="device-head">
                                                    <span class="device-icon" title={deviceLabel(d.user_agent)} aria-hidden="true" />
                                                    <Container horizontal centered_y class="device-name-wrap">
                                                        {renaming === d.id ? (
                                                            <input
                                                                ref={renameInput}
                                                                class="rename-input"
                                                                defaultValue={displayName}
                                                                autoFocus
                                                                onBlur={() => renameDevice(d.id)}
                                                                onKeyDown={(e: any) => {
                                                                    if (e.key === "Enter") renameDevice(d.id);
                                                                    if (e.key === "Escape") { setRenaming(null); load(); }
                                                                }}
                                                            />
                                                        ) : (
                                                            <>
                                                                <Text
                                                                    class="device-name"
                                                                    content={`${displayName}${isActive ? " · active speaker" : ""}`}
                                                                />
                                                                {isActive && (
                                                                    <Text dim class="online-dot" title="Online (seen in the last minute)">●</Text>
                                                                )}
                                                                {!isActive && online && (
                                                                    <Text dim class="online-dot" title={title}>●</Text>
                                                                )}
                                                            </>
                                                        )}
                                                    </Container>
                                                    <IconButton
                                                        title={renaming === d.id ? "Cancel" : "Rename"}
                                                        onClick={() => setRenaming(renaming === d.id ? null : d.id)}
                                                        disabled={renaming != null && renaming !== d.id}
                                                    >
                                                        <X size={13} />
                                                    </IconButton>
                                                    {!isActive && (
                                                        <TextIconButton
                                                            disabled={activating != null && activating !== d.id}
                                                            onClick={() => activateDevice(d.id)}
                                                        >
                                                            {activating === d.id ? "Activating…" : <MonitorSmartphone size={15} />}
                                                        </TextIconButton>
                                                    )}
                                                    <IconButton
                                                        title="Forget device"
                                                        variant="danger-subtle"
                                                        onClick={() => forgetDevice(d.id)}
                                                    >
                                                        <Trash2 size={15} />
                                                    </IconButton>
                                                </Container>
                                                <Text
                                                    dim
                                                    class="device-meta"
                                                    title={title}
                                                    content={`${deviceIp(d)}${track} · seen ${label}`}
                                                />
                                            </Container>
                                        );
                                    })}
                                </>
                            );
                        }}
                    </Loading>
                </Container>

                <Seperator />

                <Container>
                    <Header3>Sign-in tokens</Header3>
                    <Text dim content="Long-lived credentials for native clients. Revoking one signs that client out." />
                    <Loading loaded={!loading || tokens != null}>
                        {() => tokens == null || tokens.length == 0
                            ? <Text dim content="No tokens." />
                            : tokens.map(t => (
                                <Container box class="device">
                                    <Text class="device-name" content={`mcd_${t.prefix}… · ${t.name || "unnamed"}`} />
                                    <Text
                                        dim
                                        class="device-meta"
                                        content={`created ${when(t.created).label} · last used ${when(t.last_used).label}${t.revoked ? " · revoked" : ""}`}
                                    />
                                    {!t.revoked && (
                                        <IconButton
                                            title="Revoke token"
                                            variant="danger-subtle"
                                            onClick={() => confirmAct(
                                                "Revoke this token? That client will be signed out.",
                                                () => API.revokeDeviceToken(t.id),
                                            )}
                                        >
                                            <Trash2 size={15} />
                                        </IconButton>
                                    )}
                                </Container>
                            ))}
                    </Loading>
                </Container>
            </Container>
        </Content>
    );
}

function deviceIp(d: any): string {
    const ip = d.ip ?? "unknown IP";
    // Show the real client IP; 127.0.0.1 means the reverse proxy isn't
    // forwarding X-Forwarded-For (see ProxyFix in mcmusic.py).
    return ip;
}

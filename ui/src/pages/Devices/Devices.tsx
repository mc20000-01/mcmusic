import { useEffect, useState } from "preact/hooks";
import {
    Container, Content, Header2, Header3, IconButton, Loading, Seperator, Text, TextIconButton
} from "flufi-ui/components";
import { Check, Copy, KeyRound, MonitorSmartphone, RefreshCw, Trash2 } from "lucide-preact";
import { API } from "../../common/net/api";

import "./style.css";

/** Relative "x ago" label for the timestamps the device API returns (unix seconds). */
function when(ts?: number | null): string {
    if (!ts) return "—";
    const diff = Date.now() / 1000 - ts;
    if (diff < 90) return "just now";
    if (diff < 3600) return `${Math.round(diff / 60)} min ago`;
    if (diff < 86400) return `${Math.round(diff / 3600)} h ago`;
    return new Date(ts * 1000).toLocaleDateString();
}

function countdown(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
}

/**
 * Device pairing: mint a one-time code, list the account's devices and
 * long-lived tokens, and let the user promote or revoke them.
 */
export function DevicesPage() {
    const [code, setCode] = useState<{ code: string; expires: number; hint?: string } | null>(null);
    const [devices, setDevices] = useState<any[] | null>(null);
    const [tokens, setTokens] = useState<any[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);
    const [now, setNow] = useState(() => Date.now());

    function load() {
        setLoading(true);
        setError(null);
        Promise.all([
            API.devices().then(d => setDevices(d.devices ?? [])),
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
                    </Container>
                    {code?.hint && <Text dim content={code.hint} />}
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
                                "Forget every device? You will need to pair them again.",
                                () => API.clearDevices(),
                            )}
                        >
                            Forget all
                        </TextIconButton>
                    </Container>
                    <Loading loaded={!loading || devices != null}>
                        {() => devices == null || devices.length == 0
                            ? <Text dim content="No devices yet." />
                            : devices.map(d => (
                                <Container box class="device">
                                    <Text
                                        class="device-name"
                                        content={`${d.name || d.user_agent || "Unknown device"}${d.is_active ? " · active speaker" : ""}`}
                                    />
                                    <Text
                                        dim
                                        class="device-meta"
                                        content={`${d.ip ?? "unknown IP"} · seen ${when(d.last_seen)}${d.track_title ? ` · ${d.track_title}` : ""}`}
                                    />
                                    {!d.is_active && (
                                        <TextIconButton onClick={() => act(() => API.activateDevice(d.id))}>
                                            <MonitorSmartphone size={15} /> Make active
                                        </TextIconButton>
                                    )}
                                </Container>
                            ))}
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
                                        content={`created ${when(t.created)} · last used ${when(t.last_used)}${t.revoked ? " · revoked" : ""}`}
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
    )
}

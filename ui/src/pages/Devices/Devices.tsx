import { useEffect, useState } from "preact/hooks";
import {
    Container, Content, Header2, Header3, IconButton, Loading, Seperator, Text, TextIconButton
} from "flufi-ui/components";
import { KeyRound, MonitorSmartphone, RefreshCw, Trash2 } from "lucide-preact";
import { API } from "../../common/net/api";

/** Relative "x ago" label for the timestamps the device API returns (unix seconds). */
function when(ts?: number | null): string {
    if (!ts) return "—";
    const diff = Date.now() / 1000 - ts;
    if (diff < 90) return "just now";
    if (diff < 3600) return `${Math.round(diff / 60)} min ago`;
    if (diff < 86400) return `${Math.round(diff / 3600)} h ago`;
    return new Date(ts * 1000).toLocaleDateString();
}

/**
 * Device pairing: mint a one-time code, list the account's devices and
 * long-lived tokens, and let the user promote or revoke them.
 */
export function DevicesPage() {
    const [code, setCode] = useState<{ code: string; expires: number; hint?: string } | null>(null);
    const [devices, setDevices] = useState<any[] | null>(null);
    const [tokens, setTokens] = useState<any[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    function load() {
        API.devices().then(d => setDevices(d.devices ?? [])).catch(e => setError(String(e)));
        API.deviceTokens().then(d => setTokens(d.tokens ?? [])).catch(e => setError(String(e)));
    }
    useEffect(load, []);

    async function act(fn: () => Promise<unknown>) {
        setError(null);
        try { await fn(); load(); }
        catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    }

    return (
        <Content class="devices">
            <Container extra_gap>
                <Header2>Devices</Header2>
                {error && <Text class="error" content={error} />}

                <Container>
                    <Header3>Pair a device</Header3>
                    <Text dim content="Mint a one-time code, then enter it in the app you want to sign in. It works once, for five minutes." />
                    <Container horizontal centered_y wrap>
                        <TextIconButton
                            variant="accent"
                            onClick={async () => {
                                setError(null);
                                try { setCode(await API.deviceCode()); }
                                catch (e) { setError(e instanceof Error ? e.message : String(e)); }
                            }}
                        >
                            <KeyRound size={18} /> Get pairing code
                        </TextIconButton>
                        {code && <Text selectable extra_big content={code.code} />}
                    </Container>
                    {code?.hint && <Text dim content={code.hint} />}
                </Container>

                <Seperator />

                <Container>
                    <Container horizontal centered_y>
                        <Header3>This account's devices</Header3>
                        <IconButton title="Refresh" onClick={load}><RefreshCw size={15} /></IconButton>
                        <TextIconButton onClick={() => act(() => API.clearDevices())}>Forget all</TextIconButton>
                    </Container>
                    <Loading loaded={devices != null}>
                        {() => devices!.length == 0
                            ? <Text dim content="No devices yet." />
                            : devices!.map(d => (
                                <Container box>
                                    <Text content={`${d.name || d.user_agent || "Unknown device"}${d.is_active ? " · active speaker" : ""}`} />
                                    <Text dim content={`${d.ip} · seen ${when(d.last_seen)}${d.track_title ? ` · ${d.track_title}` : ""}`} />
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
                    <Loading loaded={tokens != null}>
                        {() => tokens!.length == 0
                            ? <Text dim content="No tokens." />
                            : tokens!.map(t => (
                                <Container box>
                                    <Text content={`mcd_${t.prefix}… · ${t.name || "unnamed"}`} />
                                    <Text dim content={`created ${when(t.created)} · last used ${when(t.last_used)}${t.revoked ? " · revoked" : ""}`} />
                                    {!t.revoked && (
                                        <IconButton title="Revoke" variant="danger-subtle" onClick={() => act(() => API.revokeDeviceToken(t.id))}>
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

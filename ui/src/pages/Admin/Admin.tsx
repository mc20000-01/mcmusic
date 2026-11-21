import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import {
    Container, Content, FormalInput, Header2, Header3, IconButton, Input, Loading,
    Seperator, Table, TableBody, TableCell, TableRow, Tabs, Text, TextIconButton
} from "flufi-ui/components";
import { Ban, Check, FileText, RefreshCw, RotateCcw, ScanLine, Trash2, X } from "lucide-preact";
import { API } from "../../common/net/api";

import "./style.css";

// Four panes, one per admin endpoint group. Tabs is flufi-ui's own control,
// so the admin view looks like the rest of the client.
type Tab = "overview" | "requests" | "users" | "invites";

function when(ts?: number | null): string {
    if (!ts) return "—";
    return new Date(ts * 1000).toLocaleString();
}

export function AdminPage() {
    const [tab, setTab] = useState<Tab>("overview");
    return (
        <Content class="admin" wrapped>
            <Container extra_gap>
                <Header2>Admin</Header2>
                <Tabs
                    value={tab}
                    tabs={[
                        { name: "Overview", value: "overview" },
                        { name: "Requests", value: "requests" },
                        { name: "Users", value: "users" },
                        { name: "Invites", value: "invites" },
                    ]}
                    onChange={(v) => setTab(v as Tab)}
                />
                {tab == "overview" && <Overview />}
                {tab == "requests" && <Requests />}
                {tab == "users" && <Users />}
                {tab == "invites" && <Invites />}
            </Container>
        </Content>
    )
}

/** Library stats and the scan button. */
function Overview() {
    const [data, setData] = useState<any>(null);
    const [message, setMessage] = useState<string | null>(null);
    const [scanning, setScanning] = useState(false);
    const [rooms, setRooms] = useState<any[] | null>(null);

    function load() {
        API.adminStats()
            .then(d => { setData(d); setMessage(null); })
            .catch(e => setMessage(e instanceof Error ? e.message : String(e)));
        API.adminRooms()
            .then(d => setRooms(d.rooms ?? []))
            .catch(() => setRooms([]));
    }
    useEffect(load, []);

    async function scan() {
        setScanning(true);
        setMessage("Scanning…");
        try {
            const r = await API.adminScan();
            setMessage(`Scanned ${r.tracks} tracks, ${r.albums} albums.`);
            load();
        } catch (e) {
            setMessage(e instanceof Error ? e.message : String(e));
        } finally {
            setScanning(false);
        }
    }

    async function closeRoom(code: string) {
        if (!window.confirm(`Close room ${code}?`)) return;
        try {
            await API.adminCloseRoom(code);
            load();
        } catch (e) {
            setMessage(e instanceof Error ? e.message : String(e));
        }
    }

    const diskPct = data && data.disk_total
        ? Math.round((data.disk_used / data.disk_total) * 100)
        : 0;

    return (
        <Loading loaded={data != null}>
            {() => (
                <Container extra_gap>
                    <Table>
                        <TableBody>
                            {[
                                ["Users", data.users], ["Admins", data.admins], ["Tracks", data.tracks],
                                ["Albums", data.albums], ["Playlists", data.playlists], ["Plays", data.plays],
                                ["Queue", data.queue],
                            ].map(([label, value]) => (
                                <TableRow>
                                    <TableCell><Text dim content={String(label)} /></TableCell>
                                    <TableCell><Text content={String(value)} /></TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    <Header3>Requests by status</Header3>
                    <Text dim content={Object.entries(data.requests ?? {}).map(([k, v]) => `${k}: ${v}`).join(", ") || "none"} />
                    <Header3>Disk</Header3>
                    <Text dim content={`${(data.disk_used / 1e9).toFixed(1)} GB used of ${(data.disk_total / 1e9).toFixed(1)} GB (${diskPct}%) • ${(data.disk_free / 1e9).toFixed(1)} GB free`} />
                    <Header3>Active downloads</Header3>
                    <Text dim content={`Queue length: ${data.queue ?? 0} • Running: ${Array.isArray(data.running) ? data.running.length : 0} • Rooms: ${data.rooms ?? 0}`} />
                    <Header3>Rooms</Header3>
                    {!rooms || rooms.length === 0 ? (
                        <Text dim content="No active rooms." />
                    ) : (
                        rooms.map((r: any) => (
                            <Container class="req">
                                <Container horizontal centered_y wrap class="req-head">
                                    <Text content={`${r.code} · host ${r.host ?? "?"}${r.track?.title ? ` · ${r.track.title}` : ""}`} />
                                    <IconButton title="Close room" variant="danger-subtle" onClick={() => closeRoom(r.code)}>
                                        <X size={14} />
                                    </IconButton>
                                </Container>
                                <Text dim content={`${r.listeners ?? "?"} listeners · ${r.playing ? "playing" : "paused"}`} />
                                <Seperator />
                            </Container>
                        ))
                    )}
                    <Container horizontal centered_y class="section-head">
                        <TextIconButton variant="accent" disabled={scanning} onClick={scan}>
                            <ScanLine size={18} /> {scanning ? "Scanning…" : "Scan library"}
                        </TextIconButton>
                        <IconButton title="Refresh" onClick={load}><RefreshCw size={16} /></IconButton>
                    </Container>
                    {message && <Text content={message} />}
                </Container>
            )}
        </Loading>
    )
}

/** Download requests with approve/reject/cancel/retry and the live log. */
function Requests() {
    const [rows, setRows] = useState<any[] | null>(null);
    const [log, setLog] = useState<{ id: number; text: string } | null>(null);
    const [error, setError] = useState<string | null>(null);

    function load() {
        API.adminRequests()
            .then(d => { setRows(d.requests ?? []); setError(null); })
            .catch(e => { setRows(r => r ?? []); setError(String(e)); });
    }
    useEffect(load, []);

    async function act(fn: () => Promise<unknown>) {
        setError(null);
        try { await fn(); load(); }
        catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    }

    return (
        <Container extra_gap>
            <Container horizontal centered_y class="section-head">
                <Header3>Requests</Header3>
                <IconButton title="Refresh requests" onClick={load}><RefreshCw size={15} /></IconButton>
            </Container>
            {error && <Text class="error" content={error} />}
            <Loading loaded={rows != null}>
                {() => rows!.length == 0
                    ? <Text dim content="No requests." />
                    : rows!.map(r => (
                        <Container class="req">
                            <Container horizontal centered_y wrap class="req-head">
                                <Text
                                    class="req-url"
                                    content={`#${r.id} · ${r.status}${r.running ? " (running)" : ""} · ${r.username ?? "?"} · ${r.url}`}
                                />
                                {(r.status == "pending" || r.status == "failed") && (
                                    <>
                                        <IconButton title="Approve" onClick={() => act(() => API.adminReqAction(r.id, "approve"))}><Check size={15} /></IconButton>
                                        <IconButton title="Reject" onClick={() => act(() => API.adminReqAction(r.id, "reject"))}><Ban size={15} /></IconButton>
                                    </>
                                )}
                                {(r.status == "approved" || r.status == "running") && (
                                    <IconButton title="Cancel" onClick={() => act(() => API.adminReqCancel(r.id))}><Ban size={15} /></IconButton>
                                )}
                                <IconButton title="Retry" onClick={() => act(() => API.adminReqRetry(r.id))}><RotateCcw size={15} /></IconButton>
                                <IconButton
                                    title="Show log"
                                    onClick={() => API.adminRequestLog(r.id)
                                        .then(d => setLog({ id: r.id, text: d.log || "(empty)" }))
                                        .catch(e => setError(e instanceof Error ? e.message : String(e)))}
                                >
                                    <FileText size={15} />
                                </IconButton>
                                <IconButton
                                    title="Delete"
                                    variant="danger-subtle"
                                    onClick={() => {
                                        if (window.confirm(`Delete request #${r.id}?`)) {
                                            act(() => API.adminReqDelete(r.id));
                                        }
                                    }}
                                >
                                    <Trash2 size={15} />
                                </IconButton>
                            </Container>
                            <Text dim content={`${when(r.created)}${r.elapsed ? ` · ${Math.round(r.elapsed)}s elapsed` : ""}${r.finished && r.status !== "running" ? ` · finished ${when(r.finished)}` : ""}`} />
                            <Seperator />
                        </Container>
                    ))}
            </Loading>
            {log != null && (
                <Container class="req-log-wrap">
                    <Container horizontal centered_y class="section-head">
                        <Header3>Log (request #{log.id})</Header3>
                        <IconButton title="Close log" onClick={() => setLog(null)}><X size={14} /></IconButton>
                    </Container>
                    {/* A log needs literal whitespace; no flufi-ui component renders that. */}
                    <pre class="log">{log.text}</pre>
                </Container>
            )}
        </Container>
    )
}

/** Accounts, with promote/demote and delete. */
function Users() {
    const [rows, setRows] = useState<any[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    function load() {
        API.adminUsers()
            .then(d => { setRows(d.users ?? []); setError(null); })
            .catch(e => { setRows(r => r ?? []); setError(String(e)); });
    }
    useEffect(load, []);

    async function act(fn: () => Promise<unknown>) {
        setError(null);
        try { await fn(); load(); }
        catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    }

    return (
        <Container extra_gap>
            <Container horizontal centered_y class="section-head">
                <Header3>Users</Header3>
                <IconButton title="Refresh users" onClick={load}><RefreshCw size={15} /></IconButton>
            </Container>
            {error && <Text class="error" content={error} />}
            <Loading loaded={rows != null}>
                {() => rows!.map(u => (
                    <Container class="user">
                        <Container horizontal centered_y wrap class="req-head">
                            <Text class="req-url" content={`${u.username}${u.is_admin ? " (admin)" : ""}`} />
                            <TextIconButton onClick={() => act(() => API.adminSetAdmin(u.id, !u.is_admin))}>
                                {u.is_admin ? "Demote" : "Promote"}
                            </TextIconButton>
                            <IconButton
                                title="Delete user"
                                variant="danger-subtle"
                                onClick={() => {
                                    if (window.confirm(`Delete ${u.username}? This cannot be undone.`)) {
                                        act(() => API.adminDeleteUser(u.id));
                                    }
                                }}
                            >
                                <Trash2 size={15} />
                            </IconButton>
                        </Container>
                        <Text dim content={u.email ?? "no email"} />
                        <Text dim content={`${u.plays} plays · ${u.likes} likes · ${u.playlists} playlists · ${u.requests ?? 0} requests`} />
                        <Seperator />
                    </Container>
                ))}
            </Loading>
        </Container>
    )
}

/** Invite-code creation and revocation. */
function Invites() {
    const [rows, setRows] = useState<any[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [created, setCreated] = useState<string | null>(null);
    const uses = useSignal("1");
    const hours = useSignal("");
    const note = useSignal("");

    function load() {
        API.adminInviteCodes()
            .then(d => { setRows(d.codes ?? []); setError(null); })
            .catch(e => { setRows(r => r ?? []); setError(String(e)); });
    }
    useEffect(load, []);

    async function create() {
        setError(null);
        setCreated(null);
        try {
            const r = await API.adminCreateInvite({
                uses: Number(uses.peek() || 1),
                hours: Number(hours.peek() || 0),
                note: note.peek(),
            });
            setCreated(r.code);
            load();
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    return (
        <Container extra_gap>
            <Container horizontal centered_y class="section-head">
                <Header3>Invite codes</Header3>
                <IconButton title="Refresh invite codes" onClick={load}><RefreshCw size={15} /></IconButton>
            </Container>
            <Container horizontal wrap>
                <FormalInput label="Uses"><Input value={uses} /></FormalInput>
                <FormalInput label="Expires in hours (0 = never)"><Input value={hours} /></FormalInput>
                <FormalInput label="Note"><Input value={note} /></FormalInput>
                <TextIconButton variant="accent" onClick={create}>Create code</TextIconButton>
            </Container>
            {created && <Text selectable content={`New code: ${created}`} />}
            {error && <Text class="error" content={error} />}
            <Loading loaded={rows != null}>
                {() => rows!.length == 0
                    ? <Text dim content="No invite codes." />
                    : rows!.map(c => (
                        <Container>
                            <Container horizontal centered_y>
                                <Text selectable content={c.code} />
                                {c.active
                                    ? (
                                        <TextIconButton
                                            onClick={() => {
                                                if (window.confirm(`Revoke invite ${c.code}?`)) {
                                                    API.adminRevokeInvite(c.id)
                                                        .then(load)
                                                        .catch(e => setError(e instanceof Error ? e.message : String(e)));
                                                }
                                            }}
                                        >
                                            Revoke
                                        </TextIconButton>
                                    )
                                    : <Text dim content="revoked" />}
                            </Container>
                            <Text dim content={`${c.uses}/${c.max_uses} used${c.expired ? " · expired" : ""}${c.note ? " · " + c.note : ""}`} />
                            <Text dim content={`created ${when(c.created)}`} />
                            <Seperator />
                        </Container>
                    ))}
            </Loading>
        </Container>
    )
}

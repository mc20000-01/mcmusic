import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import {
    Container, Content, FormalInput, Header2, Header3, IconButton, Input, Loading,
    Seperator, Table, TableBody, TableCell, TableRow, Tabs, Text, TextIconButton
} from "flufi-ui/components";
import {
    Ban, Check, FileText, MonitorSmartphone, Radio, RefreshCw, RotateCcw,
    ScanLine, Sparkles, Trash2, X,
} from "lucide-preact";
import { API } from "../../common/net/api";

import "./style.css";

// Admin endpoint groups, one pane each. Tabs is flufi-ui's own control,
// so the admin view looks like the rest of the client.
type Tab = "overview" | "metrics" | "requests" | "users" | "invites" | "devices" | "channels" | "enrich";

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
                        { name: "Metrics", value: "metrics" },
                        { name: "Requests", value: "requests" },
                        { name: "Users", value: "users" },
                        { name: "Invites", value: "invites" },
                        { name: "Devices", value: "devices" },
                        { name: "Channels", value: "channels" },
                        { name: "Enrich", value: "enrich" },
                    ]}
                    onChange={(v) => setTab(v as Tab)}
                />
                {tab == "overview" && <Overview />}
                {tab == "metrics" && <Metrics />}
                {tab == "requests" && <Requests />}
                {tab == "users" && <Users />}
                {tab == "invites" && <Invites />}
                {tab == "devices" && <AdminDevices />}
                {tab == "channels" && <Channels />}
                {tab == "enrich" && <EnrichLyrics />}
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

/** Admin-only listening insight: always-on events, never a public feed. */
function Metrics() {
    const [data, setData] = useState<any>(null);
    const [history, setHistory] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const load = () => {
        API.adminMetrics()
            .then(d => { setData(d); setError(null); })
            .catch(e => setError(e instanceof Error ? e.message : String(e)));
    };
    useEffect(load, []);

    async function openHistory(id: number) {
        try { setHistory(await API.adminHistory(id)); }
        catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    }

    return (
        <Container extra_gap>
            <Container horizontal centered_y class="section-head">
                <Header3>Listening metrics</Header3>
                <IconButton title="Refresh metrics" onClick={load}><RefreshCw size={15} /></IconButton>
            </Container>
            <Text dim content="Always-on, admin-only. Skips, completions and seeks rank Faves; nothing here is public." />
            {error && <Text class="error" content={error} />}
            {!data ? <Text dim content="Loading metrics…" /> : (
                <>
                    <Table>
                        <TableBody>
                            {[
                                ["Events", data.events],
                                ["Completion rate", `${Math.round((data.completion_rate ?? 0) * 100)}%`],
                                ...Object.entries(data.by_event ?? {}).map(([k, v]) => [k, v]),
                            ].map(([label, value]) => (
                                <TableRow>
                                    <TableCell><Text dim content={String(label)} /></TableCell>
                                    <TableCell><Text content={String(value)} /></TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    <Header3>Top tracks</Header3>
                    <Table>
                        <TableBody>
                            {(data.top_tracks ?? []).map((t: any) => (
                                <TableRow key={t.track_id}>
                                    <TableCell><Text content={t.title} /></TableCell>
                                    <TableCell><Text dim content={t.artist} /></TableCell>
                                    <TableCell><Text dim content={`${t.plays} plays · ${t.completions} done · ${t.skips} skips`} /></TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    <Header3>Listeners</Header3>
                    <Table>
                        <TableBody>
                            {(data.listeners ?? []).map((u: any) => (
                                <TableRow key={u.user_id}>
                                    <TableCell><Text content={u.username} /></TableCell>
                                    <TableCell><Text dim content={`${u.events} events · ${when(u.last_seen)}`} /></TableCell>
                                    <TableCell>
                                        <TextIconButton title="View recent history" onClick={() => void openHistory(u.user_id)}>
                                            <FileText size={14} /> History
                                        </TextIconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                    {history && (
                        <>
                            <Header3>{history.user?.username ?? "History"}</Header3>
                            <Table>
                                <TableBody>
                                    {(history.events ?? []).map((e: any, i: number) => (
                                        <TableRow key={`${e.ts}-${i}`}>
                                            <TableCell><Text dim content={when(e.ts)} /></TableCell>
                                            <TableCell><Text content={e.event} /></TableCell>
                                            <TableCell><Text dim content={`${e.title ?? e.track_id} · ${e.client ?? "?"}`} /></TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </>
                    )}
                </>
            )}
        </Container>
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

/** All devices across accounts, with their last known playback. */
function AdminDevices() {
    const [rows, setRows] = useState<any[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    function load() {
        API.adminDevices()
            .then(d => { setRows(d.devices ?? []); setError(null); })
            .catch(e => { setRows(r => r ?? []); setError(String(e)); });
    }
    useEffect(load, []);

    return (
        <Container extra_gap>
            <Container horizontal centered_y class="section-head">
                <Header3>All devices</Header3>
                <IconButton title="Refresh devices" onClick={load}><RefreshCw size={15} /></IconButton>
            </Container>
            {error && <Text class="error" content={error} />}
            <Loading loaded={rows != null}>
                {() => rows!.length === 0
                    ? <Text dim content="No devices have signed in." />
                    : rows!.map(d => (
                        <Container class="user" key={d.id}>
                            <Container horizontal centered_y wrap class="req-head">
                                <MonitorSmartphone size={15} />
                                <Text content={d.name || d.device_hash || `Device ${d.id}`} />
                                <Text dim content={d.username} />
                                {d.is_active ? <Text content="active" /> : <Text dim content="inactive" />}
                            </Container>
                            <Text dim content={`${d.ip || "?"} · last seen ${when(d.last_seen)}`} />
                            {d.current_track_id && (
                                <Text dim content={`Playing track #${d.current_track_id} at ${Math.round(d.current_position || 0)}s${d.current_paused ? " (paused)" : ""}`} />
                            )}
                            <Seperator />
                        </Container>
                    ))}
            </Loading>
        </Container>
    )
}

/** Bot control channels: list, bind and unbind. */
function Channels() {
    const [rows, setRows] = useState<any[]>([]);
    const [configured, setConfigured] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const platform = useSignal("discord");
    const channelId = useSignal("");
    const guildId = useSignal("");
    const mode = useSignal("control");

    function load() {
        API.channels(true)
            .then(d => { setRows(d.channels ?? []); setConfigured(!!d.configured); setError(null); })
            .catch(e => { setRows([]); setError(String(e)); });
    }
    useEffect(load, []);

    async function bind() {
        setError(null);
        try {
            await API.bindChannel({
                platform: platform.peek(),
                channel_id: channelId.peek().trim(),
                guild_id: guildId.peek().trim(),
                mode: mode.peek(),
            });
            channelId.value = "";
            load();
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function unbind(id: number) {
        if (!window.confirm("Unbind this channel?")) return;
        try { await API.unbindChannel(id); load(); }
        catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    }

    return (
        <Container extra_gap>
            <Container horizontal centered_y class="section-head">
                <Header3>Music control channels</Header3>
                <IconButton title="Refresh channels" onClick={load}><RefreshCw size={15} /></IconButton>
            </Container>
            <Text dim content={configured
                ? "The bot is configured. Run /setmusicchannel in Discord or bind a channel below."
                : "The bot token is not configured on this server."} />
            {error && <Text class="error" content={error} />}
            <Container horizontal wrap class="channel-form">
                <FormalInput label="Platform">
                    <Input value={platform} />
                </FormalInput>
                <FormalInput label="Channel ID">
                    <Input value={channelId} placeholder="1234567890" />
                </FormalInput>
                <FormalInput label="Guild ID (optional)">
                    <Input value={guildId} />
                </FormalInput>
                <FormalInput label="Mode">
                    <Input value={mode} />
                </FormalInput>
                <TextIconButton variant="accent" disabled={!channelId.value.trim()} onClick={bind}>
                    <Radio size={15} /> Bind
                </TextIconButton>
            </Container>
            {rows.length === 0
                ? <Text dim content="No channels bound." />
                : rows.map(ch => (
                    <Container class="user" key={ch.id}>
                        <Container horizontal centered_y wrap class="req-head">
                            <Text content={`${ch.platform} · ${ch.channel_id}`} />
                            <Text dim content={ch.mode} />
                            <TextIconButton variant="danger-subtle" onClick={() => unbind(ch.id)}>
                                <X size={14} /> Unbind
                            </TextIconButton>
                        </Container>
                        {ch.state && (
                            <Text dim content={JSON.stringify(ch.state).slice(0, 240)} />
                        )}
                        <Seperator />
                    </Container>
                ))}
        </Container>
    )
}

/** Metadata enrichment and lyrics backfill progress. */
function EnrichLyrics() {
    const [enrich, setEnrich] = useState<any>(null);
    const [lyrics, setLyrics] = useState<any>(null);
    const [message, setMessage] = useState<string | null>(null);

    function load() {
        API.adminEnrich().then(setEnrich).catch(e => setMessage(String(e)));
        API.adminLyrics().then(setLyrics).catch(() => setLyrics(null));
    }
    useEffect(load, []);

    async function start(mode: "enrich" | "enrich-force" | "lyrics") {
        setMessage(`Starting ${mode}…`);
        try {
            if (mode === "lyrics") {
                const r = await API.startLyrics();
                setMessage(r.started ? "Lyrics backfill started." : "Lyrics job is already running.");
            } else {
                await API.startEnrich(mode === "enrich-force");
                setMessage("Metadata enrichment queued.");
            }
            load();
        } catch (e) {
            setMessage(e instanceof Error ? e.message : String(e));
        }
    }

    return (
        <Container extra_gap>
            <Container horizontal centered_y class="section-head">
                <Header3>Metadata &amp; lyrics</Header3>
                <IconButton title="Refresh status" onClick={load}><RefreshCw size={15} /></IconButton>
            </Container>
            {message && <Text content={message} />}
            <Container>
                <Header3>YouTube enrichment</Header3>
                {enrich ? (
                    <Text dim content={`${enrich.linked ?? 0}/${enrich.total ?? 0} linked · ${enrich.fetched ?? 0} fetched · ${enrich.pending ?? 0} pending`} />
                ) : <Text dim content="Status unavailable." />}
                <Container horizontal centered_y class="section-buttons">
                    <TextIconButton variant="panel" onClick={() => start("enrich")}>
                        <Sparkles size={15} /> Enrich pending
                    </TextIconButton>
                    <TextIconButton variant="panel" onClick={() => start("enrich-force")}>
                        <RotateCcw size={15} /> Re-check all
                    </TextIconButton>
                </Container>
            </Container>
            <Seperator />
            <Container>
                <Header3>Lyrics</Header3>
                {lyrics ? (
                    <Text dim content={JSON.stringify(lyrics).slice(0, 300)} />
                ) : <Text dim content="Lyrics status unavailable." />}
                <TextIconButton variant="panel" onClick={() => start("lyrics")}>
                    <FileText size={15} /> Fetch missing lyrics
                </TextIconButton>
            </Container>
        </Container>
    )
}

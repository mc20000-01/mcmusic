/** Public listening: a directory of what people are playing, and the
 *  per-user profile page the directory cards link to.
 */
import { useEffect, useState } from "preact/hooks";
import type { RoutePropsForPath } from "preact-iso";
import {
    Container, Content, Header2, Header3, LinkButton, Loading, Text,
} from "flufi-ui/components";
import { Headphones, UserRound } from "lucide-preact";
import { API, fallbackCover } from "../../common/net/api";
import type { PublicListening, PublicNow } from "../../common/net/types";
import { CoverArt } from "../../components/Library/CoverArt";
import { UserPfp } from "../../components/User/Pfp";

import "./style.css";

function fmtPosition(seconds: number, duration?: number): string {
    const s = Math.max(0, Math.floor(seconds || 0));
    const m = Math.floor(s / 60);
    const tail = `${String(s % 60).padStart(2, "0")}`;
    return duration ? `${m}:${tail} / ${fmt(duration)}` : `${m}:${tail}`;
}
function fmt(seconds: number): string {
    const s = Math.max(0, Math.floor(seconds || 0));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function ListenersPage() {
    const [data, setData] = useState<PublicListening | null>(null);
    const [error, setError] = useState<string | null>(null);

    function load() {
        API.publicListening()
            .then(d => { setData(d); setError(null); })
            .catch(e => { setError(String(e)); setData({ ok: false, users: [], base_url: "", now: 0 }); });
    }
    useEffect(load, []);

    return (
        <Content class="profile-page">
            <Container extra_gap>
                <Container horizontal centered_y class="profile-head">
                    <Headphones size={20} />
                    <Header2>Listening now</Header2>
                </Container>
                <Text dim content="Public listening rooms from this server. Profiles show the current track in real time." />
                {error && <Text class="error" content={error} />}
                <Loading loaded={data != null}>
                    {() => {
                        const users = data?.users ?? [];
                        if (users.length === 0) {
                            return <Text dim content="Nobody is listening publicly right now." />;
                        }
                        const listening = users.filter(u => u.listening);
                        const idle = users.filter(u => !u.listening);
                        return (
                            <Container extra_gap>
                                {listening.length > 0 && (
                                    <Container>
                                        <Header3>Now playing</Header3>
                                        <Container class="listener-grid">
                                            {listening.map(u => <ListenerCard key={u.username} user={u} />)}
                                        </Container>
                                    </Container>
                                )}
                                {idle.length > 0 && (
                                    <Container>
                                        <Header3>Recently here</Header3>
                                        <Container horizontal wrap class="listener-chips">
                                            {idle.map(u => (
                                                <LinkButton key={u.username} href={`/u/${encodeURIComponent(u.username)}`} variant="panel">
                                                    <UserRound size={14} /> {u.username}
                                                </LinkButton>
                                            ))}
                                        </Container>
                                    </Container>
                                )}
                            </Container>
                        );
                    }}
                </Loading>
            </Container>
        </Content>
    );
}

function ListenerCard(props: { user: PublicListening["users"][number] }) {
    const u = props.user;
    return (
        <LinkButton
            variant="always-transparent"
            noPadding
            class="listener-card"
            href={`/u/${encodeURIComponent(u.username)}`}
        >
            <CoverArt
                src={u.cover_url || fallbackCover(u.username, "artist")}
                name={u.username}
                kind="artist"
                size={120}
            />
            <Text content={u.username} />
            <Text dim content={u.track ? `${u.track.title} — ${u.track.artist || "?"}` : "Idle"} />
            {u.track && (
                <Text dim class="listener-position" content={fmtPosition(u.position, u.track.duration)} />
            )}
        </LinkButton>
    );
}

export function ProfilePage(props: RoutePropsForPath<"/u/:username">) {
    const [data, setData] = useState<PublicNow | null>(null);
    const [error, setError] = useState<string | null>(null);
    const username = decodeURIComponent(props.username || "");

    useEffect(() => {
        let cancelled = false;
        setData(null);
        API.publicNow(username)
            .then(d => { if (!cancelled) { setData(d); setError(null); } })
            .catch(e => { if (!cancelled) setError(String(e)); });
        return () => { cancelled = true; };
    }, [username]);

    return (
        <Content class="profile-page">
            <Container extra_gap>
                <Container horizontal centered_y class="profile-head">
                    <UserPfp username={username} size={64} />
                    <Container vertical>
                        <Header2>{username}</Header2>
                        <Text dim content="Public listening profile" />
                    </Container>
                </Container>
                {error && <Text class="error" content={error} />}
                <Loading loaded={data != null || error != null}>
                    {() => data ? (
                        data.listening && data.track ? (
                            <Container horizontal wrap class="profile-now">
                                <CoverArt
                                    src={API.getTrackCoverUrl(String((data.track as any).id ?? (data.track as any).uuid ?? ""))}
                                    name={String((data.track as any).title ?? username)}
                                    kind="track"
                                    size={140}
                                />
                                <Container vertical>
                                    <Header3>Listening now</Header3>
                                    <Text content={String((data.track as any).title ?? "")} />
                                    <Text dim content={String((data.track as any).artist ?? "")} />
                                    <Text dim content={fmtPosition(data.position, Number((data.track as any).duration) || 0)} />
                                    <LinkButton href="/listeners">See everyone listening</LinkButton>
                                </Container>
                            </Container>
                        ) : (
                            <Text dim content={`${username} isn't listening right now.`} />
                        )
                    ) : null}
                </Loading>
            </Container>
        </Content>
    );
}

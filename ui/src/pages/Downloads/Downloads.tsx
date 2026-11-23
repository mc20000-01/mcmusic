/** Offline downloads: audio kept in the service worker's media cache with an
 *  IndexedDB index. Tracks stay playable when the server is unreachable.
 */
import { Button, Container, Content, Header2, Text, TextIconButton } from "flufi-ui/components";
import { Download, Play, Trash2, WifiOff } from "lucide-preact";
import {
    clearDownloads, downloadBusy, downloadStats, downloads, isCached, removeDownload,
} from "../../common/downloads";
import { playTrack } from "../../common/player";
import { pendingWrites } from "../../common/net/api";
import { useEffect, useState } from "preact/hooks";

import "./style.css";

function humanBytes(n: number): string {
    if (!n) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    let v = n, i = 0;
    while (v >= 1024 && i < units.length - 1) { v /= 1024; i += 1; }
    return `${v.toFixed(i ? 1 : 0)} ${units[i]}`;
}

export function DownloadsPage() {
    const [, force] = useState(0);
    const [pending, setPending] = useState(0);

    useEffect(() => {
        let cancelled = false;
        // isCached() is async; refresh once so the list reflects real cache hits.
        Promise.all(downloads.value.map(d => isCached(d.id))).then(() => {
            if (!cancelled) force(n => n + 1);
        });
        void pendingWrites().then(n => { if (!cancelled) setPending(n); });
        return () => { cancelled = true; };
    }, []);

    const stats = downloadStats();

    return (
        <Content class="downloads-page">
            <Container extra_gap>
                <Container horizontal centered_y class="downloads-head">
                    <Download size={20} />
                    <Header2>Downloads</Header2>
                    {downloads.value.length > 0 && (
                        <TextIconButton variant="danger-subtle" onClick={() => void clearDownloads()}>
                            <Trash2 size={15} /> Clear all
                        </TextIconButton>
                    )}
                </Container>
                <Text dim content={`${stats.count} track${stats.count === 1 ? "" : "s"} · ${humanBytes(stats.bytes)} stored on this device.`} />
                {pending > 0 && (
                    <Text class="downloads-pending" content={`${pending} offline change${pending === 1 ? "" : "s"} waiting to sync.`} />
                )}
                {downloads.value.length === 0 ? (
                    <Text dim content="Open a track's menu and choose Download to make it available offline." />
                ) : (
                    <Container vertical class="download-list">
                        {downloads.value.map(d => (
                            <Container horizontal centered_y class="download-row" key={d.id}>
                                <Button
                                    variant="always-transparent"
                                    title={`Play ${d.title}`}
                                    onClick={() => playTrack(d.id, { title: d.title, artist: d.artist })}
                                >
                                    <Play size={16} />
                                </Button>
                                <Container vertical class="download-meta">
                                    <Text content={d.title} />
                                    <Text dim content={`${d.artist} · ${humanBytes(d.bytes)}`} />
                                </Container>
                                {downloadBusy.value === d.id && <Text dim content="Working…" />}
                                <TextIconButton
                                    variant="danger-subtle"
                                    title="Remove download"
                                    onClick={() => void removeDownload(d.id)}
                                >
                                    <Trash2 size={15} />
                                </TextIconButton>
                            </Container>
                        ))}
                    </Container>
                )}
                <Container horizontal centered_y class="downloads-note">
                    <WifiOff size={15} />
                    <Text dim content="Likes and playlist edits made offline are replayed when you reconnect." />
                </Container>
            </Container>
        </Content>
    );
}

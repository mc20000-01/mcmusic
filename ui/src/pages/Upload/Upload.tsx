import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { Container, Content, FormalInput, Header2, Input, Loading, Text, TextIconButton } from "flufi-ui/components";
import { CloudUpload } from "lucide-preact";
import { API, refreshLibrary } from "../../common/net/api";

import "./style.css";

type Request = { id: number; url: string; status: string };

const DIRECT_EXTS = [".mp3", ".m4a", ".aac", ".opus", ".flac", ".wav", ".webm", ".ogg", ".zip"];

/** YouTube links plus direct HTTPS audio/ZIP links, matching the server. */
function isMusicLink(value: string): boolean {
    try {
        const url = new URL(value);
        if (url.protocol !== "https:" || !url.hostname || url.username || url.password) {
            return false;
        }
        if (/(^|\.)youtube\.com$/.test(url.hostname) || /(^|\.)youtu\.be$/.test(url.hostname)) {
            return true;
        }
        const path = decodeURIComponent(url.pathname).toLowerCase();
        return DIRECT_EXTS.some(ext => path.endsWith(ext));
    } catch {
        return false;
    }
}

function statusLabel(status: string): string {
    switch (status) {
        case "pending": return "Waiting for approval";
        case "running": return "Downloading…";
        case "done": return "Finished";
        case "failed": return "Failed";
        case "rejected": return "Rejected";
        case "approved": return "Approved";
        default: return status;
    }
}

/**
 * "Add music": submit a YouTube or direct audio/ZIP link. Admins get it
 * started immediately, everyone else queues it for approval.
 */
export function UploadPage() {
    const url = useSignal("");
    const [error, setError] = useState<string | null>(null);
    const [sent, setSent] = useState<string | null>(null);
    const [sending, setSending] = useState(false);
    const [requests, setRequests] = useState<Request[] | null>(null);

    function loadRequests() {
        API.requests()
            .then(d => setRequests(d.requests ?? []))
            .catch(() => setRequests(r => r ?? []));
    }

    useEffect(() => { loadRequests(); }, []);

    // Pending downloads change status on the server; poll while any are still
    // in flight so the list does not sit at "queued" forever.
    useEffect(() => {
        if (!requests?.some(r => r.status == "pending" || r.status == "queued" || r.status == "running")) {
            return;
        }
        const timer = setInterval(loadRequests, 15000);
        return () => clearInterval(timer);
    }, [requests]);

    async function submit() {
        const link = url.peek().trim();
        setError(null);
        setSent(null);
        if (link == "") return;
        if (!isMusicLink(link)) {
            setError("Please paste an https YouTube link or a direct https .mp3, audio or .zip link.");
            return;
        }

        setSending(true);
        try {
            const res = await API.requestDownload(link);
            setSent(res.status == "running"
                ? "Got it — downloading now. Check Requests below for progress."
                : "Request sent. An admin will review it, then it’ll download automatically.");
            url.value = "";
            refreshLibrary();
            loadRequests();
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setSending(false);
        }
    }

    return (
        <Content class="upload" wrapped>
            <Container extra_gap>
                <Header2>Add music</Header2>
                <Text dim content="Paste a YouTube link (video or playlist), or a direct https link to an MP3/audio file or a ZIP of tracks. If you’re an admin it starts right away; otherwise an admin will approve it first." />
                <FormalInput label="YouTube, MP3 or ZIP link">
                    <Input
                        value={url}
                        placeholder="https://…/album.zip"
                        onEnter={submit}
                    />
                </FormalInput>
                {error && <span class="error status-line" role="status">{error}</span>}
                {sent && <Text content={sent} />}
                <TextIconButton
                    variant="accent"
                    disabled={sending || url.value.trim() == ""}
                    onClick={submit}
                >
                    <CloudUpload size={20} /> {sending ? "Sending…" : "Request download"}
                </TextIconButton>

                <Header2>Your requests</Header2>
                <Loading loaded={requests != null}>
                    {() => (
                        <Container class="upload-requests">
                            {requests!.length == 0 && <Text dim content="Nothing here yet — paste a link above to add music." />}
                            {requests!.map(r => (
                                <Container horizontal centered_y wrap class="upload-request">
                                    <Text class="req-url" content={`#${r.id} · ${r.url}`} />
                                    <Text dim class="req-status" content={statusLabel(r.status)} />
                                </Container>
                            ))}
                        </Container>
                    )}
                </Loading>
            </Container>
        </Content>
    )
}

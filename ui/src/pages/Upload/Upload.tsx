import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { Container, Content, FormalInput, Header2, Input, Loading, Text, TextIconButton } from "flufi-ui/components";
import { CloudUpload } from "lucide-preact";
import { API, refreshLibrary } from "../../common/net/api";

import "./style.css";

type Request = { id: number; url: string; status: string };

/** Accepts youtube.com, music.youtube.com and youtu.be links only. */
function isYouTubeLink(value: string): boolean {
    try {
        const { hostname } = new URL(value);
        return /(^|\.)youtube\.com$/.test(hostname) || /(^|\.)youtu\.be$/.test(hostname);
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
 * "Add music": submit a YouTube link as a download request. Admins get it
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
        if (!isYouTubeLink(link)) {
            setError("Please paste a YouTube or YouTube Music link (like https://youtube.com/watch?v=...).");
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
                <Text dim content="Paste a YouTube or YouTube Music link (video or playlist). If you’re an admin it starts right away; otherwise an admin will approve it first." />
                <FormalInput label="YouTube link">
                    <Input
                        value={url}
                        placeholder="https://www.youtube.com/watch?v=…"
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

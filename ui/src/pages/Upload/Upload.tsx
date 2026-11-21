import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { Container, Content, FormalInput, Header2, Input, Loading, Text, TextIconButton } from "flufi-ui/components";
import { CloudUpload } from "lucide-preact";
import { API, refreshLibrary } from "../../common/net/api";

type Request = { id: number; url: string; status: string };

/**
 * "Add music": submit a YouTube link as a download request. Admins get it
 * started immediately, everyone else queues it for approval.
 */
export function UploadPage() {
    const url = useSignal("");
    const [error, setError] = useState<string | null>(null);
    const [sent, setSent] = useState<string | null>(null);
    const [requests, setRequests] = useState<Request[] | null>(null);

    function loadRequests() {
        API.requests()
            .then(d => setRequests(d.requests ?? []))
            .catch(() => setRequests([]));
    }

    useEffect(() => { loadRequests(); }, []);

    async function submit() {
        setError(null);
        setSent(null);
        try {
            const res = await API.requestDownload(url.peek().trim());
            setSent(res.status == "running"
                ? "Request accepted — downloading now."
                : "Request sent. An admin will start the download.");
            url.value = "";
            refreshLibrary();
            loadRequests();
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    return (
        <Content class="upload" wrapped>
            <Container extra_gap>
                <Header2>Add music</Header2>
                <Text dim content="Paste a YouTube / YouTube Music video or playlist link. Admins download it right away; everyone else's request waits for approval." />
                <FormalInput label="YouTube link">
                    <Input value={url} onEnter={submit} />
                </FormalInput>
                {error && <Text class="error" content={error} />}
                {sent && <Text content={sent} />}
                <TextIconButton variant="accent" disabled={url.value.trim() == ""} onClick={submit}>
                    <CloudUpload size={20} /> Request download
                </TextIconButton>

                <Header2>Requests</Header2>
                <Loading loaded={requests != null}>
                    {() => (
                        <Container>
                            {requests!.length == 0 && <Text dim content="No requests yet." />}
                            {requests!.map(r => (
                                <Text key={r.id} content={`#${r.id} · ${r.status} · ${r.url}`} />
                            ))}
                        </Container>
                    )}
                </Loading>
            </Container>
        </Content>
    )
}

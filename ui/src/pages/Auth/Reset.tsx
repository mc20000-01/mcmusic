import { useEffect, useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { useLocation } from "preact-iso";
import { Button, Container, Content, FormalInput, Input, Text } from "flufi-ui/components";

import "./style.css";
import { API } from "../../common/net/api";
import { PasswordInput } from "../../components/PasswordInput/PasswordInput";

/** Password reset: request a link, then spend the token from the email. */
export function ResetPage() {
    const loc = useLocation();
    const token = String(loc.query.token ?? "");
    const email = useSignal("");
    const password = useSignal("");
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const [valid, setValid] = useState<boolean | null>(token ? null : true);

    useEffect(() => {
        if (!token) return;
        setValid(null);
        API.checkReset(token)
            .then(() => setValid(true))
            .catch(e => {
                setValid(false);
                setError(e instanceof Error ? e.message : String(e));
            });
    }, [token]);

    async function submit() {
        setError(null);
        setNotice(null);
        setBusy(true);
        try {
            if (token) {
                await API.confirmReset(token, password.peek());
                setNotice("Password updated. Sign in with your new password.");
                setTimeout(() => loc.route("/auth"), 1500);
            } else {
                const res = await API.requestReset(email.peek());
                setNotice(res.mail
                    ? "If that address has an account, a reset link is on its way."
                    : "Reset mail is not configured on this server.");
            }
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setBusy(false);
        }
    }

    return (
        <Content class="auth" centered>
            <Container class="auth-box">
                <Text class="auth-word" content="mcmusic" />
                <Text dim content={token ? "Choose a new password." : "Reset your password."} />

                {token ? (
                    <>
                        {valid === null && <Text dim content="Checking your reset link…" />}
                        {valid === false && (
                            <>
                                <Text class="error" content={error ?? "This reset link is invalid or has expired."} />
                                <Button variant="always-transparent" onClick={() => loc.route("/forgot")}>
                                    <Text dim content="Ask for a new link" />
                                </Button>
                            </>
                        )}
                        {valid === true && (
                            <>
                                <FormalInput label="New password">
                                    <PasswordInput value={password} placeholder="at least 6 characters" />
                                </FormalInput>
                                {error && <Text class="error" content={error} />}
                                {notice && <Text dim content={notice} />}
                                <Button
                                    variant="accent"
                                    centered
                                    extraPadding
                                    disabled={busy || password.value.length < 6}
                                    onClick={submit}
                                >
                                    {busy ? "..." : "Set new password"}
                                </Button>
                            </>
                        )}
                    </>
                ) : (
                    <>
                        <Text dim content="Enter the email address on your account." />
                        <FormalInput label="Email">
                            <Input value={email} />
                        </FormalInput>
                        {error && <Text class="error" content={error} />}
                        {notice && <Text dim content={notice} />}
                        <Button
                            variant="accent"
                            centered
                            extraPadding
                            disabled={busy || email.value.trim() == ""}
                            onClick={submit}
                        >
                            {busy ? "..." : "Send reset link"}
                        </Button>
                    </>
                )}

                <Button variant="always-transparent" onClick={() => loc.route("/auth")}>
                    <Text dim content="Back to sign in" />
                </Button>
            </Container>
        </Content>
    )
}

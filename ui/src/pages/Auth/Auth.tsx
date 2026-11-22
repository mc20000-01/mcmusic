import { useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { useLocation } from "preact-iso";
import { Button, Container, Content, FormalInput, Input, Text, TextIconLinkButton } from "flufi-ui/components";
import { Link2 } from "lucide-preact";

import "./style.css";
import { login, register } from "../../common/auth";
import { PasswordInput } from "../../components/PasswordInput/PasswordInput";

/**
 * Local sign-in / registration. Authentication is a cookie session on the
 * Flask server, so there is nothing to persist client-side afterwards.
 *
 * Deliberately plain: one column, no card, no accent colour.
 */
export function AuthPage() {
    const loc = useLocation();
    const [mode, setMode] = useState<"login" | "register">("login");
    const username = useSignal("");
    const password = useSignal("");
    const invite = useSignal("");
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);

    async function submit() {
        setError(null);
        setBusy(true);
        try {
            if (mode == "login") {
                await login(username.peek(), password.peek());
            } else {
                await register({
                    username: username.peek(),
                    password: password.peek(),
                    invite: invite.peek().trim() || undefined,
                });
            }
            loc.route("/");
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
                <Text dim content={mode == "login" ? "Sign in." : "Create an account."} />

                <FormalInput label="Email or username">
                    <Input value={username} />
                </FormalInput>

                <FormalInput label="Password">
                    <PasswordInput value={password} />
                </FormalInput>

                {mode == "register" && (
                    <FormalInput label="Invite code">
                        <Input value={invite} />
                    </FormalInput>
                )}

                {error && <Text class="error" content={error} />}

                <Button
                    variant="accent"
                    centered
                    extraPadding
                    disabled={busy || username.value.trim() == "" || password.value == ""}
                    onClick={submit}
                >
                    {busy ? "..." : mode == "login" ? "Sign in" : "Create account"}
                </Button>

                <Button
                    variant="always-transparent"
                    onClick={() => { setMode(mode == "login" ? "register" : "login"); setError(null); }}
                >
                    <Text dim content={mode == "login" ? "Create an account" : "Back to sign in"} />
                </Button>

                <div class="auth-divider"><span>or</span></div>

                <TextIconLinkButton
                    class="rotur-login"
                    variant="panel"
                    href="/api/auth/rotur/authorize?next=%2F"
                >
                    <Link2 size={16} /> Sign in with Rotur
                </TextIconLinkButton>
                <Text
                    dim
                    class="rotur-note"
                    content="Use Rotur to sign in, or link it to an existing account in Settings."
                />
            </Container>
        </Content>
    )
}

import { useState } from "preact/hooks";
import { useSignal } from "@preact/signals";
import { useLocation } from "preact-iso";
import { Container, Content, FormalInput, Header1, Input, Tabs, Text, TextIconButton } from "flufi-ui/components";
import { LogIn } from "lucide-preact";

import "./style.css";
import { login, register } from "../../common/auth";
import { PasswordInput } from "../../components/PasswordInput/PasswordInput";

/**
 * Local sign-in / registration. Authentication is a cookie session on the
 * Flask server, so there is nothing to persist client-side afterwards.
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
            <Container box extra_gap centered_x class="auth-box">
                <Header1>mcmusic</Header1>
                <Text dim content={mode == "login"
                    ? "Sign in to your library."
                    : "Create an account. The first account is the admin; after that you need an invite code."} />

                <Tabs
                    value={mode}
                    tabs={[
                        { name: "Sign in", value: "login" },
                        { name: "Register", value: "register" },
                    ]}
                    onChange={(v) => { setMode(v as "login" | "register"); setError(null); }}
                />

                <FormalInput label="Username">
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

                <TextIconButton
                    variant="accent"
                    centered
                    disabled={busy || username.value.trim() == "" || password.value == ""}
                    onClick={submit}
                >
                    <LogIn size={20} />
                    {busy ? "..." : mode == "login" ? "Sign in" : "Create account"}
                </TextIconButton>
            </Container>
        </Content>
    )
}

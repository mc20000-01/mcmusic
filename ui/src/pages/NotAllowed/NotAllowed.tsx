/** 403 page shown when the account may not use the client.
 */
import { Container, Content, Header1, Text, TextButton } from "flufi-ui/components";
import { logout } from "../../common/auth";

import "./style.css";

export function NotAllowedPage() {
    return (
        <Content class="not-allowed" centered>
            <Header1>Access Denied</Header1>
            <Text content={`You have been denied access to the music server (${window.location.hostname}).`} />
            <Container horizontal>
                <TextButton extraPadding
                    onClick={() => {
                        logout();
                    }}
                >
                    Log out
                </TextButton>
                <TextButton extraPadding
                    onClick={() => {
                        window.location.reload();
                    }}
                >
                    Refresh
                </TextButton>
            </Container>
        </Content>
    )
}

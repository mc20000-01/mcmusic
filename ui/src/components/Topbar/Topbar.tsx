/** Top bar: brand, search and navigation to add-music/settings.
 */
import { Home, LogOut, Plus } from "lucide-preact";
import { Container, HeaderContainer, IconButton, IconLinkButton, If, LinkButton, Text } from "flufi-ui/components";
import { MOBILE } from "flufi-ui/common";
import { SearchBar } from "../SearchBar/SearchBar";
import { currentUser, logout } from "../../common/auth";

import "./style.css";

export function Topbar() {
    return (
        <HeaderContainer other={{ id: "topbar" }}>
            <If cond={!MOBILE.value}>
                <Left />
            </If>
            <Middle />
        </HeaderContainer>
    )
}

function Left() {
    return (
        <Container class="left">
            <LinkButton href="/" variant="always-transparent" class="logo text">mcmusic</LinkButton>
        </Container>
    )
}

function Middle() {
    return (
        <Container class="middle">
            <IconLinkButton href="/">
                <Home size={20} />
            </IconLinkButton>
            <SearchBar />
            <IconLinkButton href="/upload">
                <Plus size={20} />
            </IconLinkButton>
            {currentUser.value && (
                <Text class="user" content={currentUser.value.username} />
            )}
            <IconButton
                title="Log out"
                onClick={async () => {
                    await logout();
                    window.location.href = "/auth";
                }}
            >
                <LogOut size={18} />
            </IconButton>
        </Container>
    )
}

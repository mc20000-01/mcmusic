/** Top bar: brand, search and navigation to add-music/settings.
 */
import type { ComponentChildren } from "preact";
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

/** flufi's link buttons take no title, so label them from the outside and give
 * the anchor a real accessible name. */
function IconLink(props: { href: string; label: string; children: ComponentChildren }) {
    return (
        <span class="icon-tip" title={props.label}>
            <IconLinkButton href={props.href}>
                {props.children}
                <span class="sr-only">{props.label}</span>
            </IconLinkButton>
        </span>
    )
}

function Middle() {
    return (
        <Container class="middle">
            <IconLink href="/" label="Home">
                <Home size={20} />
            </IconLink>
            <SearchBar />
            <IconLink href="/upload" label="Add music">
                <Plus size={20} />
            </IconLink>
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

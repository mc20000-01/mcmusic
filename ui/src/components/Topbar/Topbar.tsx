/** Top bar: brand, search and navigation on one row at every width.
 */
import type { ComponentChildren } from "preact";
import { Home, LogOut, Menu, Music2, Plus } from "lucide-preact";
import { Container, HeaderContainer, IconButton, IconLinkButton, If, Text } from "flufi-ui/components";
import { mobileChrome } from "../../common/responsive";
import { SearchBar } from "../SearchBar/SearchBar";
import { currentUser, logout } from "../../common/auth";
import { toggleMobileSidebar } from "../LeftSidebar/LeftSidebar";

import "./style.css";

export function Topbar() {
    return (
        <HeaderContainer other={{ id: "topbar" }}>
            <Container class="middle">
                <IconLink href="/" label="mcmusic home" class="brand-link">
                    <span class="brand-mark"><Music2 size={18} /></span>
                    <span class="logo text">mcmusic</span>
                </IconLink>
                <If cond={mobileChrome.value}>
                    <IconButton title="Open menu" onClick={toggleMobileSidebar}>
                        <Menu size={20} />
                    </IconButton>
                </If>
                <If cond={!mobileChrome.value}>
                    <IconLink href="/" label="Home">
                        <Home size={20} />
                    </IconLink>
                </If>
                <SearchBar />
                <IconLink href="/upload" label="Add music">
                    <Plus size={20} />
                </IconLink>
                {currentUser.value && (
                    <span class="user-pill" title={currentUser.value.username}>
                        <span class="user-avatar" aria-hidden="true">
                            {currentUser.value.username.slice(0, 1).toUpperCase()}
                        </span>
                        <Text class="user" content={currentUser.value.username} />
                    </span>
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
        </HeaderContainer>
    )
}

/** flufi's link buttons take no title, so label them from the outside and give
 * the anchor a real accessible name. */
function IconLink(props: {
    href: string;
    label: string;
    children: ComponentChildren;
    class?: string;
}) {
    return (
        <span class="icon-tip" title={props.label}>
            <IconLinkButton href={props.href} class={props.class}>
                {props.children}
                <span class="sr-only">{props.label}</span>
            </IconLinkButton>
        </span>
    )
}

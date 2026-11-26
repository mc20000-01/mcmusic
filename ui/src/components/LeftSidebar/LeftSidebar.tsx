/** Sidebar with library shortcuts and account links. Desktop keeps a
 * collapsible rail; phones get a slide-in drawer opened from the top bar.
 */
import type { ComponentChildren } from "preact";
import { useEffect } from "preact/hooks";
import { useLocation } from "preact-iso";
import { signal, type Signal } from "@preact/signals";
import "./style.css";
import {
    Branch, Container, Else, IconButton, MiniHeader, TextLinkButton, Then,
} from "flufi-ui/components";
import { addClass } from "flufi-ui/common";
import { mobileChrome, tier } from "../../common/responsive";
import {
    Download, Headphones, Heart, Home, ListMusic, MonitorSmartphone,
    PanelLeftClose, PanelLeftOpen, Search, Settings, ShieldCheck, Upload,
    UserRound, X,
} from "lucide-preact";
import { LeftSidebarDesktopClosedContent, LeftSidebarDesktopOpenedContent } from "./Desktop";
import { currentUser } from "../../common/auth";

const leftSidebarOpen: Signal<boolean> = signal(true);
const leftSidebarMobileOpen: Signal<boolean> = signal(false);

export function toggleMobileSidebar() {
    leftSidebarMobileOpen.value = !leftSidebarMobileOpen.value;
}

function closeMobileSidebar() {
    leftSidebarMobileOpen.value = false;
}

// NOTE: when adding sidebar resizing, try setting the transition for width to 0
// TODO: mobile - swipe open  / close (use progress so its smooth)

export function LeftSidebar() {
    const loc = useLocation();
    const open = mobileChrome.value ? leftSidebarMobileOpen.value : leftSidebarOpen.value;

    useEffect(() => { closeMobileSidebar(); }, [loc.path]);

    // Compact windows use the rail always; a full open sidebar would clip.
    useEffect(() => {
        if (tier.value === "compact") leftSidebarOpen.value = false;
    }, [tier.value]);

    return (
        <>
            <Container
                other={{ id: "left-sidebar" }}
                class={addClass(
                    open && "open",
                    mobileChrome.value ? "mobile" : "desktop"
                )}
            >
                <Branch cond={mobileChrome.value}>
                    <Then>
                        <MobileContent />
                    </Then>
                    <Else>
                        <DesktopContent />
                    </Else>
                </Branch>
            </Container>
            {mobileChrome.value && leftSidebarMobileOpen.value && (
                <div class="mobile-sidebar-scrim" aria-hidden="true" onClick={closeMobileSidebar} />
            )}
        </>
    )
}

// desktop
function DesktopContent() {
    return (
        <Container class={addClass(
            "desktop",
            leftSidebarOpen.value && "open"
        )}>
            <IconButton
                class="openclose"
                title={leftSidebarOpen.value ? "Collapse sidebar" : "Expand sidebar"}
                onClick={() => leftSidebarOpen.value = !leftSidebarOpen.value}
            >
                <Branch cond={leftSidebarOpen.value}>
                    <Then>
                        <PanelLeftClose size={18} />
                    </Then>
                    <Else>
                        <PanelLeftOpen size={18} />
                    </Else>
                </Branch>
            </IconButton>
            <LeftSidebarDesktopOpenedContent />
            <LeftSidebarDesktopClosedContent />
        </Container>
    )
}

// mobile
function MobileContent() {
    return (
        <Container class="mobile-drawer">
            <Container horizontal centered_y class="drawer-head">
                <MiniHeader>mcmusic</MiniHeader>
                <IconButton title="Close menu" onClick={closeMobileSidebar}>
                    <X size={18} />
                </IconButton>
            </Container>

            <MiniHeader dim>Library</MiniHeader>
            <MobileLink href="/" icon={<Home size={18} />}>Home</MobileLink>
            <MobileLink href="/search" icon={<Search size={18} />}>Search</MobileLink>
            <MobileLink href="/likes" icon={<Heart size={18} />}>Liked songs</MobileLink>
            <MobileLink href="/artists" icon={<UserRound size={18} />}>Artists</MobileLink>
            <MobileLink href="/playlists" icon={<ListMusic size={18} />}>Playlists</MobileLink>
            <MobileLink href="/downloads" icon={<Download size={18} />}>Downloads</MobileLink>
            <MobileLink href="/listeners" icon={<Headphones size={18} />}>Listening now</MobileLink>
            <MobileLink href="/upload" icon={<Upload size={18} />}>Add music</MobileLink>

            <MiniHeader dim>Account</MiniHeader>
            <MobileLink href="/settings" icon={<Settings size={18} />}>Settings</MobileLink>
            <MobileLink href="/devices" icon={<MonitorSmartphone size={18} />}>Devices</MobileLink>
            {currentUser.value?.is_admin && (
                <MobileLink href="/admin" icon={<ShieldCheck size={18} />}>Admin</MobileLink>
            )}
        </Container>
    )
}

function MobileLink(props: { href: string; icon: ComponentChildren; children: ComponentChildren }) {
    return (
        <TextLinkButton href={props.href} class="drawer-link" onClick={closeMobileSidebar}>
            {props.icon}
            <span>{props.children}</span>
        </TextLinkButton>
    )
}

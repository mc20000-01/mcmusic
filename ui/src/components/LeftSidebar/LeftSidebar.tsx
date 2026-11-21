/** Desktop sidebar with library shortcuts and account links.
 */
import { signal, type Signal } from "@preact/signals";
import "./style.css";
import { Branch, Container, Else, IconButton, Then } from "flufi-ui/components";
import { addClass, MOBILE } from "flufi-ui/common";
import { PanelLeftClose, PanelLeftOpen } from "lucide-preact";
import { LeftSidebarDesktopClosedContent, LeftSidebarDesktopOpenedContent } from "./Desktop";

const leftSidebarOpen: Signal<boolean> = signal(true);
const leftSidebarMobileOpen: Signal<boolean> = signal(false);

// NOTE: when adding sidebar resizing, try setting the transition for width to 0
// TODO: mobile - swipe open  / close (use progress so its smooth)

export function LeftSidebar() {
    const open = MOBILE.value ? leftSidebarMobileOpen.value : leftSidebarOpen.value;
    
    return (
        <Container
            other={{ id: "left-sidebar" }}
            class={addClass(
                open && "open",
                MOBILE.value ? "mobile" : "desktop"
            )}
        >
            <Branch cond={MOBILE.value}>
                <Then>
                    <MobileContent />
                </Then>
                <Else>
                    <DesktopContent />
                </Else>
            </Branch>
        </Container>
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
        <Container class="mobile">
            
        </Container>
    )
}

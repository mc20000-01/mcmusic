/** Sidebar layout used at desktop widths.
 */
import { Container, MiniHeader, TextLinkButton } from "flufi-ui/components"
import {
    Home, ListMusic, MonitorSmartphone, Settings, ShieldCheck, Upload, UserRound
} from "lucide-preact"
import { currentUser } from "../../common/auth"

export function LeftSidebarDesktopOpenedContent() {
    return (
        <Container class="opened">
            <MiniHeader dim>Library</MiniHeader>
            <TextLinkButton href="/"><Home size={16} /> Home</TextLinkButton>
            <TextLinkButton href="/artists"><UserRound size={16} /> Artists</TextLinkButton>
            <TextLinkButton href="/playlists"><ListMusic size={16} /> Playlists</TextLinkButton>
            <TextLinkButton href="/upload"><Upload size={16} /> Add music</TextLinkButton>
            <MiniHeader dim>Account</MiniHeader>
            <TextLinkButton href="/settings"><Settings size={16} /> Settings</TextLinkButton>
            <TextLinkButton href="/devices"><MonitorSmartphone size={16} /> Devices</TextLinkButton>
            {currentUser.value?.is_admin && (
                <TextLinkButton href="/admin"><ShieldCheck size={16} /> Admin</TextLinkButton>
            )}
        </Container>
    )
}
export function LeftSidebarDesktopClosedContent() {
    return (
        <Container class="closed">
            <TextLinkButton href="/"><Home size={18} /></TextLinkButton>
            <TextLinkButton href="/artists"><UserRound size={18} /></TextLinkButton>
            <TextLinkButton href="/playlists"><ListMusic size={18} /></TextLinkButton>
            <TextLinkButton href="/settings"><Settings size={18} /></TextLinkButton>
        </Container>
    )
}

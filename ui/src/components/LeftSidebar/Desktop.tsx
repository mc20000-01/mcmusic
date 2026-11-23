/** Sidebar layout used at desktop widths.
 */
import { Container, MiniHeader, TextLinkButton } from "flufi-ui/components"
import {
    Download, Headphones, Heart, Home, ListMusic, MonitorSmartphone, Search,
    Settings, ShieldCheck, Upload, UserRound
} from "lucide-preact"
import { currentUser } from "../../common/auth"

export function LeftSidebarDesktopOpenedContent() {
    return (
        <Container class="opened">
            <MiniHeader dim>Library</MiniHeader>
            <TextLinkButton href="/"><Home size={16} /> Home</TextLinkButton>
            <TextLinkButton href="/search"><Search size={16} /> Search</TextLinkButton>
            <TextLinkButton href="/likes"><Heart size={16} /> Liked songs</TextLinkButton>
            <TextLinkButton href="/artists"><UserRound size={16} /> Artists</TextLinkButton>
            <TextLinkButton href="/playlists"><ListMusic size={16} /> Playlists</TextLinkButton>
            <TextLinkButton href="/downloads"><Download size={16} /> Downloads</TextLinkButton>
            <TextLinkButton href="/listeners"><Headphones size={16} /> Listening now</TextLinkButton>
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
            <TextLinkButton href="/search"><Search size={18} /></TextLinkButton>
            <TextLinkButton href="/likes"><Heart size={18} /></TextLinkButton>
            <TextLinkButton href="/artists"><UserRound size={18} /></TextLinkButton>
            <TextLinkButton href="/playlists"><ListMusic size={18} /></TextLinkButton>
            <TextLinkButton href="/downloads"><Download size={18} /></TextLinkButton>
            <TextLinkButton href="/settings"><Settings size={18} /></TextLinkButton>
        </Container>
    )
}

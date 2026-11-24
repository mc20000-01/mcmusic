/** Route table and page chrome. The shell is a fixed column: Topbar, an
 * optional sidebar, the routed page, and the PlayerBar pinned to the bottom.
 */
import { LocationProvider, Route, Router, useLocation } from "preact-iso";

import "./env.css";
import "./app.css";
import { Container, MainContainer, TextIconButton } from "flufi-ui/components";
import { Download, RefreshCw, WifiOff } from "lucide-preact";

import { HomePage } from "./pages/Home/Home";
import { NotFoundPage } from "./pages/NotFound/NotFound";
import { AuthPage } from "./pages/Auth/Auth";
import { ResetPage } from "./pages/Auth/Reset";
import { Topbar } from "./components/Topbar/Topbar";
import { LeftSidebar } from "./components/LeftSidebar/LeftSidebar";
import { UploadPage } from "./pages/Upload/Upload";
import { PlaylistsPage } from "./pages/Playlists/Playlists";
import { PlaylistPage } from "./pages/Playlists/Playlist";
import { SettingsPage } from "./pages/Settings/Settings";
import { DevicesPage } from "./pages/Devices/Devices";
import { AdminPage } from "./pages/Admin/Admin";
import { useEffect } from "preact/hooks";
import { allowed } from "./common/state";
import { authCheckDone, peekAuth } from "./common/auth";
import { loadPrefs } from "./common/prefs";
import { addClass, MOBILE } from "flufi-ui/common";
import { ArtistPage } from "./pages/Artist/Artist";
import { ArtistsPage } from "./pages/Artists/Artists";
import { SetPage } from "./pages/Set/Set";
import { PlayerBar } from "./components/PlayerBar/PlayerBar";
import { SearchPage } from "./pages/Search/Search";
import { LikesPage } from "./pages/Likes/Likes";
import { DownloadsPage } from "./pages/Downloads/Downloads";
import { ListenersPage, ProfilePage } from "./pages/Profile/Profile";
import {
    activateUpdate, bootPlaybackSync, bootPwa, installPwa,
    pwaInstallAvailable, pwaUpdateReady,
} from "./common/integrations";
import { signal } from "@preact/signals";
import { SELFHOST_GUIDE } from "./common/links";

export function App() {
    return (
        <LocationProvider>
            <Main />
        </LocationProvider>
    )
}

const offline = signal(typeof navigator !== "undefined" && !navigator.onLine);

/** Small unobtrusive banners for PWA updates/install and offline state. */
function SystemBanners() {
    return (
        <div class="system-banners">
            {offline.value && (
                <div class="system-banner" role="status">
                    <WifiOff size={15} />
                    <span>Offline — cached music still plays. See the <a href={SELFHOST_GUIDE} target="_blank" rel="noopener noreferrer">self-hosting guide</a> for setup help.</span>
                </div>
            )}
            {pwaUpdateReady.value && (
                <div class="system-banner" role="status">
                    <RefreshCw size={15} />
                    <span>An update is ready.</span>
                    <TextIconButton variant="accent" onClick={activateUpdate}>Reload</TextIconButton>
                </div>
            )}
            {pwaInstallAvailable.value && (
                <div class="system-banner" role="status">
                    <Download size={15} />
                    <span>Install mcmusic for offline use.</span>
                    <TextIconButton variant="panel" onClick={installPwa}>Install</TextIconButton>
                </div>
            )}
        </div>
    );
}

export function Main() {
    const loc = useLocation();

    let showTopbar: boolean = true;
    let showSidebar: boolean = true;

    const publicPage = loc.path == "/auth" || loc.path == "/forgot" ||
        loc.path == "/reset" || loc.path == "/reset/" || loc.path == "/not-allowed";

    if (publicPage)
        showTopbar = false,
        showSidebar = false;

    if (authCheckDone.value && peekAuth() == null && !publicPage)
        loc.route("/auth");

    useEffect(() => {
        loadPrefs();
        bootPwa();
        const startSync = () => {
            if (authCheckDone.value && peekAuth()) bootPlaybackSync();
        };
        startSync();
        const unsub = authCheckDone.subscribe(startSync);
        const goOnline = () => { offline.value = false; };
        const goOffline = () => { offline.value = true; };
        window.addEventListener("online", goOnline);
        window.addEventListener("offline", goOffline);
        return () => {
            unsub();
            window.removeEventListener("online", goOnline);
            window.removeEventListener("offline", goOffline);
        };
    }, []);

    useEffect(() => {
        return allowed.subscribe(a => {
            if (a == false && loc.path != "/not-allowed") {
                loc.route("/not-allowed");
            } else if (a && loc.path == "/not-allowed") {
                loc.route("/");
            }
        })
    }, [loc.path]);

    return (
        <Container
            key="app"
            class={addClass(
                MOBILE.value && "mobile"
            )}
        >
            <SystemBanners />
            {showTopbar && (
                <Topbar />
            )}
            <MainContainer>
                {showSidebar && (
                    <LeftSidebar />
                )}
                <Router>
                    <Route path="/" component={HomePage} />
                    <Route path="/auth" component={AuthPage} />
                    <Route path="/forgot" component={ResetPage} />
                    <Route path="/reset" component={ResetPage} />
                    <Route path="/reset/" component={ResetPage} />
                    <Route path="/search" component={SearchPage} />
                    <Route path="/likes" component={LikesPage} />
                    <Route path="/downloads" component={DownloadsPage} />
                    <Route path="/listeners" component={ListenersPage} />
                    <Route path="/u/:username" component={ProfilePage} />
                    <Route path="/upload" component={UploadPage} />
                    <Route path="/artists" component={ArtistsPage} />
                    <Route path="/artist/:uuid" component={ArtistPage} />
                    <Route path="/set/:uuid" component={SetPage} />
                    <Route path="/playlists" component={PlaylistsPage} />
                    <Route path="/playlist/:id" component={PlaylistPage} />
                    <Route path="/settings" component={SettingsPage} />
                    <Route path="/devices" component={DevicesPage} />
                    <Route path="/admin" component={AdminPage} />

                    <Route default component={NotFoundPage} />
                </Router>
            </MainContainer>
            {showTopbar && <PlayerBar />}
        </Container>
    )
}

/** Route table and page chrome. The shell is a fixed column: Topbar, an
 * optional sidebar, the routed page, and the PlayerBar pinned to the bottom.
 */
import { LocationProvider, Route, Router, useLocation } from "preact-iso";

import "./env.css";
import "./app.css";
import { Container, MainContainer } from "flufi-ui/components";

import { HomePage } from "./pages/Home/Home";
import { NotFoundPage } from "./pages/NotFound/NotFound";
import { AuthPage } from "./pages/Auth/Auth";
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

export function App() {
    return (
        <LocationProvider>
            <Main />
        </LocationProvider>
    )
}

export function Main() {
    const loc = useLocation();

    let showTopbar: boolean = true;
    let showSidebar: boolean = true;

    if (loc.path == "/auth" || loc.path == "/not-allowed")
        showTopbar = false,
        showSidebar = false;

    if (authCheckDone.value && peekAuth() == null && loc.path != "/auth")
        loc.route("/auth");

    useEffect(() => {
        loadPrefs();
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

"""All routed views: home, search, library, collections, likes, playlists,
requests, settings and the admin console.

Screens are plain QScrollAreas that reload from the API when shown. Data loads
on the worker pool; widgets are built on the GUI thread only.
"""
from __future__ import annotations

import time
from dataclasses import replace
from typing import Any, Callable, Optional, Sequence

from shiboken6 import isValid
from PySide6.QtCore import QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QColor, QDesktopServices, QGuiApplication, QPainter, QPen,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QColorDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .models import (
    BuildInfo,
    DeviceRow,
    ListeningUser,
    AdminStats,
    AdminUser,
    AlbumRef,
    ArtistRef,
    HomeData,
    PlaylistRef,
    RequestRow,
    SearchData,
    Settings,
    Track,
    fmt_bytes,
    fmt_time,
    fmt_total,
    fmt_uptime,
)
from .widgets import (
    EmptyState,
    Glyph,
    Hero,
    IconButton,
    LabeledField,
    McButton,
    PageHead,
    Panel,
    Segmented,
    Shelf,
    Spinner,
    StatCard,
    Sheet,
    StatusChip,
    Switch,
    TileGrid,
    Txt,
    confirm,
    prompt,
)
from .version import VERSION

STATUS_TOKEN = {
    "done": "ok",
    "failed": "err",
    "rejected": "err",
    "cancelled": "err",
    "running": "accent",
    "approved": "accent",
    "pending": "warn",
}


class Screen(QScrollArea):
    """Scrollable page with a centred, max-width content column."""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.shell = window
        self.track_list = None
        self._loading_row: Optional[QWidget] = None
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport().setAutoFillBackground(False)
        self.setStyleSheet("QScrollArea{background:transparent;border:none;}"
                           "QScrollArea>QWidget>QWidget{background:transparent;}")

        host = QWidget()
        host.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch(1)
        self.body = QWidget()
        self.body.setMaximumWidth(1180)
        self.body.setStyleSheet("background: transparent;")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(26, 22, 26, 40)
        self.body_layout.setSpacing(0)
        self.body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        row.addWidget(self.body, 100)
        row.addStretch(1)
        outer.addLayout(row)
        self.setWidget(host)

    # layout helpers -----------------------------------------------------
    def add(self, widget: QWidget, spacing: int = 0) -> QWidget:
        self.body_layout.addWidget(widget)
        if spacing:
            self.body_layout.addSpacing(spacing)
        return widget

    def space(self, height: int) -> None:
        self.body_layout.addSpacing(height)

    def clear(self) -> None:
        while self.body_layout.count():
            item = self.body_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.track_list = None
        self._loading_row = None

    def reset_scroll(self) -> None:
        self.verticalScrollBar().setValue(0)

    # async --------------------------------------------------------------
    def run(self, fn: Callable[[], Any],
            ok: Callable[[Any], None],
            error: Optional[Callable[[Exception], None]] = None) -> None:
        def safe_ok(value) -> None:
            if not isValid(self):
                return
            try:
                ok(value)
            except RuntimeError:
                return

        def safe_error(exc: Exception) -> None:
            if not isValid(self):
                return
            self.shell.toast(str(exc) or "Something went wrong")
            if error:
                error(exc)

        self.shell.run(fn, safe_ok, safe_error)

    def loading(self, text: str = "Loading…") -> None:
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(0, 40, 0, 40)
        line.setSpacing(10)
        line.addStretch(1)
        line.addWidget(Spinner(18))
        line.addWidget(Txt(text, size=13, token="dim2"))
        line.addStretch(1)
        self._loading_row = row
        self.add(row)

    def stop_loading(self) -> None:
        if self._loading_row is None:
            return
        self.body_layout.removeWidget(self._loading_row)
        self._loading_row.setParent(None)
        self._loading_row.deleteLater()
        self._loading_row = None

    def load(self) -> None:
        pass

    # hooks --------------------------------------------------------------
    def apply_like(self, track_id: int, liked: bool) -> None:
        if self.track_list is not None:
            self.track_list.set_liked(track_id, liked)

    def apply_settings(self, settings: Settings) -> None:
        pass

    def refresh_theme(self) -> None:
        self.viewport().update()


# ── shared bits ────────────────────────────────────────────────────────────


def section_head(title: str, meta: str = "", actions: Sequence[QWidget] = ()) -> QWidget:
    widget = QWidget()
    line = QHBoxLayout(widget)
    line.setContentsMargins(0, 0, 0, 12)
    line.setSpacing(10)
    line.addWidget(Txt(title, size=18, family="display", token="fg"), 0,
                   Qt.AlignmentFlag.AlignBottom)
    if meta:
        line.addWidget(Txt(meta.upper(), size=9, family="mono", token="dim2", spacing=1.2),
                       0, Qt.AlignmentFlag.AlignBottom)
    line.addStretch(1)
    for action in actions:
        line.addWidget(action)
    return widget


def _album_items(albums: Sequence[AlbumRef]) -> list[dict]:
    return [
        {
            "title": a.album,
            "subtitle": " · ".join(x for x in [a.artist, f"{a.n} tracks"] if x),
            "cover_id": a.cover_id,
            "kind": "album",
            "payload": a,
        }
        for a in albums
    ]


def _artist_items(artists: Sequence[ArtistRef]) -> list[dict]:
    return [
        {
            "title": a.artist,
            "subtitle": f"{a.n} tracks · {a.albums} albums",
            "cover_id": a.cover_id,
            "round": True,
            "kind": "artist",
            "payload": a,
        }
        for a in artists
    ]


def _playlist_items(playlists: Sequence[PlaylistRef]) -> list[dict]:
    return [
        {
            "title": p.name,
            "subtitle": f"{p.n} tracks",
            "cover_id": p.cover_id,
            "kind": "playlist",
            "payload": p,
        }
        for p in playlists
    ]


# ── home ───────────────────────────────────────────────────────────────────


class HomeScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        self.loading("Warming up the shelves…")
        self.run(self.shell.repo.home, self._render)

    def _render(self, home: HomeData) -> None:
        self.clear()
        hour = time.localtime().tm_hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
        head = PageHead("Home", greeting, f"{len(home.sections)} shelves")
        self.add(head, 16)

        if home.albums:
            shelf = Shelf("Fresh pressings", f"{len(home.albums)} albums")
            shelf.set_items(_album_items(home.albums))
            shelf.opened.connect(lambda a: self.shell.navigate(("album", a.album)))
            shelf.played.connect(lambda a: self.shell.play_album(a.album))
            browse = McButton("All albums", small=True, ghost=True)
            browse.clicked.connect(lambda: self.shell.navigate(("library", "albums")))
            shelf.add_action(browse)
            self.add(shelf, 10)

        for section in home.sections:
            if not section.tracks:
                continue
            shelf = Shelf(section.title, f"{len(section.tracks)} tracks")
            play_all = McButton("Play all", small=True, solid=True, icon="play")
            play_all.clicked.connect(
                lambda _=False, tracks=section.tracks: self.shell.play_tracks(tracks, 0)
            )
            shelf.add_action(play_all)
            shelf.set_items([
                {
                    "title": t.title,
                    "subtitle": t.artist,
                    "cover_id": t.id,
                    "kind": "track",
                    "payload": (section.tracks, i),
                }
                for i, t in enumerate(section.tracks)
            ])
            shelf.opened.connect(
                lambda payload: self.shell.play_tracks(payload[0], payload[1])
            )
            shelf.played.connect(
                lambda payload: self.shell.play_tracks(payload[0], payload[1])
            )
            self.add(shelf, 10)

        if not home.sections and not home.albums:
            self.add(EmptyState(
                "Your library is waiting for its first song",
                "Ask an admin to scan the music folder, or add something yourself from Requests.",
                icon="disc-3",
                action=("Add music", lambda: self.shell.navigate(("requests",))),
            ))
        self.reset_scroll()


# ── search ─────────────────────────────────────────────────────────────────


class SearchScreen(Screen):
    def __init__(self, window, query: str = "", parent=None):
        super().__init__(window, parent)
        self._query = query
        self._token = 0
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(260)
        self._debounce.timeout.connect(self._search)

        self.head = PageHead("Search", "Find something to play", "")
        self.add(self.head, 16)
        self.results = QWidget()
        self.rlayout = QVBoxLayout(self.results)
        self.rlayout.setContentsMargins(0, 0, 0, 0)
        self.rlayout.setSpacing(0)
        self.add(self.results)

        if query.strip():
            self._debounce.start(10)
        else:
            self._render_empty()

    def set_query(self, query: str) -> None:
        self._query = query
        self._debounce.start()

    def _search(self) -> None:
        query = self._query.strip()
        self._token += 1
        token = self._token
        if not query:
            self._render_empty()
            return
        self._render_loading(query)
        self.run(
            lambda: self.shell.repo.search(query),
            lambda data: self._render(query, data, token),
        )

    def _clear_results(self) -> None:
        while self.rlayout.count():
            item = self.rlayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.track_list = None

    def _render_loading(self, query: str) -> None:
        self._clear_results()
        self.head.title_label.setText("Search")
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(0, 30, 0, 30)
        line.setSpacing(10)
        line.addWidget(Spinner(18))
        line.addWidget(Txt(f'Searching for “{query}”…', size=13, token="dim2"))
        line.addStretch(1)
        self.rlayout.addWidget(row)

    def _render_empty(self) -> None:
        self._clear_results()
        self.head.title_label.setText("Search")
        self.rlayout.addWidget(EmptyState(
            "Search your library",
            "Songs, albums and artists — start typing in the field above.",
            icon="search",
        ))

    def _render(self, query: str, data: SearchData, token: int) -> None:
        if token != self._token or query != self._query.strip():
            return
        self._clear_results()
        self.head.title_label.setText(f"“{query}”")
        total = len(data.tracks) + len(data.albums) + len(data.artists)
        if not total:
            self.rlayout.addWidget(EmptyState(
                "Nothing matched",
                "Try a different spelling or browse the library.",
                icon="search",
                action=("Browse library", lambda: self.shell.navigate(("library",))),
            ))
            return

        if data.tracks:
            self.rlayout.addWidget(section_head("Songs", f"{len(data.tracks)} results"))
            tl = self.shell.make_track_list(data.tracks, self)
            tl.setParent(self.results)
            self.rlayout.addWidget(tl)
            self.track_list = tl
            self.rlayout.addSpacing(22)

        if data.albums:
            self.rlayout.addWidget(section_head("Albums", f"{len(data.albums)} results"))
            grid = TileGrid()
            grid.set_items(_album_items(data.albums))
            grid.opened.connect(lambda a: self.shell.navigate(("album", a.album)))
            grid.played.connect(lambda a: self.shell.play_album(a.album))
            self.rlayout.addWidget(grid)
            self.rlayout.addSpacing(22)

        if data.artists:
            self.rlayout.addWidget(section_head("Artists", f"{len(data.artists)} results"))
            grid = TileGrid()
            grid.set_items(_artist_items(data.artists))
            grid.opened.connect(lambda a: self.shell.navigate(("artist", a.artist)))
            grid.played.connect(lambda a: self.shell.play_artist(a.artist))
            self.rlayout.addWidget(grid)


# ── library ────────────────────────────────────────────────────────────────


class LibraryScreen(Screen):
    def __init__(self, window, tab: str = "songs", parent=None):
        super().__init__(window, parent)
        self.tab = tab if tab in ("songs", "albums", "artists", "playlists") else "songs"
        self.tracks: list[Track] = []
        head = PageHead("Library", "Everything on the server", "")
        self.seg = Segmented(
            [("songs", "Songs"), ("albums", "Albums"), ("artists", "Artists"),
             ("playlists", "Playlists")], self.tab
        )
        self.seg.changed.connect(self._switch)
        head.add_action(self.seg)
        self.add(head, 16)
        self.content = QWidget()
        self.clayout = QVBoxLayout(self.content)
        self.clayout.setContentsMargins(0, 0, 0, 0)
        self.clayout.setSpacing(0)
        self.add(self.content)
        self.load()

    def _switch(self, tab: str) -> None:
        self.tab = tab
        self.load()

    def _clear_content(self) -> None:
        while self.clayout.count():
            item = self.clayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.track_list = None

    def load(self) -> None:
        self._clear_content()
        self.loading()
        if self.tab == "songs":
            self.run(self.shell.repo.tracks, self._render_songs)
        elif self.tab == "albums":
            self.run(self.shell.repo.albums, self._render_albums)
        elif self.tab == "artists":
            self.run(self.shell.repo.artists, self._render_artists)
        else:
            self.run(self.shell.repo.playlists, self._render_playlists)

    def _render_playlists(self, playlists: list[PlaylistRef]) -> None:
        self._clear_content()
        if not playlists:
            self.clayout.addWidget(EmptyState(
                "No playlists yet",
                "Faves and Likes appear here automatically once you listen and like tracks.",
                icon="list-music",
            ))
            return
        grid = TileGrid()
        grid.set_items(_playlist_items(playlists))
        grid.opened.connect(lambda p: self.shell.navigate(("playlist", p.id)))
        grid.played.connect(lambda p: self.shell.play_playlist(p.id))
        self.clayout.addWidget(grid)

    def _render_songs(self, tracks: list[Track]) -> None:
        self._clear_content()
        self.tracks = tracks
        if not tracks:
            self.clayout.addWidget(EmptyState(
                "No songs yet", "Add music to the server and rescan.",
                icon="music",
            ))
            return
        self.clayout.addWidget(section_head("Songs", f"{len(tracks)} tracks"))
        tl = self.shell.make_track_list(tracks, self)
        tl.setParent(self.content)
        self.clayout.addWidget(tl)
        self.track_list = tl

    def _render_albums(self, albums: list[AlbumRef]) -> None:
        self._clear_content()
        if not albums:
            self.clayout.addWidget(EmptyState("No albums yet", icon="disc-3"))
            return
        self.clayout.addWidget(section_head("Albums", f"{len(albums)} albums"))
        grid = TileGrid()
        grid.set_items(_album_items(albums))
        grid.opened.connect(lambda a: self.shell.navigate(("album", a.album)))
        grid.played.connect(lambda a: self.shell.play_album(a.album))
        self.clayout.addWidget(grid)

    def _render_artists(self, artists: list[ArtistRef]) -> None:
        self._clear_content()
        if not artists:
            self.clayout.addWidget(EmptyState("No artists yet", icon="users"))
            return
        self.clayout.addWidget(section_head("Artists", f"{len(artists)} artists"))
        grid = TileGrid()
        grid.set_items(_artist_items(artists))
        grid.opened.connect(lambda a: self.shell.navigate(("artist", a.artist)))
        grid.played.connect(lambda a: self.shell.play_artist(a.artist))
        self.clayout.addWidget(grid)


# ── album / artist ─────────────────────────────────────────────────────────


class CollectionScreen(Screen):
    def __init__(self, window, name: str, kind: str = "album", parent=None):
        super().__init__(window, parent)
        self.name = name
        self.kind = kind
        self.tracks: list[Track] = []
        self.load()

    def load(self) -> None:
        self.clear()
        self.loading()
        if self.kind == "artist":
            self.run(lambda: self.shell.repo.artist(self.name), self._render)
        else:
            self.run(lambda: self.shell.repo.album(self.name), self._render)

    def _render(self, tracks: list[Track]) -> None:
        self.clear()
        self.tracks = tracks
        if not tracks:
            self.add(PageHead("Artist" if self.kind == "artist" else "Album",
                              "", ""), 16)
            self.add(EmptyState(
                "Nothing here", "This release has no tracks on the server.",
                icon="disc-3",
                action=("Back to library", lambda: self.shell.navigate(("library",))),
            ))
            return
        cover = tracks[0].id
        total = sum(t.duration for t in tracks)
        subs = [
            tracks[0].artist if self.kind == "album" else "",
            f"{len(tracks)} tracks",
            fmt_total(total),
        ]
        hero = Hero(
            "Artist" if self.kind == "artist" else "Album",
            self.name,
            [s for s in subs if s],
            cover,
            round_=self.kind == "artist",
        )
        play = McButton("Play", solid=True, icon="play")
        play.clicked.connect(lambda: self.shell.play_tracks(tracks, 0))
        hero.add_action(play)
        shuffle = McButton("Shuffle", icon="shuffle")
        shuffle.clicked.connect(lambda: self.shell.shuffle_tracks(tracks))
        hero.add_action(shuffle)
        radio = McButton("Radio", ghost=True, icon="radio")
        radio.clicked.connect(lambda: self.shell.start_radio(tracks[0]))
        hero.add_action(radio)
        self.add(hero, 10)
        tl = self.shell.make_track_list(tracks, self)
        tl.setParent(self.body)
        self.add(tl)
        self.track_list = tl


# ── likes ──────────────────────────────────────────────────────────────────


class LikesScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        self.loading()
        self.run(self.shell.repo.likes, self._render)

    def _render(self, tracks: list[Track]) -> None:
        self.clear()
        if not tracks:
            self.add(PageHead("Liked songs", "Saved by you", ""), 16)
            self.add(EmptyState(
                "No liked songs yet",
                "Tap the heart on any track and it will show up here.",
                icon="heart",
                action=("Browse library", lambda: self.shell.navigate(("library",))),
            ))
            return
        hero = Hero(
            "Collection", "Liked songs",
            [f"{len(tracks)} tracks", fmt_total(sum(t.duration for t in tracks))],
            tracks[0].id,
        )
        play = McButton("Play", solid=True, icon="play")
        play.clicked.connect(lambda: self.shell.play_tracks(tracks, 0))
        hero.add_action(play)
        shuffle = McButton("Shuffle", icon="shuffle")
        shuffle.clicked.connect(lambda: self.shell.shuffle_tracks(tracks))
        hero.add_action(shuffle)
        self.add(hero, 10)
        tl = self.shell.make_track_list(tracks, self)
        tl.setParent(self.body)
        self.add(tl)
        self.track_list = tl


# ── playlists ──────────────────────────────────────────────────────────────


class PlaylistsScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        head = PageHead("Playlists", "Your collections", "")
        new = McButton("New playlist", solid=True, icon="plus")
        new.clicked.connect(self.shell.create_playlist)
        head.add_action(new)
        self.add(head, 16)
        self.loading()
        self.run(self.shell.repo.playlists, self._render)

    def _render(self, playlists: list[PlaylistRef]) -> None:
        self.clear()
        head = PageHead("Playlists", "Your collections", f"{len(playlists)} lists")
        new = McButton("New playlist", solid=True, icon="plus")
        new.clicked.connect(self.shell.create_playlist)
        head.add_action(new)
        self.add(head, 16)
        if not playlists:
            self.add(EmptyState(
                "No playlists yet",
                "Group tracks into a playlist — it syncs with the web and mobile apps.",
                icon="list-music",
                action=("Create playlist", self.shell.create_playlist),
            ))
            return
        grid = TileGrid()
        grid.set_items(_playlist_items(playlists))
        grid.opened.connect(lambda p: self.shell.navigate(("playlist", p.id)))
        grid.played.connect(lambda p: self.shell.play_playlist(p.id))
        self.add(grid)


class PlaylistScreen(Screen):
    def __init__(self, window, playlist_id: int, parent=None):
        super().__init__(window, parent)
        self.playlist_id = playlist_id
        self.playlist_name = ""
        self.tracks: list[Track] = []
        self.load()

    def load(self) -> None:
        self.clear()
        self.loading()
        self.run(lambda: self.shell.repo.playlist(self.playlist_id), self._render)

    def _render(self, result: tuple[str, list[Track]]) -> None:
        name, tracks = result
        self.playlist_name = name
        self.tracks = tracks
        self.clear()
        hero = Hero(
            "Playlist", name,
            [f"{len(tracks)} tracks", fmt_total(sum(t.duration for t in tracks))],
            tracks[0].id if tracks else None,
        )
        if tracks:
            play = McButton("Play", solid=True, icon="play")
            play.clicked.connect(lambda: self.shell.play_tracks(tracks, 0))
            hero.add_action(play)
            shuffle = McButton("Shuffle", icon="shuffle")
            shuffle.clicked.connect(lambda: self.shell.shuffle_tracks(tracks))
            hero.add_action(shuffle)
        rename = McButton("Rename", ghost=True)
        rename.clicked.connect(self._rename)
        hero.add_action(rename)
        delete = McButton("Delete", ghost=True, danger=True, icon="trash-2")
        delete.clicked.connect(self._delete)
        hero.add_action(delete)
        self.add(hero, 10)

        if not tracks:
            self.add(EmptyState(
                "This playlist is empty",
                "Add tracks from any song menu — “Add to playlist…”.",
                icon="list-music",
            ))
            return
        tl = self.shell.make_track_list(tracks, self, playlist_id=self.playlist_id)
        tl.setParent(self.body)
        self.add(tl)
        self.track_list = tl

    def _rename(self) -> None:
        name = prompt(self, "Rename playlist", "Name", initial=self.playlist_name,
                      confirm="Rename")
        if not name:
            return
        self.run(lambda: self.shell.repo.rename_playlist(self.playlist_id, name),
                 lambda _: (self.shell.refresh_playlists(), self.shell.toast("Renamed"),
                            self.load()))

    def _delete(self) -> None:
        if not confirm(self, "Delete playlist",
                       f"“{self.playlist_name}” will be removed. Tracks stay in the library.",
                       confirm_label="Delete"):
            return

        def job():
            self.shell.repo.delete_playlist(self.playlist_id)

        def ok(_):
            self.shell.refresh_playlists()
            self.shell.toast("Playlist deleted")
            self.shell.navigate(("playlists",), push=False)

        self.run(job, ok)


# ── requests ───────────────────────────────────────────────────────────────


class RequestLine(QWidget):
    def __init__(self, row: RequestRow, is_admin: bool, last: bool,
                 on_action: Callable[[int, str], None],
                 on_log: Callable[[RequestRow], None], parent=None):
        super().__init__(parent)
        self._last = last
        line = QHBoxLayout(self)
        line.setContentsMargins(16, 10, 16, 10)
        line.setSpacing(12)
        line.addWidget(Glyph("download", 15, "dim2"))
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)
        url = Txt(row.url, size=11, family="mono", token="fg", wrap=True)
        url.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        text.addWidget(url)
        when = time.strftime("%d %b %H:%M", time.localtime(row.created)) if row.created else ""
        who = f"@{row.username}" if row.username else "you"
        text.addWidget(Txt(f"#{row.id} · {who} · {when}", size=10, family="mono",
                           token="dim2"))
        line.addLayout(text, 1)
        line.addWidget(StatusChip(row.status or "queued",
                                  STATUS_TOKEN.get(row.status, "dim")), 0,
                       Qt.AlignmentFlag.AlignVCenter)
        if is_admin and row.status in ("pending", "failed"):
            approve = McButton("Approve", small=True, solid=True)
            approve.clicked.connect(lambda: on_action(row.id, "approve"))
            line.addWidget(approve)
            reject = McButton("Reject", small=True, ghost=True, danger=True)
            reject.clicked.connect(lambda: on_action(row.id, "reject"))
            line.addWidget(reject)
        elif row.status == "running":
            line.addWidget(Spinner(14))
        if is_admin:
            if row.status in ("pending", "running"):
                cancel = IconButton("x", size=26, icon_size=12, tooltip="Cancel request")
                cancel.clicked.connect(lambda: on_action(row.id, "cancel"))
                line.addWidget(cancel)
            if row.status in ("failed", "rejected", "cancelled"):
                retry = IconButton("refresh-cw", size=26, icon_size=12,
                                   tooltip="Retry request")
                retry.clicked.connect(lambda: on_action(row.id, "retry"))
                line.addWidget(retry)
            delete = IconButton("trash-2", size=26, icon_size=12, tooltip="Delete request")
            delete.clicked.connect(lambda: on_action(row.id, "delete"))
            line.addWidget(delete)
        log = IconButton("info", size=26, icon_size=13, tooltip="View log")
        log.clicked.connect(lambda: on_log(row))
        line.addWidget(log)

    def paintEvent(self, _event) -> None:
        if not self._last:
            p = QPainter(self)
            p.fillRect(16, self.height() - 1, self.width() - 16, 1, theme.pal().q("line"))


class RequestsScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        head = PageHead("Requests", "Download queue", "")
        self.add(head, 16)

        add_row = QWidget()
        line = QHBoxLayout(add_row)
        line.setContentsMargins(0, 0, 0, 16)
        line.setSpacing(8)
        self.url = QLineEdit()
        self.url.setPlaceholderText("Paste an https YouTube / YouTube Music link")
        self.url.setFixedHeight(36)
        self.url.returnPressed.connect(self._add)
        line.addWidget(self.url, 1)
        button = McButton("Request", solid=True, icon="download")
        button.clicked.connect(self._add)
        line.addWidget(button)
        self.add(add_row)

        self.list_host = QWidget()
        self.llayout = QVBoxLayout(self.list_host)
        self.llayout.setContentsMargins(0, 0, 0, 0)
        self.llayout.setSpacing(0)
        self.add(self.list_host)
        self.loading()
        self.run(
            self.shell.repo.requests,
            lambda result: self._render(result[0], result[1]),
        )

    def _clear_list(self) -> None:
        while self.llayout.count():
            item = self.llayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _render(self, is_admin: bool, rows: list[RequestRow]) -> None:
        self.stop_loading()
        self._clear_list()
        if not rows:
            self.llayout.addWidget(EmptyState(
                "No requests yet",
                "Paste a link above to add music to the server.",
                icon="download",
            ))
            return
        panel = Panel("Recent requests")
        for i, row in enumerate(rows):
            panel.add_widget(RequestLine(row, is_admin, i == len(rows) - 1,
                                         self._act, self._log))
        self.llayout.addWidget(panel)

    def _add(self) -> None:
        url = self.url.text().strip()
        if not url.startswith("http"):
            self.shell.toast("Paste an https YouTube link")
            return
        self.run(lambda: self.shell.repo.request_add(url), self._added)

    def _added(self, status: str) -> None:
        self.url.clear()
        self.shell.toast("Sent for approval" if status == "pending" else "Download queued")
        self.load()

    def _act(self, request_id: int, action: str) -> None:
        def job():
            if action == "cancel":
                self.shell.repo.request_cancel(request_id)
            elif action == "retry":
                self.shell.repo.request_retry(request_id)
            elif action == "delete":
                self.shell.repo.request_delete(request_id)
            else:
                self.shell.repo.request_act(request_id, action)

        self.run(job, lambda _: self.load())

    def _log(self, row: RequestRow) -> None:
        sheet = Sheet(self, f"Request #{row.id}")
        view = QTextEdit()
        view.setReadOnly(True)
        view.setPlainText(row.log or "No log recorded yet.")
        sheet.body.addWidget(view, 1)

        def ok(data: dict) -> None:
            if not isValid(view):
                return
            text = ""
            if isinstance(data, dict):
                text = str(data.get("log") or data.get("text") or "")
            view.setPlainText(text or row.log or "No log recorded yet.")

        self.run(lambda: self.shell.repo.request_log(row.id), ok,
                 error=lambda _e: None)
        sheet.exec()


# ── settings ───────────────────────────────────────────────────────────────


class ThemeCard(QAbstractButton):
    def __init__(self, name: str, label: str, selected: bool = False, parent=None):
        super().__init__(parent)
        self.name = name
        self.label = label
        self._selected = selected
        self.setFixedSize(84, 64)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_selected(self, selected: bool) -> None:
        if self._selected != selected:
            self._selected = selected
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        surface, accent = theme.theme_preview(self.name)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(theme.pal().q("accent") if self._selected else
                      theme.pal().q("line2"), 1))
        p.setBrush(theme.pal().q("bg"))
        p.drawRoundedRect(rect, 10, 10)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(surface))
        p.drawRoundedRect(QRectF(rect.x() + 1, rect.y() + 1, rect.width() - 2, 38), 10, 10)
        p.setBrush(QColor(accent))
        p.drawRoundedRect(QRectF(rect.x() + 9, rect.y() + 29, 16, 4), 2, 2)
        p.setFont(theme.mono(9, spacing=0.5))
        p.setPen(QPen(theme.pal().q("dim")))
        p.drawText(QRectF(rect.x(), rect.y() + 40, rect.width(), rect.height() - 42),
                   int(Qt.AlignmentFlag.AlignCenter), self.label.upper())


class Swatch(QAbstractButton):
    def __init__(self, color: str, selected: bool = False, parent=None):
        super().__init__(parent)
        self.color = color
        self._selected = selected
        self.setFixedSize(24, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(color)

    def set_selected(self, selected: bool) -> None:
        if self._selected != selected:
            self._selected = selected
            self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(theme.pal().q("line2"), 1))
        p.setBrush(QColor(self.color))
        p.drawEllipse(QRectF(2, 2, 20, 20))
        if self._selected:
            p.setPen(QPen(theme.pal().q("fg"), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(0.5, 0.5, 22, 22))


class SettingsScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self._theme_cards: list[ThemeCard] = []
        self._swatches: list[Swatch] = []
        self._mode: Optional[Segmented] = None
        self._density: Optional[Segmented] = None
        self._material: Optional[Segmented] = None
        self._glass: Optional[Segmented] = None
        self._stroke: Optional[Segmented] = None
        self._filled: Optional[Switch] = None
        self._rotur_layout: Optional[QHBoxLayout] = None
        self._rotur_row = None
        self._discord_layout: Optional[QHBoxLayout] = None
        self._discord_row = None
        self._builds_host: Optional[QWidget] = None
        self._server_row = None
        self._update_row = None
        self._update_button: Optional[McButton] = None
        self._pending_row = None
        self.load()

    def load(self) -> None:
        self.clear()
        settings = self.shell.settings
        user = self.shell.me
        head = PageHead("Settings", "Preferences",
                        user.username if user else "")
        self.add(head, 16)
        self._theme_cards = []
        self._swatches = []

        # appearance -----------------------------------------------------
        panel = Panel("Appearance")
        themes_row = QWidget()
        line = QHBoxLayout(themes_row)
        line.setContentsMargins(16, 14, 16, 12)
        line.setSpacing(8)
        for name in theme.THEME_ORDER:
            card = ThemeCard(name, theme.family_label(name),
                             theme.family_of(settings.theme) == name)
            card.clicked.connect(lambda _=False, n=name: self._pick_theme(n))
            self._theme_cards.append(card)
            line.addWidget(card)
        line.addStretch(1)
        panel.add_widget(themes_row)

        self._mode = Segmented(
            [("auto", "System"), ("light", "Light"), ("dark", "Dark")],
            theme.mode_of(settings.theme),
        )
        self._mode.changed.connect(self._set_mode)
        panel.add_row("Mode", "Top half light, bottom half dark", self._mode)

        accents = QWidget()
        aline = QHBoxLayout(accents)
        aline.setContentsMargins(0, 0, 0, 0)
        aline.setSpacing(8)
        current = QColor(settings.accent).name().lower()
        for color, _label in theme.ACCENTS:
            swatch = Swatch(color, color.lower() == current)
            swatch.clicked.connect(lambda _=False, c=color: self._pick_accent(c))
            self._swatches.append(swatch)
            aline.addWidget(swatch)
        custom = McButton("Custom", small=True, ghost=True)
        custom.clicked.connect(self._pick_custom_accent)
        aline.addWidget(custom)
        aline.addStretch(1)
        panel.add_row("Accent", "Buttons, progress and highlights", accents)
        self._stroke = Segmented(
            [("1", "1x"), ("1.5", "1.5x"), ("2", "2x")],
            f"{settings.iconStroke:g}",
        )
        self._stroke.changed.connect(
            lambda value: self._set(iconStroke=float(value))
        )
        panel.add_row("Icon width", "Lucide outline weight", self._stroke)
        self._filled = Switch(settings.iconFilled)
        self._filled.toggled.connect(lambda value: self._set(iconFilled=value))
        panel.add_row("Filled icons", "Fill circles and squares only", self._filled)
        self._density = Segmented([("comfy", "Comfy"), ("compact", "Compact")],
                                  settings.density)
        self._density.changed.connect(lambda value: self._set(density=value))
        panel.add_row("Density", "Row height in track lists", self._density)
        self._material = Segmented(
            [("plane", "Plane"), ("glass", "Glass"), ("solid", "Solid")],
            settings.material,
        )
        self._material.changed.connect(lambda value: self._set(material=value))
        panel.add_row("Surface", "Background treatment shared with the web player",
                      self._material)
        self._glass = Segmented(
            [("auto", "Auto"), ("on", "On"), ("off", "Off")], settings.real_glass
        )
        self._glass.changed.connect(lambda value: self._set(real_glass=value))
        panel.add_row("Glass effect", "Let the desktop use real translucency", self._glass)
        covers = Switch(settings.covers)
        covers.toggled.connect(lambda value: self._set(covers=value))
        panel.add_row("Cover art", "Show embedded artwork", covers, last=True)
        self.add(panel, 16)

        # playback -------------------------------------------------------
        panel = Panel("Playback")
        options = [
            ("autoplay", "Autoplay", "Continue to the next track automatically", settings.autoplay),
            ("hide_explicit", "Hide explicit tracks", "Skip explicit tracks in queues", settings.hide_explicit),
            ("yt_stats", "YouTube stats", "Show like counts in track lists", settings.yt_stats),
            ("remember_volume", "Remember volume", "Restore the last volume on start", settings.remember_volume),
            ("prefetch", "Prefetch next track", "Cache the next track in the background", settings.prefetch),
            ("offline_audio", "Stream cache", "Keep played audio on disk for offline replay", settings.offline_audio),
        ]
        for index, (key, title, subtitle, value) in enumerate(options):
            toggle = Switch(value)
            toggle.toggled.connect(lambda checked, k=key: self._set(**{k: checked}))
            panel.add_row(title, subtitle, toggle, last=index == len(options) - 1)
        self.add(panel, 16)

        # privacy / activity ----------------------------------------------
        panel = Panel("Privacy & activity")
        options = [
            ("private", "Private listening", "Hide what you play from other listeners", settings.private),
            ("rotur_activity", "RoturLink activity", "Publish your current track to RoturLink", settings.rotur_activity),
            ("discord_activity", "Discord activity", "Show your current track in Discord", settings.discord_activity),
            ("show_room_url", "Show room link", "Expose your listen-along invite link in Settings", settings.show_room_url),
        ]
        for index, (key, title, subtitle, value) in enumerate(options):
            toggle = Switch(value)
            toggle.toggled.connect(lambda checked, k=key: self._set(**{k: checked}))
            panel.add_row(title, subtitle, toggle, last=index == len(options) - 1)
        self.add(panel, 16)

        # account --------------------------------------------------------
        panel = Panel("Account")
        panel.add_row("Username", "Signed in to this server",
                      Txt(user.username if user else "", size=13, token="dim"))

        server_row = QWidget()
        sline = QHBoxLayout(server_row)
        sline.setContentsMargins(0, 0, 0, 0)
        sline.setSpacing(8)
        sline.addWidget(Txt(self.shell.api.base_url, size=11, family="mono",
                            token="dim", wrap=True))
        change = McButton("Change", small=True, ghost=True)
        change.clicked.connect(self._change_server)
        sline.addWidget(change)
        self._server_row = panel.add_row("Server", "Where the library lives", server_row)

        email = McButton("Change", small=True, ghost=True)
        email.clicked.connect(self._change_email)
        panel.add_row("Email", user.email or "No email on this account", email)

        password = McButton("Change password", small=True)
        password.clicked.connect(self._change_password)
        panel.add_row("Password", "Update your local account password", password)

        room_trailing = QWidget()
        rline = QHBoxLayout(room_trailing)
        rline.setContentsMargins(0, 0, 0, 0)
        rline.setSpacing(6)
        copy_room = McButton("Copy", small=True, ghost=True)
        copy_room.clicked.connect(self._copy_room_url)
        open_room = McButton("Open", small=True, ghost=True, icon="arrow-up-right")
        open_room.clicked.connect(self._open_room_url)
        rline.addWidget(copy_room)
        rline.addWidget(open_room)
        self._room_row = panel.add_row(
            "Room link", "Invite others to listen along", room_trailing
        )

        self._rotur_trailing = QWidget()
        self._rotur_layout = QHBoxLayout(self._rotur_trailing)
        self._rotur_layout.setContentsMargins(0, 0, 0, 0)
        self._rotur_layout.setSpacing(8)
        self._rotur_trailing.setMinimumWidth(120)
        self._rotur_row = panel.add_row("RoturLink", "Checking…", self._rotur_trailing)

        self._discord_trailing = QWidget()
        self._discord_layout = QHBoxLayout(self._discord_trailing)
        self._discord_layout.setContentsMargins(0, 0, 0, 0)
        self._discord_layout.setSpacing(8)
        self._discord_trailing.setMinimumWidth(120)
        self._discord_row = panel.add_row("Discord", "Checking…", self._discord_trailing)

        if user and user.is_admin:
            admin = McButton("Open admin", small=True, ghost=True, icon="users")
            admin.clicked.connect(lambda: self.shell.navigate(("admin",)))
            panel.add_row("Admin", "Manage users, requests and scans", admin)
        signout = McButton("Sign out", small=True, danger=True, icon="log-out")
        signout.clicked.connect(self.shell.sign_out)
        panel.add_row("Session", "Sign out of this desktop", signout, last=True)
        self.add(panel, 16)

        # server metadata / builds ---------------------------------------
        panel = Panel("Updates & builds")
        panel.add_row("Client version", VERSION,
                      Txt("Running now", size=11, token="dim2"))
        self._server_version_row = panel.add_row(
            "Server version", "Checking…", Txt("", size=11, family="mono", token="dim")
        )
        update_actions = QWidget()
        update_line = QHBoxLayout(update_actions)
        update_line.setContentsMargins(0, 0, 0, 0)
        update_line.setSpacing(6)
        self._update_button = McButton("Open page", small=True, ghost=True, icon="download")
        self._update_button.setToolTip("Open the public download page in your browser")
        self._update_button.clicked.connect(
            lambda _=False: self.shell.open_update()
        )
        self._update_button.setVisible(False)
        check = McButton("Check", small=True, ghost=True, icon="refresh-cw")
        check.clicked.connect(self._check_for_updates)
        update_line.addWidget(self._update_button)
        update_line.addWidget(check)
        self._update_row = panel.add_row(
            "App update", f"Current version {VERSION}", update_actions
        )
        self._render_update(self.shell._update)

        self._builds_host = QWidget()
        build_line = QVBoxLayout(self._builds_host)
        build_line.setContentsMargins(0, 0, 0, 0)
        build_line.setSpacing(0)
        panel.add_widget(self._builds_host)
        guide = McButton("Self-hosting guide", small=True, ghost=True,
                         icon="arrow-up-right")
        guide.clicked.connect(self._open_selfhost)
        panel.add_row("Run your own", "Docs for hosting a private server", guide,
                      last=True)
        self.add(panel, 16)

        # offline state / cache ------------------------------------------
        panel = Panel("Offline & cache")
        self._pending_label = Txt("0 pending changes", size=11, token="dim")
        sync = McButton("Sync now", small=True, ghost=True, icon="refresh-cw")
        sync.clicked.connect(self.shell.sync_outbox)
        self._pending_row = panel.add_row("Offline writes",
                                         "Queued until the server is reachable", sync)
        self._cache_label = Txt("", size=11, token="dim")
        panel.add_row("Cache", "Saved replies and streamed audio", self._cache_label)
        downloads = McButton("Manage", small=True, ghost=True,
                             icon="arrow-up-right")
        downloads.clicked.connect(lambda: self.shell.navigate(("downloads",)))
        panel.add_row("Downloads", "Inspect, prune or clear cached files", downloads,
                      last=True)
        self.add(panel, 16)

        about = Txt(
            f"mcmusic desktop {VERSION} · native Qt 6 client. Same server API, "
            "palette and icons as the web player and Android app.",
            size=11, token="dim2", wrap=True,
        )
        self.add(about)

        self.refresh_sync_state()
        self.run(self.shell.repo.rotur_status, self._render_rotur,
                 error=lambda _e: self._render_rotur({}))
        self.run(self.shell.repo.discord_status, self._render_discord,
                 error=lambda _e: self._render_discord({}))
        self.run(self.shell.repo.version, self._render_version,
                 error=lambda _e: None)
        self.run(self.shell.repo.builds, self._render_builds,
                 error=lambda _e: None)

    # helpers ------------------------------------------------------------
    def _set(self, **changes) -> None:
        self.shell.apply_settings(replace(self.shell.settings, **changes))

    def _pick_theme(self, name: str) -> None:
        family = theme.family_of(name)
        mode = theme.mode_of(self.shell.settings.theme)
        self.shell.apply_settings(
            replace(self.shell.settings, theme=theme.with_mode(family, mode))
        )

    def _set_mode(self, mode: str) -> None:
        self.shell.apply_settings(
            replace(self.shell.settings,
                    theme=theme.with_mode(self.shell.settings.theme, mode))
        )

    def _pick_accent(self, color: str) -> None:
        self.shell.apply_settings(replace(self.shell.settings, accent=color))

    def _pick_custom_accent(self) -> None:
        initial = QColor(self.shell.settings.accent)
        chosen = QColorDialog.getColor(initial, self, "Accent colour")
        if chosen.isValid():
            self._pick_accent(chosen.name())

    def _change_server(self) -> None:
        url = prompt(self, "Change server", "Server URL",
                     initial=self.shell.api.base_url, placeholder="http://host:8000",
                     confirm="Connect")
        if url:
            self.shell.change_server(url)

    def _change_password(self) -> None:
        from .widgets import Sheet

        sheet = Sheet(self, "Change password")
        old = LabeledField("Current password", "••••••••", password=True)
        new = LabeledField("New password", "at least 6 characters", password=True)
        sheet.body.addWidget(old)
        sheet.body.addWidget(new)
        error = Txt("", size=11, token="err", wrap=True)
        error.setVisible(False)
        sheet.body.addWidget(error)

        row = QHBoxLayout()
        row.addStretch(1)
        cancel = McButton("Cancel", ghost=True)
        cancel.clicked.connect(sheet.reject)
        row.addWidget(cancel)
        save = McButton("Save", solid=True)
        row.addWidget(save)
        sheet.body.addLayout(row)

        def submit() -> None:
            if len(new.text()) < 6:
                error.setText("New password must be 6+ characters")
                error.setVisible(True)
                return
            save.setEnabled(False)

            def job():
                self.shell.repo.change_password(old.text(), new.text())

            def ok(_):
                sheet.accept()
                self.shell.toast("Password changed")

            def fail(exc: Exception) -> None:
                save.setEnabled(True)
                error.setText(str(exc))
                error.setVisible(True)

            self.shell.run(job, ok, fail)

        save.clicked.connect(submit)
        new.line_edit.returnPressed.connect(submit)
        old.line_edit.setFocus()
        sheet.exec()

    def _change_email(self) -> None:
        current = self.shell.me.email if self.shell.me else ""
        email = prompt(self, "Account email", "Email address", initial=current or "",
                       placeholder="you@example.com", confirm="Save")
        if not email:
            return
        self.run(lambda: self.shell.repo.set_email(email),
                 lambda me: (self.shell.after_login(me), self.load(),
                             self.shell.toast("Email updated")))

    def _room_url(self) -> str:
        base = self.shell.settings.room_url or self.shell.store.room_url
        if not base:
            return ""
        user = self.shell.me
        code = (user.rotur_user_id or user.rotur_id if user else "") or ""
        return base.rstrip("/") + ("#room=" + code[:8] if code else "")

    def _copy_room_url(self) -> None:
        url = self._room_url()
        if not url:
            self.shell.toast("No room link is available yet")
            return
        QGuiApplication.clipboard().setText(url)
        self.shell.toast("Room link copied")

    def _open_room_url(self) -> None:
        url = self._room_url()
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def _render_rotur(self, status: dict) -> None:
        while self._rotur_layout.count():
            item = self._rotur_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not isinstance(status, dict):
            status = {}
        configured = bool(status.get("configured"))
        linked = bool(status.get("linked"))
        if not configured:
            self._rotur_trailing.setVisible(False)
            if self._rotur_row.subtitle_label is not None:
                self._rotur_row.subtitle_label.setText(
                    "RoturLink is not configured on this server"
                )
            return
        self._rotur_trailing.setVisible(True)
        if self._rotur_row.subtitle_label is not None:
            self._rotur_row.subtitle_label.setText(
                f"Linked as {status.get('rotur_id')}" if linked else
                "Not linked — sign in through RoturLink"
            )
        if linked:
            unlink = McButton("Unlink", small=True, ghost=True, danger=True)
            unlink.clicked.connect(self._unlink)
            self._rotur_layout.addWidget(unlink)
        else:
            open_link = McButton("Open", small=True, ghost=True, icon="link")
            open_link.clicked.connect(self._open_rotur)
            self._rotur_layout.addWidget(open_link)

    def _unlink(self) -> None:
        self.run(self.shell.repo.unlink_rotur, lambda _: self.load())

    def _open_rotur(self) -> None:
        QDesktopServices.openUrl(QUrl(self.shell.repo.rotur_authorize_url(
            self.shell.store.device_hash
        )))

    def _render_discord(self, status: dict) -> None:
        while self._discord_layout.count():
            item = self._discord_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not isinstance(status, dict):
            status = {}
        configured = bool(status.get("configured"))
        linked = bool(status.get("linked"))
        if not configured:
            self._discord_trailing.setVisible(False)
            if self._discord_row.subtitle_label is not None:
                self._discord_row.subtitle_label.setText(
                    "Discord linking is not configured on this server"
                )
            return
        self._discord_trailing.setVisible(True)
        if self._discord_row.subtitle_label is not None:
            self._discord_row.subtitle_label.setText(
                f"Linked as {status.get('username') or status.get('discord_id')}"
                if linked else "Not linked — connect a Discord account"
            )
        if linked:
            unlink = McButton("Unlink", small=True, ghost=True, danger=True)
            unlink.clicked.connect(self._unlink_discord)
            self._discord_layout.addWidget(unlink)
        else:
            link = McButton("Connect", small=True, ghost=True, icon="link")
            link.clicked.connect(self._open_discord)
            self._discord_layout.addWidget(link)

    def _unlink_discord(self) -> None:
        self.run(self.shell.repo.discord_unlink, lambda _: self.load())

    def _open_discord(self) -> None:
        QDesktopServices.openUrl(QUrl(self.shell.repo.discord_authorize_url()))

    def _check_for_updates(self) -> None:
        def render(build: Optional[BuildInfo]) -> None:
            self._render_update(build)
            if build is None and self.shell._update is None:
                self.shell.toast("No update is available for this platform")

        if self._update_button is not None:
            self._update_button.setVisible(False)
        self.shell._check_updates(render)

    def _render_update(self, build: Optional[BuildInfo]) -> None:
        if self._update_row is None or not isValid(self._update_row):
            return
        if build and build.available and build.version:
            subtitle = f"{build.version} available — open the download page"
        else:
            subtitle = f"Up to date ({VERSION})"
        if self._update_row.subtitle_label is not None:
            self._update_row.subtitle_label.setText(subtitle)
        if self._update_button is not None:
            self._update_button.setVisible(bool(build and build.available))

    def _render_version(self, data: dict) -> None:
        if not self._server_row or not isinstance(data, dict):
            return
        build = str(data.get("build") or "")[:12]
        label = f"build {build}" if build else "reachable"
        if self._server_version_row.subtitle_label is not None:
            self._server_version_row.subtitle_label.setText(label)
        trailing = self._server_version_row.layout().itemAt(1)
        if trailing is not None and trailing.widget() is not None:
            trailing.widget().setText(str(data.get("shell") or VERSION))

    def _render_builds(self, builds: list[BuildInfo]) -> None:
        host = self._builds_host
        if host is None or not isValid(host):
            return
        layout = host.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        shown = [b for b in builds if b.available][:12]
        if not shown:
            layout.addWidget(Txt("No builds are published yet.", size=11,
                                 token="dim2", wrap=True))
            return
        panel = Panel("Available builds")
        for index, build in enumerate(shown):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(6)
            download = McButton("Download", small=True, ghost=True, icon="download")
            download.clicked.connect(lambda _=False, b=build: QDesktopServices.openUrl(
                QUrl(self.shell.repo.build_url(b.url))))
            email = McButton("Email", small=True, ghost=True)
            email.clicked.connect(lambda _=False, b=build: self._email_build(b))
            line.addWidget(download)
            line.addWidget(email)
            subtitle = " · ".join(x for x in [build.version, fmt_bytes(build.bytes),
                                              build.built] if x)
            panel.add_row(build.label, subtitle or build.note, trailing,
                          last=index == len(shown) - 1)
        layout.addWidget(panel)

    def _email_build(self, build: BuildInfo) -> None:
        email = prompt(self, "Email build", "Email address",
                       placeholder="you@example.com", confirm="Send")
        if not email:
            return
        self.run(lambda: self.shell.repo.email_build(build.kind, email),
                 lambda _: self.shell.toast(f"{build.label} link sent"))

    def _open_selfhost(self) -> None:
        QDesktopServices.openUrl(QUrl(
            "https://github.com/mc20000-01/mcmusic/blob/main/docs/selfhost.md"
        ))

    def refresh_sync_state(self) -> None:
        pending = self.shell.api.pending_writes()
        if self._pending_label is not None and isValid(self._pending_label):
            self._pending_label.setText(
                f"{pending} pending change" + ("" if pending == 1 else "s")
            )
        if self._cache_label is not None and isValid(self._cache_label):
            responses, audio = self.shell.store.cache_stats()
            self._cache_label.setText(f"{responses} replies · {audio} audio files")

    def apply_settings(self, settings: Settings) -> None:
        for card in self._theme_cards:
            card.set_selected(theme.family_of(settings.theme) == card.name)
        if self._mode is not None:
            self._mode.set_selected(theme.mode_of(settings.theme))
        current = QColor(settings.accent).name().lower()
        for swatch in self._swatches:
            swatch.set_selected(swatch.color.lower() == current)
        if self._density is not None:
            self._density.set_selected(settings.density)
        if self._material is not None:
            self._material.set_selected(settings.material)
        if self._glass is not None:
            self._glass.set_selected(settings.real_glass)
        if self._stroke is not None:
            self._stroke.set_selected(f"{settings.iconStroke:g}")
        if self._filled is not None:
            self._filled.setChecked(settings.iconFilled)
        if self._room_row is not None:
            self._room_row.setVisible(bool(settings.show_room_url and self._room_url()))
        self.refresh_sync_state()


# ── admin ──────────────────────────────────────────────────────────────────


class AdminScreen(Screen):
    """Sectioned server console matching the web/Android admin tools."""

    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    @staticmethod
    def _clear(widget: QWidget) -> None:
        layout = widget.layout()
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.setParent(None)
                child.deleteLater()

    @staticmethod
    def _host(title: str) -> tuple[QWidget, QVBoxLayout, QWidget]:
        """A permanent panel wrapper with a replaceable body layout."""
        host = QWidget()
        outer = QVBoxLayout(host)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        panel = Panel(title)
        outer.addWidget(panel)
        body = QWidget()
        line = QVBoxLayout(body)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(0)
        panel.add_widget(body)
        return host, line, body

    def load(self) -> None:
        self.clear()
        head = PageHead("Admin", "Server console", "")
        refresh = McButton("Refresh", small=True, ghost=True, icon="refresh-cw")
        refresh.clicked.connect(self.load)
        head.add_action(refresh)
        scan = McButton("Rescan library", small=True, ghost=True)
        scan.clicked.connect(self._rescan)
        head.add_action(scan)
        self.add(head, 16)
        self.loading("Reading server stats…")

        self._stats_host = QWidget()
        self.add(self._stats_host, 16)
        self._users_host, self._users_line, self._users_body = self._host("Users")
        self.add(self._users_host, 16)
        self._invites_host, self._invites_line, self._invites_body = self._host(
            "Invite codes"
        )
        invite = McButton("New code", small=True, ghost=True, icon="plus")
        invite.clicked.connect(self._create_invite)
        head.add_action(invite)
        self.add(self._invites_host, 16)
        self._requests_host, self._requests_line, self._requests_body = self._host(
            "Download requests"
        )
        self.add(self._requests_host, 16)
        self._devices_host, self._devices_line, self._devices_body = self._host(
            "Connected devices"
        )
        self.add(self._devices_host, 16)
        self._channels_host, self._channels_line, self._channels_body = self._host(
            "Control channels"
        )
        self.add(self._channels_host, 16)
        self._rooms_host, self._rooms_line, self._rooms_body = self._host(
            "Listening rooms"
        )
        self.add(self._rooms_host, 16)
        self._jobs_host, self._jobs_line, self._jobs_body = self._host("Library jobs")
        self.add(self._jobs_host, 16)

        self.run(self.shell.repo.admin_stats, self._render_stats)
        self.run(self.shell.repo.admin_users, self._render_users)
        self.run(self.shell.repo.admin_invites, self._render_invites)
        self.run(self.shell.repo.admin_requests, self._render_requests)
        self.run(self.shell.repo.admin_devices, self._render_devices)
        self.run(self.shell.repo.admin_channels, self._render_channels)
        self.run(self.shell.repo.admin_rooms, self._render_rooms)
        self.run(self.shell.repo.admin_enrich_status, self._render_enrich)
        self.run(self.shell.repo.admin_lyrics_status, self._render_lyrics)

    def _done(self) -> None:
        self.stop_loading()

    def _render_stats(self, stats: AdminStats) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._stats_host)
        grid = QGridLayout(self._stats_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        cards = [
            (str(stats.users), "users"), (str(stats.admins), "admins"),
            (str(stats.tracks), "tracks"), (str(stats.albums), "albums"),
            (str(stats.playlists), "playlists"), (str(stats.plays), "plays"),
            (str(stats.queue), "queue"), (str(stats.rooms), "rooms"),
            (fmt_bytes(stats.music_bytes), "music"),
            (fmt_bytes(stats.disk_free), "disk free"),
            (fmt_uptime(stats.uptime), "uptime"),
        ]
        columns = max(2, min(6, self.width() // 190))
        for i, (value, label) in enumerate(cards):
            grid.addWidget(StatCard(value, label), i // columns, i % columns)

    def _render_users(self, users: list[AdminUser]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._users_body)
        for i, user in enumerate(users):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(8)
            if user.is_admin:
                line.addWidget(StatusChip("admin", "accent"))
            button = McButton("Revoke" if user.is_admin else "Make admin",
                              small=True, ghost=True, danger=user.is_admin)
            button.clicked.connect(lambda _=False, u=user: self._toggle_admin(u))
            delete = IconButton("trash-2", size=26, icon_size=13,
                                tooltip="Delete user")
            delete.clicked.connect(lambda _=False, u=user: self._delete_user(u))
            line.addWidget(button)
            line.addWidget(delete)
            subtitle = (f"{user.plays} plays · {user.likes} likes · "
                        f"{user.playlists} playlists · {user.requests} requests")
            self._users_line.addWidget(self._row_widget(
                user.username, subtitle, trailing, i == len(users) - 1))
        if not users:
            self._users_line.addWidget(self._row_widget(
                "No users", "Nobody has signed in yet", None, True))

    @staticmethod
    def _row_widget(title: str, subtitle: str, trailing: Optional[QWidget],
                    last: bool) -> QWidget:
        host = QWidget()
        line = QHBoxLayout(host)
        line.setContentsMargins(16, 12, 16, 12)
        line.setSpacing(16)
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.addWidget(Txt(title, size=13, token="fg"))
        if subtitle:
            text.addWidget(Txt(subtitle, size=11, token="dim2", wrap=True))
        line.addLayout(text, 1)
        if trailing is not None:
            line.addWidget(trailing, 0, Qt.AlignmentFlag.AlignVCenter)
        if not last:
            host.setProperty("mcRow", True)
        return host

    def _toggle_admin(self, user: AdminUser) -> None:
        self.run(
            lambda: self.shell.repo.admin_set_admin(user.id, not user.is_admin),
            lambda _: (self.shell.toast(
                "Admin removed" if user.is_admin else "Admin granted"), self.load()),
        )

    def _delete_user(self, user: AdminUser) -> None:
        if not confirm(self, "Delete user",
                       f"Permanently delete @{user.username} and their library?",
                       confirm_label="Delete"):
            return
        self.run(lambda: self.shell.repo.admin_delete_user(user.id),
                 lambda _: (self.shell.toast("User deleted"), self.load()))

    def _rescan(self) -> None:
        self.run(
            self.shell.repo.admin_scan,
            lambda result: self.shell.toast(f"{result[0]} tracks · {result[1]} albums"),
        )

    def _create_invite(self) -> None:
        note = prompt(self, "New invite code", "Note (optional)",
                      placeholder="For a friend", confirm="Create")
        if note is None:
            return
        self.run(lambda: self.shell.repo.admin_invite_create(1, 0, note),
                 lambda data: (QGuiApplication.clipboard().setText(str(data.get("code", ""))),
                               self.shell.toast("Invite code copied"), self.load()))

    def _render_invites(self, codes: list[dict]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._invites_body)
        for i, code in enumerate(codes[:50]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            copy = McButton("Copy", small=True, ghost=True)
            copy.clicked.connect(lambda _=False, c=code: QGuiApplication.clipboard().setText(
                str(c.get("code", ""))))
            revoke = IconButton("x", size=26, icon_size=12, tooltip="Revoke code")
            revoke.setEnabled(not code.get("expired") and not code.get("exhausted"))
            revoke.clicked.connect(lambda _=False, c=code: self.run(
                lambda: self.shell.repo.admin_invite_revoke(int(c.get("id") or 0)),
                lambda _: self.load()))
            line.addWidget(copy)
            line.addWidget(revoke)
            state = "expired" if code.get("expired") else (
                "used up" if code.get("exhausted") else "active")
            subtitle = (f"{code.get('uses', 0)}/{code.get('max_uses', 0)} uses · "
                        f"{code.get('note') or state}")
            self._invites_line.addWidget(self._row_widget(
                str(code.get("code", "")), subtitle, trailing, i == min(len(codes), 50) - 1))
        if not codes:
            self._invites_line.addWidget(self._row_widget(
                "No invite codes", "Create one to invite a friend", None, True))

    def _render_requests(self, rows: list[RequestRow]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._requests_body)
        open_requests = McButton("Open queue", small=True, ghost=True,
                                 icon="arrow-up-right")
        open_requests.clicked.connect(lambda: self.shell.navigate(("requests",)))
        self._requests_line.addWidget(self._row_widget(
            f"{len(rows)} requests", "Approve, cancel, retry and read logs",
            open_requests, True))

    def _render_devices(self, devices: list[DeviceRow]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._devices_body)
        open_devices = McButton("Open devices", small=True, ghost=True,
                                icon="arrow-up-right")
        open_devices.clicked.connect(lambda: self.shell.navigate(("devices",)))
        self._devices_line.addWidget(self._row_widget(
            f"{len(devices)} devices", "Rename, activate and revoke app passwords",
            open_devices, True))

    def _render_channels(self, channels: list[dict]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._channels_body)
        for i, channel in enumerate(channels[:50]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            unbind = McButton("Unbind", small=True, ghost=True, danger=True)
            unbind.clicked.connect(lambda _=False, c=channel: self.run(
                lambda: self.shell.api.delete(f"channels/{int(c.get('id') or 0)}"),
                lambda _: self.load()))
            line.addWidget(unbind)
            subtitle = (f"{channel.get('platform', 'chat')} · "
                        f"{channel.get('channel_id', '')}")
            self._channels_line.addWidget(self._row_widget(
                str(channel.get("name") or channel.get("id") or "channel"),
                subtitle, trailing, i == min(len(channels), 50) - 1))
        if not channels:
            self._channels_line.addWidget(self._row_widget(
                "No control channels", "Bot channels appear here when bound", None, True))

    def _render_rooms(self, rooms: list[dict]) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._rooms_body)
        for i, room in enumerate(rooms[:40]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            close = McButton("Close", small=True, ghost=True, danger=True)
            close.clicked.connect(lambda _=False, r=room: self.run(
                lambda: self.shell.repo.admin_room_close(str(r.get("code", ""))),
                lambda _: self.load()))
            line.addWidget(close)
            track = room.get("track") or {}
            subtitle = (f"@{room.get('host', '?')} · "
                        f"{(track.get('title') if isinstance(track, dict) else '') or 'idle'}")
            self._rooms_line.addWidget(self._row_widget(
                str(room.get("code", "")), subtitle, trailing,
                i == min(len(rooms), 40) - 1))
        if not rooms:
            self._rooms_line.addWidget(self._row_widget(
                "No open rooms", "Listen-along rooms appear here", None, True))

    def _render_enrich(self, status: dict) -> None:
        if not isValid(self):
            return
        self._done()
        self._clear(self._jobs_body)
        status = status if isinstance(status, dict) else {}
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(16, 12, 16, 12)
        line.setSpacing(8)
        line.addWidget(Txt(
            f"YouTube metadata: {status.get('linked', 0)}/{status.get('total', 0)} linked · "
            f"{status.get('fetched', 0)} fetched", size=11, token="dim", wrap=True), 1)
        start = McButton("Refresh stats", small=True, ghost=True)
        start.clicked.connect(lambda: self.run(self.shell.repo.admin_enrich_start,
                                               lambda _: self.load()))
        force = McButton("Re-fetch all", small=True, ghost=True, danger=True)
        force.clicked.connect(lambda: self.run(
            lambda: self.shell.repo.admin_enrich_start(force=True),
            lambda _: (self.shell.toast("Metadata refresh queued"), self.load())))
        lyric = McButton("Fetch lyrics", small=True, ghost=True)
        lyric.clicked.connect(lambda: self.run(self.shell.repo.admin_lyrics_start,
                                               lambda _: (self.shell.toast(
                                                   "Lyrics fetch queued"), self.load())))
        for button in (start, force, lyric):
            line.addWidget(button)
        self._jobs_line.addWidget(row)

    def _render_lyrics(self, status: dict) -> None:
        if not isValid(self):
            return
        status = status if isinstance(status, dict) else {}
        row = QWidget()
        line = QHBoxLayout(row)
        line.setContentsMargins(16, 4, 16, 12)
        line.addWidget(Txt("Lyrics: " + ", ".join(
            f"{k}={v}" for k, v in list(status.items())[:4]
        ) or "no status", size=11, token="dim2", wrap=True))
        self._jobs_line.addWidget(row)


# ── downloads / cache ────────────────────────────────────────────────────────


class DownloadsScreen(Screen):
    """The local audio cache: files, bytes, pruning and removal."""

    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        from .player import cache_dir
        self._dir = cache_dir()
        head = PageHead("Downloads", "Server imports and local audio", "")
        seg = Segmented([("requests", "Requests"), ("device", "Your downloads")],
                        getattr(self, "tab", "device"))
        seg.changed.connect(self._switch)
        head.add_action(seg)
        refresh = McButton("Refresh", small=True, ghost=True, icon="refresh-cw")
        refresh.clicked.connect(self.load)
        head.add_action(refresh)
        self.add(head, 12)
        self.tab = getattr(self, "tab", "device")
        if self.tab == "requests":
            panel = Panel("Requests")
            open_requests = McButton("Open requests", small=True, ghost=True,
                                     icon="arrow-up-right")
            open_requests.clicked.connect(lambda: self.shell.navigate(("requests",)))
            panel.add_row(
                "Server imports", "YouTube and direct links are approved on the server",
                open_requests, last=True,
            )
            self.add(panel, 16)
            self.add(Txt("Approved imports appear in the library; saved tracks show up under "
                         "“Your downloads” on this device.", size=11, token="dim2", wrap=True))
            return

        from datetime import datetime
        files = []
        for p in sorted(self._dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True):
            if not p.is_file() or p.suffix == ".part":
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            files.append((p, st))
        total = sum(st.st_size for _, st in files)
        responses, _ = self.shell.store.cache_stats()

        panel = Panel("Storage")
        panel.add_row("Audio files", f"{len(files)} files · {fmt_bytes(total)}",
                      Txt("on this device", size=11, token="dim2"))
        panel.add_row("API responses", f"{responses} cached replies",
                      Txt("offline reads", size=11, token="dim2"))
        actions = QWidget()
        line = QHBoxLayout(actions)
        line.setContentsMargins(0, 0, 0, 0)
        line.setSpacing(6)
        prune = McButton("Prune old", small=True, ghost=True)
        prune.clicked.connect(self._prune)
        line.addWidget(prune)
        clear = McButton("Clear cache", small=True, danger=True, icon="trash-2")
        clear.clicked.connect(self._clear)
        line.addWidget(clear)
        folder = McButton("Open folder", small=True, ghost=True, icon="arrow-up-right")
        folder.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self._dir))))
        line.addWidget(folder)
        panel.add_row("Maintenance", "Old files and oversized caches can be removed", actions,
                      last=True)
        self.add(panel, 16)

        panel = Panel("Cached tracks")
        if not files:
            panel.add_row("Nothing cached yet", "Tracks you play are kept here",
                          last=True)
        for index, (path, st) in enumerate(files[:200]):
            trailing = QWidget()
            row_line = QHBoxLayout(trailing)
            row_line.setContentsMargins(0, 0, 0, 0)
            row_line.setSpacing(6)
            row_line.addWidget(Txt(fmt_bytes(st.st_size), size=11, family="mono", token="dim"))
            play = McButton("Play", small=True, ghost=True, icon="play")
            play.clicked.connect(lambda _=False, p=path: self._play_cached(p))
            row_line.addWidget(play)
            remove = IconButton("trash-2", size=26, icon_size=13, tooltip="Remove file")
            remove.clicked.connect(lambda _=False, p=path: self._remove(p))
            row_line.addWidget(remove)
            when = datetime.fromtimestamp(st.st_mtime).strftime("%d %b %Y")
            panel.add_row(path.stem, fmt_bytes(st.st_size) + " · " + when,
                          trailing, last=index == min(len(files), 200) - 1)
        self.add(panel, 16)
        self.add(Txt("Downloads are the same stream cache the player uses. Turning off "
                     "“Stream cache” in Settings discards files after playback.",
                     size=11, token="dim2", wrap=True))

    def _switch(self, tab: str) -> None:
        self.tab = tab
        self.load()

    def _play_cached(self, path) -> None:
        # Reuse the normal engine so MPRIS, activity and queue state stay in sync.
        try:
            track_id = int(path.stem.split(".")[0])
        except ValueError:
            return
        if track_id in (t.id for t in self.shell.player.queue):
            self.shell.player.jump(next(i for i, t in enumerate(self.shell.player.queue)
                                         if t.id == track_id))
            return
        self.run(
            lambda: self.shell.repo.find_track(track_id),
            lambda track: (
                self.shell.player.play([track], 0) if track is not None
                else self.shell.toast("Track details are not cached — open it from your library")
            ),
            lambda _exc: self.shell.toast("Track details are not cached — open it from your library"),
        )

    def _remove(self, path) -> None:
        try:
            path.unlink()
            self.shell.toast("Cache file removed")
        except OSError as exc:
            self.shell.toast(str(exc))
        self.load()

    def _prune(self) -> None:
        removed = self.shell.store.cache_prune()
        self.shell.toast(f"Pruned {removed} files")
        self.load()

    def _clear(self) -> None:
        if not confirm(self, "Clear cache",
                       "Remove cached audio and offline API replies? You will need a "
                       "connection to play those tracks again.", confirm_label="Clear"):
            return
        removed = self.shell.store.cache_clear()
        self.shell.toast(f"Cleared {removed} cached items")
        self.load()


# ── devices ──────────────────────────────────────────────────────────────────


class DevicesScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        head = PageHead("Devices", "Your signed-in players", "")
        refresh = McButton("Refresh", small=True, ghost=True, icon="refresh-cw")
        refresh.clicked.connect(self.load)
        head.add_action(refresh)
        pair = McButton("Pair device", small=True, icon="link")
        pair.clicked.connect(self._pair)
        head.add_action(pair)
        self.add(head, 12)
        self.loading("Reading devices…")
        self.run(self.shell.repo.devices, self._render_devices,
                 error=lambda _e: self.stop_loading())
        self.run(self.shell.repo.device_tokens, self._render_tokens,
                 error=lambda _e: None)

    def _render_devices(self, devices: list[DeviceRow]) -> None:
        self.stop_loading()
        panel = Panel("Registered devices")
        for index, device in enumerate(devices):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(6)
            if device.active:
                line.addWidget(StatusChip("active", "accent"))
            if not device.active:
                activate = McButton("Activate", small=True, ghost=True)
                activate.clicked.connect(lambda _=False, d=device: self._act(
                    lambda: self.shell.repo.device_activate(d.id), "Device activated"))
                line.addWidget(activate)
            rename = McButton("Rename", small=True, ghost=True)
            rename.clicked.connect(lambda _=False, d=device: self._rename(d))
            line.addWidget(rename)
            forget = IconButton("trash-2", size=26, icon_size=13, tooltip="Forget device")
            forget.clicked.connect(lambda _=False, d=device: self._forget(d))
            line.addWidget(forget)
            subtitle = (device.track_title or "No track") + (
                " — " + device.track_artist if device.track_artist else "")
            panel.add_row(device.name or device.device_hash[:12], subtitle, trailing,
                          last=index == len(devices) - 1)
        if not devices:
            panel.add_row("No devices yet", "Play something to register this app", last=True)
        self.add(panel, 16)

        panel = Panel("Maintenance")
        cleanup = McButton("Remove stale devices", small=True, ghost=True)
        cleanup.clicked.connect(lambda: self._act(
            self.shell.repo.devices_cleanup, "Stale devices removed"))
        panel.add_row("Cleanup", "Drop devices unseen for 30 days", cleanup)
        clear = McButton("Forget all devices", small=True, danger=True)
        clear.clicked.connect(self._clear_all)
        panel.add_row("Reset", "Remove every device for this account", clear, last=True)
        self.add(panel, 16)
        self.reset_scroll()

    def _render_tokens(self, tokens: list[dict]) -> None:
        panel = Panel("App passwords")
        for index, token in enumerate(tokens[:50]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            revoke = McButton("Revoke", small=True, danger=True)
            token_id = token.get("id", token.get("device_id", 0))
            revoke.clicked.connect(lambda _=False, tid=token_id: self._act(
                lambda: self.shell.repo.device_token_revoke(int(tid)), "Token revoked"))
            line.addWidget(revoke)
            label = str(token.get("name") or token.get("prefix") or token.get("id") or "token")
            panel.add_row(label, "Long-lived native client credential", trailing,
                          last=index == min(len(tokens), 50) - 1)
        if not tokens:
            panel.add_row("No app passwords", "Pair a device to create one", last=True)
        self.add(panel, 16)

    def _act(self, fn, success: str) -> None:
        self.run(fn, lambda _: (self.shell.toast(success), self.load()))

    def _rename(self, device: DeviceRow) -> None:
        name = prompt(self, "Rename device", "Name", initial=device.name,
                      placeholder="Living room speaker", confirm="Rename")
        if name:
            self._act(lambda: self.shell.repo.device_rename(device.id, name),
                      "Device renamed")

    def _forget(self, device: DeviceRow) -> None:
        if confirm(self, "Forget device", f"Remove {device.name or 'this device'}?",
                   confirm_label="Forget"):
            self._act(lambda: self.shell.repo.device_forget(device.id), "Device forgotten")

    def _clear_all(self) -> None:
        if confirm(self, "Forget all devices", "Every device for this account will be "
                   "signed out. This app will re-register on its next heartbeat.",
                   confirm_label="Forget all"):
            self._act(self.shell.repo.devices_clear, "Devices cleared")

    def _pair(self) -> None:
        sheet = Sheet(self, "Pair a device")
        code_label = Txt("Asking the server for a code…", size=13, token="dim", wrap=True)
        sheet.body.addWidget(code_label)
        hint = Txt("", size=11, token="dim2", wrap=True)
        sheet.body.addWidget(hint)

        def ok(data: dict) -> None:
            if not isinstance(data, dict):
                return
            code = str(data.get("code") or "")
            code_label.setText(code or "No code returned")
            hint.setText(str(data.get("hint") or ""))

        self.run(self.shell.repo.device_code, ok,
                 error=lambda e: code_label.setText(str(e)))

        enter = McButton("I have a code", small=True)
        sheet.body.addWidget(enter, 0, Qt.AlignmentFlag.AlignLeft)

        def claim() -> None:
            value = prompt(self, "Pair device", "One-time code", placeholder="XXXX-XXXX",
                           confirm="Sign in")
            if not value:
                return
            enter.setEnabled(False)

            def done(data: dict) -> None:
                token = str(data.get("token") or "")
                if not token:
                    self.shell.toast("That code could not be used")
                    enter.setEnabled(True)
                    return
                self.shell.api.set_token(token)
                me = self.shell.repo.me()
                sheet.accept()
                self.shell.after_login(me)
                self.shell.toast("Device paired")

            self.run(lambda: self.shell.repo.device_claim(value, "mcmusic desktop"),
                     done, error=lambda _e: enter.setEnabled(True))

        enter.clicked.connect(claim)
        sheet.exec()


# ── public listening ─────────────────────────────────────────────────────────


class ListeningScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

    def load(self) -> None:
        self.clear()
        head = PageHead("Listening", "What your server is playing", "")
        refresh = McButton("Refresh", small=True, ghost=True, icon="refresh-cw")
        refresh.clicked.connect(self.load)
        head.add_action(refresh)
        self.add(head, 12)
        self.loading("Checking who is online…")
        self.run(self.shell.repo.public_listening,
                 lambda value: self._render(value[0], value[1]),
                 error=lambda _e: self.stop_loading())

    def _render(self, users: list[ListeningUser], base: str) -> None:
        self.stop_loading()
        panel = Panel("Recently active")
        for index, user in enumerate(users[:60]):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            line.addWidget(StatusChip("listening" if user.listening else "paused",
                                      "accent" if user.listening else "dim"))
            profile = McButton("Profile", small=True, ghost=True, icon="arrow-up-right")
            profile.clicked.connect(lambda _=False, u=user: self._profile(u.username))
            line.addWidget(profile)
            if user.track:
                sub = f"{user.track.title} · {user.track.artist}"
                if user.listening and user.track.duration:
                    sub += f" · {fmt_time(user.position)}/{fmt_time(user.track.duration)}"
            else:
                sub = "Nothing playing"
            panel.add_row(user.username, sub, trailing, last=index == min(len(users), 60) - 1)
        if not users:
            panel.add_row("Nobody listening right now",
                          "Devices appear here while they are active", last=True)
        self.add(panel, 16)
        if base:
            self.add(Txt("Public profiles: " + base + "/u/username",
                         size=11, family="mono", token="dim2", wrap=True))
        self.reset_scroll()

    def _profile(self, username: str) -> None:
        sheet = Sheet(self, "Profile")
        label = Txt("Loading " + username + "…", size=13, token="dim", wrap=True)
        sheet.body.addWidget(label)
        open_web = McButton("Open profile", small=True, ghost=True, icon="arrow-up-right")
        open_web.setEnabled(False)
        sheet.body.addWidget(open_web, 0, Qt.AlignmentFlag.AlignLeft)

        def ok(data: dict) -> None:
            if not isinstance(data, dict):
                return
            track = data.get("track") or {}
            if isinstance(track, dict):
                label.setText(
                    f"{data.get('username', username)}\n"
                    f"{track.get('title', '')} — {track.get('artist', '')}\n"
                    f"{fmt_time(float(data.get('position') or 0))}"
                )
            else:
                label.setText(str(data.get("username") or username))
            url = str(data.get("profile_url") or "")
            if url:
                open_web.setEnabled(True)
                open_web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

        self.run(lambda: self.shell.repo.public_now(username), ok,
                 error=lambda e: label.setText(str(e)))
        sheet.exec()

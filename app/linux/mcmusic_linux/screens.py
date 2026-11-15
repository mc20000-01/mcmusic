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
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QColorDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .models import (
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
    Artwork,
    EmptyState,
    Glyph,
    Hero,
    IconButton,
    LabeledField,
    McButton,
    PageHead,
    Panel,
    Segmented,
    SettingRow,
    Shelf,
    Spinner,
    StatCard,
    StatusChip,
    Switch,
    TileGrid,
    Txt,
    confirm,
    message,
    prompt,
)

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
        self.window = window
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
        self.layout = QVBoxLayout(self.body)
        self.layout.setContentsMargins(26, 22, 26, 40)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        row.addWidget(self.body, 100)
        row.addStretch(1)
        outer.addLayout(row)
        self.setWidget(host)

    # layout helpers -----------------------------------------------------
    def add(self, widget: QWidget, spacing: int = 0) -> QWidget:
        self.layout.addWidget(widget)
        if spacing:
            self.layout.addSpacing(spacing)
        return widget

    def space(self, height: int) -> None:
        self.layout.addSpacing(height)

    def clear(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
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
            self.window.toast(str(exc) or "Something went wrong")
            if error:
                error(exc)

        self.window.run(fn, safe_ok, safe_error)

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
        self.layout.removeWidget(self._loading_row)
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
        self.run(self.window.repo.home, self._render)

    def _render(self, home: HomeData) -> None:
        self.clear()
        hour = time.localtime().tm_hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
        head = PageHead("Home", greeting, f"{len(home.sections)} shelves")
        self.add(head, 16)

        if home.albums:
            shelf = Shelf("Fresh pressings", f"{len(home.albums)} albums")
            shelf.set_items(_album_items(home.albums))
            shelf.opened.connect(lambda a: self.window.navigate(("album", a.album)))
            shelf.played.connect(lambda a: self.window.play_album(a.album))
            browse = McButton("All albums", small=True, ghost=True)
            browse.clicked.connect(lambda: self.window.navigate(("library", "albums")))
            shelf.add_action(browse)
            self.add(shelf, 10)

        for section in home.sections:
            if not section.tracks:
                continue
            shelf = Shelf(section.title, f"{len(section.tracks)} tracks")
            play_all = McButton("Play all", small=True, solid=True, icon="play")
            play_all.clicked.connect(
                lambda _=False, tracks=section.tracks: self.window.play_tracks(tracks, 0)
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
                lambda payload: self.window.play_tracks(payload[0], payload[1])
            )
            shelf.played.connect(
                lambda payload: self.window.play_tracks(payload[0], payload[1])
            )
            self.add(shelf, 10)

        if not home.sections and not home.albums:
            self.add(EmptyState(
                "Your library is waiting for its first song",
                "Ask an admin to scan the music folder, or add something yourself from Requests.",
                icon="disc-3",
                action=("Add music", lambda: self.window.navigate(("requests",))),
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
            lambda: self.window.repo.search(query),
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
                action=("Browse library", lambda: self.window.navigate(("library",))),
            ))
            return

        if data.tracks:
            self.rlayout.addWidget(section_head("Songs", f"{len(data.tracks)} results"))
            tl = self.window.make_track_list(data.tracks, self)
            tl.setParent(self.results)
            self.rlayout.addWidget(tl)
            self.track_list = tl
            self.rlayout.addSpacing(22)

        if data.albums:
            self.rlayout.addWidget(section_head("Albums", f"{len(data.albums)} results"))
            grid = TileGrid()
            grid.set_items(_album_items(data.albums))
            grid.opened.connect(lambda a: self.window.navigate(("album", a.album)))
            grid.played.connect(lambda a: self.window.play_album(a.album))
            self.rlayout.addWidget(grid)
            self.rlayout.addSpacing(22)

        if data.artists:
            self.rlayout.addWidget(section_head("Artists", f"{len(data.artists)} results"))
            grid = TileGrid()
            grid.set_items(_artist_items(data.artists))
            grid.opened.connect(lambda a: self.window.navigate(("artist", a.artist)))
            grid.played.connect(lambda a: self.window.play_artist(a.artist))
            self.rlayout.addWidget(grid)


# ── library ────────────────────────────────────────────────────────────────


class LibraryScreen(Screen):
    def __init__(self, window, tab: str = "songs", parent=None):
        super().__init__(window, parent)
        self.tab = tab if tab in ("songs", "albums", "artists") else "songs"
        self.tracks: list[Track] = []
        head = PageHead("Library", "Everything on the server", "")
        self.seg = Segmented(
            [("songs", "Songs"), ("albums", "Albums"), ("artists", "Artists")], self.tab
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
            self.run(self.window.repo.tracks, self._render_songs)
        elif self.tab == "albums":
            self.run(self.window.repo.albums, self._render_albums)
        else:
            self.run(self.window.repo.artists, self._render_artists)

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
        tl = self.window.make_track_list(tracks, self)
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
        grid.opened.connect(lambda a: self.window.navigate(("album", a.album)))
        grid.played.connect(lambda a: self.window.play_album(a.album))
        self.clayout.addWidget(grid)

    def _render_artists(self, artists: list[ArtistRef]) -> None:
        self._clear_content()
        if not artists:
            self.clayout.addWidget(EmptyState("No artists yet", icon="users"))
            return
        self.clayout.addWidget(section_head("Artists", f"{len(artists)} artists"))
        grid = TileGrid()
        grid.set_items(_artist_items(artists))
        grid.opened.connect(lambda a: self.window.navigate(("artist", a.artist)))
        grid.played.connect(lambda a: self.window.play_artist(a.artist))
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
            self.run(lambda: self.window.repo.artist(self.name), self._render)
        else:
            self.run(lambda: self.window.repo.album(self.name), self._render)

    def _render(self, tracks: list[Track]) -> None:
        self.clear()
        self.tracks = tracks
        if not tracks:
            self.add(PageHead("Artist" if self.kind == "artist" else "Album",
                              "", ""), 16)
            self.add(EmptyState(
                "Nothing here", "This release has no tracks on the server.",
                icon="disc-3",
                action=("Back to library", lambda: self.window.navigate(("library",))),
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
        play.clicked.connect(lambda: self.window.play_tracks(tracks, 0))
        hero.add_action(play)
        shuffle = McButton("Shuffle", icon="shuffle")
        shuffle.clicked.connect(lambda: self.window.shuffle_tracks(tracks))
        hero.add_action(shuffle)
        radio = McButton("Radio", ghost=True, icon="radio")
        radio.clicked.connect(lambda: self.window.start_radio(tracks[0]))
        hero.add_action(radio)
        self.add(hero, 10)
        tl = self.window.make_track_list(tracks, self)
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
        self.run(self.window.repo.likes, self._render)

    def _render(self, tracks: list[Track]) -> None:
        self.clear()
        if not tracks:
            self.add(PageHead("Liked songs", "Saved by you", ""), 16)
            self.add(EmptyState(
                "No liked songs yet",
                "Tap the heart on any track and it will show up here.",
                icon="heart",
                action=("Browse library", lambda: self.window.navigate(("library",))),
            ))
            return
        hero = Hero(
            "Collection", "Liked songs",
            [f"{len(tracks)} tracks", fmt_total(sum(t.duration for t in tracks))],
            tracks[0].id,
        )
        play = McButton("Play", solid=True, icon="play")
        play.clicked.connect(lambda: self.window.play_tracks(tracks, 0))
        hero.add_action(play)
        shuffle = McButton("Shuffle", icon="shuffle")
        shuffle.clicked.connect(lambda: self.window.shuffle_tracks(tracks))
        hero.add_action(shuffle)
        self.add(hero, 10)
        tl = self.window.make_track_list(tracks, self)
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
        new.clicked.connect(self.window.create_playlist)
        head.add_action(new)
        self.add(head, 16)
        self.loading()
        self.run(self.window.repo.playlists, self._render)

    def _render(self, playlists: list[PlaylistRef]) -> None:
        self.clear()
        head = PageHead("Playlists", "Your collections", f"{len(playlists)} lists")
        new = McButton("New playlist", solid=True, icon="plus")
        new.clicked.connect(self.window.create_playlist)
        head.add_action(new)
        self.add(head, 16)
        if not playlists:
            self.add(EmptyState(
                "No playlists yet",
                "Group tracks into a playlist — it syncs with the web and mobile apps.",
                icon="list-music",
                action=("Create playlist", self.window.create_playlist),
            ))
            return
        grid = TileGrid()
        grid.set_items(_playlist_items(playlists))
        grid.opened.connect(lambda p: self.window.navigate(("playlist", p.id)))
        grid.played.connect(lambda p: self.window.play_playlist(p.id))
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
        self.run(lambda: self.window.repo.playlist(self.playlist_id), self._render)

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
            play.clicked.connect(lambda: self.window.play_tracks(tracks, 0))
            hero.add_action(play)
            shuffle = McButton("Shuffle", icon="shuffle")
            shuffle.clicked.connect(lambda: self.window.shuffle_tracks(tracks))
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
        tl = self.window.make_track_list(tracks, self, playlist_id=self.playlist_id)
        tl.setParent(self.body)
        self.add(tl)
        self.track_list = tl

    def _rename(self) -> None:
        name = prompt(self, "Rename playlist", "Name", initial=self.playlist_name,
                      confirm="Rename")
        if not name:
            return
        self.run(lambda: self.window.repo.rename_playlist(self.playlist_id, name),
                 lambda _: (self.window.refresh_playlists(), self.window.toast("Renamed"),
                            self.load()))

    def _delete(self) -> None:
        if not confirm(self, "Delete playlist",
                       f"“{self.playlist_name}” will be removed. Tracks stay in the library.",
                       confirm_label="Delete"):
            return

        def job():
            self.window.repo.delete_playlist(self.playlist_id)

        def ok(_):
            self.window.refresh_playlists()
            self.window.toast("Playlist deleted")
            self.window.navigate(("playlists",), push=False)

        self.run(job, ok)


# ── requests ───────────────────────────────────────────────────────────────


class RequestLine(QWidget):
    def __init__(self, row: RequestRow, is_admin: bool, last: bool,
                 on_action: Callable[[int, str], None], parent=None):
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
            self.window.repo.requests,
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
            panel.add_widget(RequestLine(row, is_admin, i == len(rows) - 1, self._act))
        self.llayout.addWidget(panel)

    def _add(self) -> None:
        url = self.url.text().strip()
        if not url.startswith("http"):
            self.window.toast("Paste an https YouTube link")
            return
        self.run(lambda: self.window.repo.request_add(url), self._added)

    def _added(self, status: str) -> None:
        self.url.clear()
        self.window.toast("Sent for approval" if status == "pending" else "Download queued")
        self.load()

    def _act(self, request_id: int, action: str) -> None:
        self.run(lambda: self.window.repo.request_act(request_id, action),
                 lambda _: self.load())


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
        p.drawRoundedRect(rect, 4, 4)
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0, QColor(surface))
        grad.setColorAt(1, QColor(accent))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawRoundedRect(QRectF(rect.x() + 1, rect.y() + 1, rect.width() - 2, 38), 3, 3)
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
        self._density: Optional[Segmented] = None
        self.load()

    def load(self) -> None:
        self.clear()
        settings = self.window.settings
        user = self.window.me
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
            card = ThemeCard(name, name, name == settings.theme)
            card.clicked.connect(lambda _=False, n=name: self._pick_theme(n))
            self._theme_cards.append(card)
            line.addWidget(card)
        line.addStretch(1)
        panel.add_widget(themes_row)

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
        self._density = Segmented([("comfy", "Comfy"), ("compact", "Compact")],
                                  settings.density)
        self._density.changed.connect(lambda value: self._set(density=value))
        panel.add_row("Density", "Row height in track lists", self._density)
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
            ("offline_audio", "Offline audio cache", "Keep streamed audio on disk", settings.offline_audio),
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
        # room link row
        room_row = QWidget()
        rline = QHBoxLayout(room_row)
        rline.setContentsMargins(0, 0, 0, 0)
        rline.setSpacing(8)
        from PySide6.QtCore import QUrl, QDesktopServices
        room_url = self.window.settings.room_url or ""
        if room_url:
            room_display = room_url.rstrip('/') + "#room=" + (self.window.me.rotur_user_id[:8] if self.window.me else "C0de")
            room_txt = Txt(room_display, size=11, token="dim", family="mono", wrap=True)
            copy_btn = McButton("Copy", small=True, ghost=True)
            copy_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(room_url)))
            rline.addWidget(room_txt)
            rline.addWidget(copy_btn)
        else:
            room_txt = Txt("Generating room link…", size=11, token="dim")
            rline.addWidget(room_txt)
        room_row.setEnabled(False)  # greyed out until ready
        rline.addStretch(1)

        server_row = QWidget()
        sline = QHBoxLayout(server_row)
        sline.setContentsMargins(0, 0, 0, 0)
        sline.setSpacing(8)
        sline.addWidget(Txt(self.window.api.base_url, size=11, family="mono",
                            token="dim"))
        change = McButton("Change", small=True, ghost=True)
        change.clicked.connect(self._change_server)
        sline.addWidget(change)
        panel.add_row("Server", "Where the library lives", server_row)
        password = McButton("Change password", small=True)
        password.clicked.connect(self._change_password)
        panel.add_row("Password", "Update your local account password", password)
        self._rotur_trailing = QWidget()
        self._rotur_layout = QHBoxLayout(self._rotur_trailing)
        self._rotur_layout.setContentsMargins(0, 0, 0, 0)
        self._rotur_layout.setSpacing(8)
        self._rotur_trailing.setMinimumWidth(120)
        self.add_panel_rotur = panel.add_row(
            "RoturLink", "Checking…", self._rotur_trailing
        )
        self._rotur_row = self.add_panel_rotur
        if user and user.is_admin:
            admin = McButton("Open admin", small=True, ghost=True, icon="users")
            admin.clicked.connect(lambda: self.window.navigate(("admin",)))
            panel.add_row("Admin", "Manage users, requests and scans", admin)
        signout = McButton("Sign out", small=True, danger=True, icon="log-out")
        signout.clicked.connect(self.window.sign_out)
        panel.add_row("Session", "Sign out of this desktop", signout, last=True)
        self.add(panel, 16)

        about = Txt(
            "mcmusic desktop · native Qt 6 client. Same server API, palette and icons "
            "as the web player and Android app.",
            size=11, token="dim2", wrap=True,
        )
        self.add(about)

        self.run(self.window.repo.rotur_status, self._render_rotur,
                 error=lambda _e: self._render_rotur({}))

    # helpers ------------------------------------------------------------
    def _set(self, **changes) -> None:
        self.window.apply_settings(replace(self.window.settings, **changes))

    def _pick_theme(self, name: str) -> None:
        self.window.apply_settings(replace(self.window.settings, theme=name))

    def _pick_accent(self, color: str) -> None:
        self.window.apply_settings(replace(self.window.settings, accent=color))

    def _pick_custom_accent(self) -> None:
        initial = QColor(self.window.settings.accent)
        chosen = QColorDialog.getColor(initial, self, "Accent colour")
        if chosen.isValid():
            self._pick_accent(chosen.name())

    def _change_server(self) -> None:
        url = prompt(self, "Change server", "Server URL",
                     initial=self.window.api.base_url, placeholder="http://host:8000",
                     confirm="Connect")
        if url:
            self.window.change_server(url)

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
                self.window.repo.change_password(old.text(), new.text())

            def ok(_):
                sheet.accept()
                self.window.toast("Password changed")

            def fail(exc: Exception) -> None:
                save.setEnabled(True)
                error.setText(str(exc))
                error.setVisible(True)

            self.window.run(job, ok, fail)

        save.clicked.connect(submit)
        new.edit.returnPressed.connect(submit)
        old.edit.setFocus()
        sheet.exec()

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
        self.run(self.window.repo.unlink_rotur, lambda _: self.load())

    def _open_rotur(self) -> None:
        QDesktopServices.openUrl(self.window.api.web_url("api/auth/rotur/authorize"))

    def apply_settings(self, settings: Settings) -> None:
        for card in self._theme_cards:
            card.set_selected(card.name == settings.theme)
        current = QColor(settings.accent).name().lower()
        for swatch in self._swatches:
            swatch.set_selected(swatch.color.lower() == current)
        if self._density is not None:
            self._density.set_selected(settings.density)


# ── admin ──────────────────────────────────────────────────────────────────


class AdminScreen(Screen):
    def __init__(self, window, parent=None):
        super().__init__(window, parent)
        self.load()

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
        self.run(self.window.repo.admin_stats, self._render_stats)
        self.run(self.window.repo.admin_users, self._render_users)

    def _render_stats(self, stats: AdminStats) -> None:
        if not isValid(self):
            return
        self.stop_loading()
        # Replace only the stats block (it is the first content widget).
        target = None
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if getattr(widget, "_mc_stats", False):
                target = widget
                break
        if target is not None:
            target.setParent(None)
            target.deleteLater()
        grid_widget = QWidget()
        grid_widget._mc_stats = True  # type: ignore[attr-defined]
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 18)
        grid.setSpacing(8)
        cards = [
            (str(stats.users), "users"),
            (str(stats.admins), "admins"),
            (str(stats.tracks), "tracks"),
            (str(stats.albums), "albums"),
            (str(stats.playlists), "playlists"),
            (str(stats.plays), "plays"),
            (str(stats.queue), "queue"),
            (str(stats.rooms), "rooms"),
            (fmt_bytes(stats.music_bytes), "music"),
            (fmt_bytes(stats.disk_free), "disk free"),
            (fmt_uptime(stats.uptime), "uptime"),
        ]
        columns = max(2, min(6, self.width() // 190))
        for i, (value, label) in enumerate(cards):
            grid.addWidget(StatCard(value, label), i // columns, i % columns)
        self.layout.insertWidget(1, grid_widget)

    def _render_users(self, users: list[AdminUser]) -> None:
        if not isValid(self):
            return
        target = None
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if getattr(widget, "_mc_users", False):
                target = widget
                break
        if target is not None:
            target.setParent(None)
            target.deleteLater()
        panel = Panel("Users")
        panel._mc_users = True  # type: ignore[attr-defined]
        for i, user in enumerate(users):
            trailing = QWidget()
            line = QHBoxLayout(trailing)
            line.setContentsMargins(0, 0, 0, 0)
            line.setSpacing(8)
            if user.is_admin:
                line.addWidget(StatusChip("admin", "accent"))
            button = McButton("Revoke" if user.is_admin else "Make admin",
                              small=True, ghost=True,
                              danger=user.is_admin)
            button.clicked.connect(lambda _=False, u=user: self._toggle_admin(u))
            line.addWidget(button)
            subtitle = (f"{user.plays} plays · {user.likes} likes · "
                        f"{user.playlists} playlists · {user.requests} requests")
            panel.add_row(user.username, subtitle, trailing, last=i == len(users) - 1)
        self.add(panel)
        self.reset_scroll()

    def _toggle_admin(self, user: AdminUser) -> None:
        self.run(
            lambda: self.window.repo.admin_set_admin(user.id, not user.is_admin),
            lambda _: (self.window.toast(
                "Admin removed" if user.is_admin else "Admin granted"), self.load()),
        )

    def _rescan(self) -> None:
        self.run(
            self.window.repo.admin_scan,
            lambda result: self.window.toast(f"{result[0]} tracks · {result[1]} albums"),
        )

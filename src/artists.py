#!/usr/bin/env python3
"""Split collab artist tags into the individual artists on the track.

A tag like "Artist A, Artist B feat. Artist C" is stored as-is on the track
(the UI keeps showing the full credit), and each name is indexed in
track_artists so the song shows up on every collaborator's artist page.

Each name also gets an artist_key: case, spacing, full-width forms and kana
romanisation are folded so "Uraru" and "うらる" resolve to the same artist.
"""
import json
import re
import unicodedata

# Separators that mean "another artist is credited here". "&" and "x" only
# count when spaced so "AC/DC" survives; spaced "&" is treated as a collab
# credit ("A & B"), which is the common case in YouTube music tags.
SPLIT_RE = re.compile(
    r"\s*(?:,|;|\s&\s|\s×\s|\sx\s|\bfeat\.?|\bft\.?|\bfeaturing\b|\bwith\b|\bvs\.?)\s*",
    re.I,
)
FEAT_TITLE_RE = re.compile(r"\b(?:feat\.?|ft\.?|featuring)\s+([^()\[\]{}]+)", re.I)
EDGE_RE = re.compile(r"^[\s\-–—,;:]+|[\s\-–—,;:]+$")

# Hiragana -> romaji, one row per consonant group. Katakana folds onto these.
_KANA_ROWS = (
    "あいうえお:a i u e o",
    "かきくけこ:ka ki ku ke ko",
    "がぎぐげご:ga gi gu ge go",
    "さしすせそ:sa shi su se so",
    "ざじずぜぞ:za ji zu ze zo",
    "たちつてと:ta chi tsu te to",
    "だぢづでど:da ji zu de do",
    "なにぬねの:na ni nu ne no",
    "はひふへほ:ha hi fu he ho",
    "ばびぶべぼ:ba bi bu be bo",
    "ぱぴぷぺぽ:pa pi pu pe po",
    "まみむめも:ma mi mu me mo",
    "やゆよ:ya yu yo",
    "らりるれろ:ra ri ru re ro",
    "わを:wa o",
    "ん:n",
    "ぁぃぅぇぉ:a i u e o",
    "ゃゅょ:ya yu yo",
    "ゎ:wa",
    "ゔ:vu",
)
_KANA = {}
for _row in _KANA_ROWS:
    _kana, _romaji = _row.split(":")
    for _k, _r in zip(_kana, _romaji.split()):
        _KANA[_k] = _r

_KATAKANA_SHIFT = ord("ア") - ord("あ")


def _romaji(text):
    """Romanise kana, leave everything else alone."""
    out = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:  # katakana -> hiragana
            ch = chr(code - _KATAKANA_SHIFT)
        if ch in _KANA:
            out.append(_KANA[ch])
        elif ch in "ーっッ":
            continue
        else:
            out.append(ch)
    return "".join(out)


def norm_key(name):
    """Matching key: case-, spacing-, width- and kana-insensitive."""
    text = unicodedata.normalize("NFKC", str(name or ""))
    text = _romaji(text.casefold())
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean(part):
    name = re.sub(r"\s+", " ", str(part or "")).strip()
    name = EDGE_RE.sub("", name)
    return name


def split_artists(artist, title=""):
    """Individual artist names, in credit order, de-duplicated case-insensitively."""
    text = _clean(artist)
    found = []
    seen = set()

    def add(name):
        name = _clean(name)
        key = name.casefold()
        if name and key not in seen:
            seen.add(key)
            found.append(name)

    for part in SPLIT_RE.split(text):
        add(part)

    # "Song (feat. X)" credits are often only in the title.
    if title:
        m = FEAT_TITLE_RE.search(str(title))
        if m:
            for part in SPLIT_RE.split(m.group(1)):
                add(part)

    return found


def index_track(conn, track_id, artist, title="", names=None):
    """(Re)write track_artists, the artist_key index and tracks.artists JSON.

    The puller can pass the exact credited names it parsed; older callers fall
    back to splitting the (possibly raw) artist tag here.
    """
    names = list(names) if names is not None else split_artists(artist, title)
    conn.execute("delete from track_artists where track_id=?", (track_id,))
    for pos, name in enumerate(names):
        conn.execute(
            "insert or ignore into track_artists(track_id, artist, artist_key, position) "
            "values(?,?,?,?)",
            (track_id, name, norm_key(name) or name.casefold(), pos),
        )
    conn.execute("update tracks set artists=? where id=?", (json.dumps(names), track_id))
    return names


def backfill(conn):
    """Index artists for tracks that were scanned before split credits existed."""
    rows = conn.execute(
        "select id, artist, title from tracks where id not in "
        "(select track_id from track_artists)"
    ).fetchall()
    for row in rows:
        index_track(conn, row["id"], row["artist"], row["title"])
    return len(rows)


def reindex_all(conn):
    """Rebuild the whole index (used when the key scheme changes)."""
    rows = conn.execute("select id, artist, title from tracks").fetchall()
    for row in rows:
        index_track(conn, row["id"], row["artist"], row["title"])
    return len(rows)

"""Metadata parsing shared by the song puller and the library scanner.

Everything here works on data yt-dlp already gives us -- the raw video title,
the uploader/channel name, tags, categories and the description. There are no
network calls and no database access, so the same rules can be used while a
video is being downloaded, while the library is scanned and while duplicates
are matched.
"""
import re
import unicodedata

# Text that describes the *upload*, not the song. It is removed from displayed
# titles and ignored when deciding whether a bracket is meaningful.
NOISE_WORDS = {
    "official", "video", "music", "audio", "lyric", "lyrics", "hd", "hq",
    "full", "mv", "m", "v", "4k", "720p", "1080p", "visualizer", "visualiser",
    "remaster", "remastered", "teaser", "preview", "topic", "vevo",
}
VERSION_WORDS = {
    "cover", "live", "acoustic", "instrumental", "karaoke", "remix", "mix",
    "edit", "version", "sped", "slowed", "nightcore", "piano", "orchestral",
    "fan", "parody", "instrumental", "english", "full",
}
BAD_ARTISTS = {
    "unknown", "unknown artist", "various", "various artists", "official",
    "music", "video", "audio", "lyrics", "lyric", "topic", "vevo",
    # "Alone With Me" and "Down with the King" are titles, not credits.
    "me", "you", "us", "them", "him", "her", "it", "myself", "yourself",
    "everyone", "everybody", "somebody", "nobody",
}

BRACKET_RE = re.compile(r"[\(\[\{（【「《]([^\)\]\}）】」》]*)[\)\]\}）】」》]")
CREDIT_BRACKET_RE = re.compile(r"[【\[]([^\]】]{1,80})[】\]]")
TOPIC_RE = re.compile(r"\s*[-–—]\s*topic\s*$", re.I)
LEAD_INDEX_RE = re.compile(r"^\s*\d{1,3}\s*[-–—]\s*")
DASH_RE = re.compile(r"\s+[-–—]\s+")
CREDIT_SPLIT_RE = re.compile(
    r"\s*(?:,|;|、|\s&\s|\s×\s|\sx\s|\bfeat\.?|\bft\.?|\bfeaturing\b|\bwith\b|\bvs\.?)\s*",
    re.I,
)
# Deliberately no bare "with": song titles like "Alone With Me" and
# "Down with the King" are not collaborations. Only explicit feat./ft.
# credit markers count (plus the "Artist - Title" dash handled separately).
FEAT_RE = re.compile(
    r"\b(?:feat\.?|ft\.?|featuring|vs\.?)\s+"
    r"((?:(?!\s[-–—]\s)[^\(\)\[\]\{\}【】「」《》]){1,100})",
    re.I,
)
NOISE_RE = re.compile(
    r"\b(?:official(?:\s+(?:music|video|audio|lyrics?))?|(?:music\s+)?video|"
    r"audio|lyric(?:\s+video)?|lyrics|with\s+lyrics?|hd|hq|full\s*hd|4k|"
    r"720p|1080p|m/?v|visuali[sz]er|remaster(?:ed)?|teaser|preview)\b",
    re.I,
)
HASHTAG_RE = re.compile(r"#([^\s#]{2,40})")
CREDIT_LINE_RE = re.compile(
    r"^\s*(?:artists?|vocals?|singers?|performed\s+by|music\s+by|song\s+by|"
    r"by|featuring|feat\.?|ft\.?|with)\s*[:：]\s*(.+)$",
    re.I | re.M,
)
YT_ID_RE = re.compile(
    r"(?:youtube\.com/watch\?[^\s'\"&]*?v=|youtu\.be/|youtube\.com/shorts/|"
    r"youtube\.com/live/|youtube\.com/embed/|v=)([\w-]{11})",
    re.I,
)

# Keywords that describe what a track *is*. They are only used for themes;
# they never rewrite the title or get mistaken for an artist.
THEME_PATTERNS = (
    (r"\benglish\s+cover\b", "English Cover"),
    (r"\bcover\b", "Cover"),
    (r"\blive\b", "Live"),
    (r"\bacoustic\b", "Acoustic"),
    (r"\binstrumental\b", "Instrumental"),
    (r"\bkaraoke\b", "Karaoke"),
    (r"\bremix\b", "Remix"),
    (r"\bsped\s*up\b", "Sped Up"),
    (r"\bslowed\b", "Slowed"),
    (r"\bnightcore\b", "Nightcore"),
    (r"\blo[-\s]?fi\b", "Lo-fi"),
    (r"\bvocaloid\b", "Vocaloid"),
    (r"\banime\b", "Anime"),
    (r"\bgame\b", "Game"),
    (r"\bopening\b", "Opening"),
    (r"\bending\b", "Ending"),
    (r"\b(?:ost|soundtrack)\b", "Soundtrack"),
    (r"\bfan\s*song\b", "Fan Song"),
    (r"\bparody\b", "Parody"),
    (r"\bmeme\b", "Meme"),
    (r"\bpiano\b", "Piano"),
    (r"\borchestral\b", "Orchestral"),
    (r"\bmetal\b", "Metal"),
    (r"\brock\b", "Rock"),
    (r"\bjazz\b", "Jazz"),
    (r"\bclassical\b", "Classical"),
    (r"\belectronic\b", "Electronic"),
    (r"\bedm\b", "EDM"),
    (r"\bchiptune\b", "Chiptune"),
    (r"\b8[-\s]?bit\b", "8-bit"),
    (r"\bsad\b", "Sad"),
    (r"\bchill\b", "Chill"),
    (r"\benergetic\b", "Energetic"),
)


def _squash(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _words(value):
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return {w for w in re.findall(r"\w+", text, re.UNICODE)
            if re.search(r"[a-z0-9]", w)}


def _tokens(value):
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return re.findall(r"\w+", text, re.UNICODE)


def video_id(value):
    """Pull an 11-character YouTube video id out of a URL, or return None."""
    if not value:
        return None
    m = YT_ID_RE.search(str(value))
    return m.group(1) if m else None


def _is_junk_bracket(content):
    if not _tokens(content):
        return True
    words = _words(content)
    if words and words <= NOISE_WORDS:
        return True
    return bool(re.search(
        r"\b(?:official|music)?\s*(?:video|audio|lyric\s*video|lyrics?)\b",
        content, re.I,
    )) and len(words) <= 4


def _is_credit_bracket(content):
    """True for 【Will Stetson】-style credit brackets, not for version/source text."""
    words = _words(content)
    return bool(words) and not (words & VERSION_WORDS) \
        and not _is_junk_bracket(content) and len(content.strip()) <= 60


def _clean_artist(value):
    name = _squash(value)
    name = TOPIC_RE.sub("", name)
    name = re.sub(r"\s+vevo\s*$", "", name, flags=re.I)
    name = re.sub(r"^[\s\[\(【「]+|[\s\]\)】」]+$", "", name)
    name = name.strip(" ,;、&×x-–—")
    # Channel handles often carry a second alias ("Jamie Paige / JamieP") or
    # decorative emoji ("rachie 🎀💌"). Keep the human-readable artist, not the
    # handle decoration, so the display artist stays consistent in the library.
    if " / " in name:
        parts = [p.strip() for p in name.split(" / ") if p.strip()]
        spaced = [p for p in parts if " " in p]
        ascii_parts = [p for p in parts if p.isascii()]
        name = spaced[0] if spaced else (ascii_parts[0] if ascii_parts else parts[0])
    name = re.sub(r"\s+[^\w\s\-'.,&!?\u3040-\u30ff\u4e00-\u9fff]+$", "", name)
    name = _squash(name)
    if not name or name.casefold() in BAD_ARTISTS:
        return ""
    return name


def _artist_key(value):
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[^a-z0-9]+", "", text)


def _first_dash(text):
    """Index of a top-level ' - ', ignoring dashes inside brackets/quotes."""
    depth = 0
    for i, ch in enumerate(text):
        if ch in "([{（【「《":
            depth += 1
        elif ch in ")]}）】」》":
            depth = max(0, depth - 1)
        elif depth == 0 and ch in "-–—":
            if text[:i].strip() and text[i + 1:].strip():
                return i
    return -1


def clean_title(raw):
    """Strip upload noise while keeping version-defining text intact."""
    text = _squash(raw)
    text = LEAD_INDEX_RE.sub("", text)

    # "Artist - Song (Official Video)" -> "Song (Official Video)"
    pos = _first_dash(text)
    if pos > 0 and len(text[:pos]) <= 80:
        text = text[pos + 1:].strip()

    # Drop "feat. X" / "with X" from the title; those names become artists.
    text = FEAT_RE.sub(" ", text)

    def replace_bracket(match):
        content = _squash(match.group(1))
        if _is_junk_bracket(content):
            return " "
        if match.group(0).startswith(("【", "[")) and _is_credit_bracket(content):
            return " "
        return f" {match.group(0)} "

    text = BRACKET_RE.sub(replace_bracket, text)
    text = TOPIC_RE.sub(" ", text)
    text = NOISE_RE.sub(" ", text)
    text = re.sub(r"\s+[-–—]\s*$", "", text)
    text = _squash(text).strip(" ,;、-–—")
    return text or _squash(raw) or "Unknown Title"


def artist_names(raw_title="", artist="", creator="", uploader="", channel="", description=""):
    """All credited artists, in credit order, without upload/channel noise."""
    raw = _squash(raw_title)
    credited = []

    def add(value):
        for part in CREDIT_SPLIT_RE.split(_squash(value)):
            name = _clean_artist(part)
            if name and name.casefold() not in {n.casefold() for n in credited}:
                credited.append(name)

    # Explicit upload metadata is the source of truth. A title like
    # "Trickle • Forget Me Not (MV) – Reverse: 1999" has a dash, but the text
    # before it is a song title, not an artist -- trusting it produced broken
    # artist names. The channel/uploader only loses to a real artist/creator
    # tag, never to a title fragment.
    for value in (artist, creator, uploader, channel):
        add(value)
    if not credited:
        # No upload credits at all: fall back to the old title parsing.
        title_credits = []
        pos = _first_dash(raw)
        if pos > 0 and len(raw[:pos]) <= 80:
            title_credits.append(raw[:pos])
        for pattern in (CREDIT_BRACKET_RE, FEAT_RE):
            for match in pattern.finditer(raw):
                title_credits.append(match.group(1))
        for value in title_credits:
            add(value)
    else:
        # Featured credits in the title/description are still worth keeping.
        for match in FEAT_RE.finditer(raw):
            add(match.group(1))
    for line in CREDIT_LINE_RE.findall(str(description or "")):
        add(line)
    return credited[:8]


def artist_display(names):
    return ", ".join(names or [])


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v) for v in value]
    return [p.strip() for p in re.split(r"[,;|]", str(value))]


def extract_themes(title="", description="", tags=None, categories=None,
                   genre="", artists=(), limit=24):
    """Collect tags/themes from any metadata the puller already has."""
    title = str(title or "")
    description = str(description or "")
    haystack = " ".join((title, description)).lower()
    themes = []

    def add(value):
        name = _squash(value).strip("# ")
        if not (2 <= len(name) <= 60) or _is_junk_bracket(name):
            return
        if name.casefold() in {t.casefold() for t in themes}:
            return
        if name.casefold() in {a.casefold() for a in (artists or ())}:
            return
        themes.append(name)

    for pattern, label in THEME_PATTERNS:
        if re.search(pattern, haystack):
            add(label)
    for match in BRACKET_RE.finditer(clean_title(title)):
        content = _squash(match.group(1))
        if _is_junk_bracket(content):
            continue
        if match.group(0).startswith(("【", "[")) and _is_credit_bracket(content):
            continue
        add(content)
    for tag in HASHTAG_RE.findall(description):
        add(tag)
    for tag in HASHTAG_RE.findall(title):
        add(tag)
    for value in (*_as_list(tags), *_as_list(categories), *_as_list(genre)):
        add(value)
    return themes[:limit]


def parse_song_meta(raw_title="", artist="", creator="", uploader="", channel="",
                    description="", tags=None, categories=None, genre=""):
    """Turn raw puller metadata into clean title, credited artists and themes."""
    raw = _squash(raw_title)
    credited = artist_names(raw, artist, creator, uploader, channel, description)
    title = clean_title(raw)
    # "Song (feat. X)" already lost its credit bracket; remove any remaining
    # bare credit phrase so the title is just the song.
    title = _squash(FEAT_RE.sub(" ", title)) or raw or "Unknown Title"
    themes = extract_themes(raw, description, tags, categories, genre, credited)
    return {
        "raw_title": raw,
        "title": title,
        "artists": credited,
        "artist": artist_display(credited),
        "themes": themes,
        "genre": _squash(genre),
    }


def match_text(value):
    """Noise-free text for duplicate matching (keeps version info, drops credits)."""
    text = _squash(value)
    text = TOPIC_RE.sub(" ", text)
    text = FEAT_RE.sub(" ", text)
    text = CREDIT_BRACKET_RE.sub(" ", text)
    text = BRACKET_RE.sub(
        lambda m: " " if _is_junk_bracket(m.group(1)) else f" {m.group(1)} ",
        text,
    )
    text = NOISE_RE.sub(" ", text)
    return _squash(text)

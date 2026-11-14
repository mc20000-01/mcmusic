"""The builds we hand out.

One table describes every app we ship, where its file lives, and how to label
it. The website reads this through /api/builds so a new build shows up without
touching the front end, and the email endpoint uses the same table so the
attachment always matches what the download button serves.
"""
import hashlib
import os
import re
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = os.path.join(ROOT, "apps")

BUILDS = {
    "android": {
        "label": "Android",
        "name": "mcmusic for Android",
        "dir": os.path.join(APPS, "android"),
        "pattern": ".apk",
        "latest": "mainbuild.apk",
        "hint": "Signed APK. Install over the old one to update — your library stays put.",
        "ext": "apk",
        "maintype": "application",
        "subtype": "vnd.android.package-archive",
        "note": "Android 7.0 and newer.",
    },
    "linux-appimage": {
        "label": "Linux (AppImage)",
        "name": "mcmusic for Linux",
        "dir": os.path.join(APPS, "linux"),
        "pattern": ".AppImage",
        "latest": "mcmusic-x86_64.AppImage",
        "hint": "Runs anywhere without installing. Mark it executable, then open it.",
        "ext": "AppImage",
        "maintype": "application",
        "subtype": "x-executable",
        "note": "64-bit x86 Linux.",
    },
    "linux-deb": {
        "label": "Linux (deb)",
        "name": "mcmusic for Debian and Ubuntu",
        "dir": os.path.join(APPS, "linux"),
        "pattern": ".deb",
        "latest": "mcmusic_amd64.deb",
        "hint": "Installs into your applications menu like any other package.",
        "ext": "deb",
        "maintype": "application",
        "subtype": "vnd.debian.binary-package",
        "note": "Debian, Ubuntu, and friends on 64-bit x86.",
    },
}


def _stamp(path):
    when = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
    return when.strftime("%d %b %Y")


_DIGESTS = {}


def _digest(path):
    """Short content hash for the download URL.

    A value cache means /api/builds does not re-read a 13 MB APK on every
    page load, while a replaced file always gets a new URL — so neither the
    browser nor an edge cache can keep serving yesterday's bytes.
    """
    st = os.stat(path)
    key = (path, st.st_size, int(st.st_mtime))
    hit = _DIGESTS.get(key)
    if hit:
        return hit
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    out = h.hexdigest()[:16]
    _DIGESTS.clear()
    _DIGESTS[key] = out
    return out


def _pick(spec):
    """The concrete file for a build: the newest matching file.

    The stable name is preferred on a tie, but a fresh named copy still wins
    if publish_apps.sh managed to write it after mainbuild.apk.
    """
    stable = os.path.join(spec["dir"], spec["latest"])
    if not os.path.isdir(spec["dir"]):
        return stable if os.path.isfile(stable) else None
    found = [
        os.path.join(spec["dir"], f)
        for f in os.listdir(spec["dir"])
        if f.endswith(spec["pattern"])
    ]
    if os.path.isfile(stable):
        found.append(stable)
    if not found:
        return None
    found.sort(key=os.path.getmtime, reverse=True)
    return found[0]


def _named(spec, path):
    """The friendly name we show and attach, e.g. mcmusic-2.0.apk. The file on
    disk under that name is the same bytes as the stable link."""
    ext = spec["ext"]
    folder = spec["dir"]
    if os.path.isdir(folder):
        found = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.startswith("mcmusic-") and f.endswith(f".{ext}")
        ]
        if found:
            return os.path.basename(max(found, key=os.path.getmtime))
    return os.path.basename(path)


def describe(kind):
    spec = BUILDS.get(kind)
    if not spec:
        return None
    path = _pick(spec)
    if not path:
        return {
            "kind": kind,
            "label": spec["label"],
            "name": spec["name"],
            "hint": spec["hint"],
            "note": spec["note"],
            "available": False,
        }
    file = _named(spec, path)
    served = os.path.join(spec["dir"], file)
    if not os.path.isfile(served):
        served = path
    digest = _digest(served)
    match = re.search(r"mcmusic-([^/]+)\.[A-Za-z0-9]+$", file)
    return {
        "kind": kind,
        "label": spec["label"],
        "name": spec["name"],
        "hint": spec["hint"],
        "note": spec["note"],
        "available": True,
        "file": file,
        "version": match.group(1) if match else None,
        "url": f"/apps/{os.path.basename(spec['dir'])}/{os.path.basename(served)}?v={digest}",
        "bytes": os.path.getsize(path),
        "built": _stamp(path),
        "mimetype": f"{spec['maintype']}/{spec['subtype']}",
    }


def all_builds():
    return [describe(kind) for kind in BUILDS]


def available_builds():
    return [b for b in all_builds() if b.get("available")]


def attachment(kind):
    """(path, filename, mimetype) for the build, or None when it isn't built."""
    spec = BUILDS.get(kind)
    if not spec:
        return None
    path = _pick(spec)
    if not path:
        return None
    return path, _named(spec, path), (spec["maintype"], spec["subtype"])

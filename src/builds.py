"""The builds we hand out.

One table describes every app we ship, where its file lives, and how to label
it. The website reads this through /api/builds so a new build shows up without
touching the front end, and the email endpoint uses the same table so the
attachment always matches what the download button serves.
"""
import hashlib
import os
import re
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
        "note": "Android 14 and newer.",
    },
    "ios": {
        "label": "iOS (Simulator)",
        "name": "mcmusic for iOS",
        "dir": os.path.join(APPS, "ios"),
        "pattern": ".app.zip",
        "latest": "mainbuild.zip",
        "hint": "Unsigned SwiftUI Simulator build. iOS cannot install it from the app; open this page in Safari for the current build.",
        "ext": "zip",
        "maintype": "application",
        "subtype": "zip",
        "note": "Requires Xcode and iOS Simulator; not installable on a physical iPhone.",
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
    "macos": {
        "label": "macOS",
        "name": "mcmusic for macOS",
        "dir": os.path.join(APPS, "macos"),
        "pattern": ".zip",
        "latest": "mainbuild.zip",
        "hint": "Unzip and open mcmusic.app. If Gatekeeper blocks an unsigned "
                "build, right-click it and choose Open.",
        "ext": "zip",
        "maintype": "application",
        "subtype": "zip",
        "note": "Apple silicon or Intel via Rosetta 2.",
    },
    "macos-dmg": {
        "label": "macOS (disk image)",
        "name": "mcmusic for macOS (DMG)",
        "dir": os.path.join(APPS, "macos"),
        "pattern": ".dmg",
        "latest": "mainbuild.dmg",
        "hint": "Open the image and drag mcmusic.app into Applications.",
        "ext": "dmg",
        "maintype": "application",
        "subtype": "x-apple-diskimage",
        "note": "Signed and notarized builds when release credentials are set.",
    },
    "windows": {
        "label": "Windows",
        "name": "mcmusic for Windows",
        "dir": os.path.join(APPS, "windows"),
        "pattern": ".zip",
        "latest": "mainbuild.zip",
        "hint": "Unzip and run mcmusic.exe. Keep the whole folder together.",
        "ext": "zip",
        "maintype": "application",
        "subtype": "zip",
        "note": "64-bit Windows 10 and newer.",
    },
    "windows-zip": {
        "label": "Windows (zip)",
        "name": "mcmusic for Windows (portable zip)",
        "dir": os.path.join(APPS, "windows"),
        "pattern": ".zip",
        "latest": "mainbuild.zip",
        "hint": "Portable bundle: unzip anywhere and launch mcmusic.exe.",
        "ext": "zip",
        "maintype": "application",
        "subtype": "zip",
        "note": "Same portable build as the Windows download.",
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


def _version_from_filename(name):
    """Extract a dotted client version from any published artifact name.

    Names vary by platform (``mcmusic-desktop_4.1.0_all.deb``,
    ``mcmusic-ios-simulator-4.1.0.app.zip``), so a single suffix regex used to
    return the whole middle of the name. Updaters need the real version.
    """
    base = os.path.basename(name)
    if base == "mcmusic-x86_64.AppImage":
        # The stable AppImage name carries no release number. Claiming
        # "x86_64" as a version made updaters treat it as newer than 4.1.0.
        return None
    matches = re.findall(
        r"(?<![0-9])(\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z.]+)?)(?![0-9])", base
    )
    return matches[0] if matches else None


def describe(kind):
    spec = BUILDS.get(kind)
    if not spec:
        return None
    path = _pick(spec)
    if not path:
        # A self-hosted server may have no build output at all. The public
        # GitHub Release is the fallback; /apps/... pulls it in on demand.
        import github_builds
        remote = github_builds.match(kind)
        if not remote:
            return {
                "kind": kind,
                "label": spec["label"],
                "name": spec["name"],
                "hint": spec["hint"],
                "note": spec["note"],
                "available": False,
            }
        file = remote["name"]
        folder = os.path.basename(spec["dir"])
        digest = (remote.get("digest") or "")[:16] or "latest"
        return {
            "kind": kind,
            "label": spec["label"],
            "name": spec["name"],
            "hint": spec["hint"],
            "note": spec["note"],
            "available": True,
            "file": file,
            "version": _version_from_filename(file),
            "url": f"/apps/{folder}/{file}?v={digest}",
            "bytes": remote["size"],
            "built": github_builds.built_stamp(remote),
            "mimetype": f"{spec['maintype']}/{spec['subtype']}",
            "source": "github",
        }
    file = _named(spec, path)
    served = os.path.join(spec["dir"], file)
    if not os.path.isfile(served):
        served = path
    digest = _digest(served)
    return {
        "kind": kind,
        "label": spec["label"],
        "name": spec["name"],
        "hint": spec["hint"],
        "note": spec["note"],
        "available": True,
        "file": file,
        "version": _version_from_filename(file),
        "url": f"/apps/{os.path.basename(spec['dir'])}/{os.path.basename(served)}?v={digest}",
        "bytes": os.path.getsize(path),
        "built": _stamp(path),
        "mimetype": f"{spec['maintype']}/{spec['subtype']}",
        "source": "server",
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
        import github_builds
        if not github_builds.ensure(kind):
            return None
        path = _pick(spec)
    if not path:
        return None
    return path, _named(spec, path), (spec["maintype"], spec["subtype"])

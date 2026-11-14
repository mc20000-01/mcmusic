#!/usr/bin/env python3
"""Throwaway mcmusic server for the client integration tests.

Run as a script it boots the real Flask app against the DATA_DIR / MUSIC_DIR the
parent handed it, listens on ``$PORT`` and seeds one track row so the playlist
and playback endpoints have something to point at. Imported, it offers
``ThrowawayServer``, which starts and tears down that same script for a test
class. Nothing here touches the running mcmusic instance.
"""
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SEED_PATH = "seeded.mp3"
INVITE = "test-invite"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ThrowawayServer:
    """A real server process with its own data, music dir and free port."""

    def __init__(self, invite: str = INVITE):
        self.invite = invite
        self.tmp = Path(tempfile.mkdtemp(prefix="mcmusic-it-"))
        self.music_dir = self.tmp / "music"
        self.data_dir = self.tmp / "data"
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.tmp / "server.log"
        self.base = ""
        self.proc = None
        self._log = None

    # lifecycle ---------------------------------------------------------
    def start(self) -> "ThrowawayServer":
        # The real downloader must never run: approving a request would spawn
        # yt-dlp. This stand-in fails immediately, so a request reaches
        # "failed" and the suite stays offline.
        dl_script = self.tmp / "fake_download.py"
        dl_script.write_text("import sys\nsys.exit(1)\n")

        port = free_port()
        env = {
            k: v for k, v in os.environ.items()
            if not k.lower().startswith(("discord_", "rotur_"))
        }
        env.update({
            "DATA_DIR": str(self.data_dir),
            "MUSIC_DIR": str(self.music_dir),
            "STAGING_DIR": str(self.music_dir / ".staging"),
            "DL_SCRIPT": str(dl_script),
            "AUTO_APPROVE": "0",
            "YT_ENRICH": "0",
            "INVITE_CODE": self.invite,
            "API_RATE_LIMIT": "100000",
            "API_AUTH_LIMIT": "1000",
            "MCMUSIC_NO_BOT": "1",
            "PORT": str(port),
            "PYTHONUNBUFFERED": "1",
            "PYTHONPATH": str(ROOT / "src"),
        })
        self._log = open(self.log_path, "w")
        self.proc = subprocess.Popen(
            [sys.executable, str(HERE / "fixture_server.py")],
            env=env, stdout=self._log, stderr=subprocess.STDOUT, text=True,
        )
        self.base = f"http://127.0.0.1:{port}"
        self._wait_ready()
        return self

    def _wait_ready(self) -> None:
        deadline = time.time() + 30
        last = ""
        while time.time() < deadline:
            if self.proc.poll() is not None:
                break
            try:
                with urllib.request.urlopen(f"{self.base}/api/version", timeout=2) as res:
                    if res.status == 200:
                        return
            except (urllib.error.URLError, OSError, TimeoutError) as exc:
                last = str(exc)
            time.sleep(0.2)
        log = ""
        if self._log is not None:
            self._log.flush()
            try:
                log = self.log_path.read_text()[-4000:]
            except OSError:
                log = ""
        self.stop()
        raise RuntimeError(f"fixture server never answered ({last})\n{log}")

    def stop(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
        if self._log is not None:
            self._log.close()
            self._log = None
        shutil.rmtree(self.tmp, ignore_errors=True)

    def __enter__(self) -> "ThrowawayServer":
        return self.start()

    def __exit__(self, *_exc) -> None:
        self.stop()


# --------------------------------------------------------------------------- script mode
def seed() -> None:
    """Insert a library row for a real (empty) file on disk.

    The row's mtime matches the file, so a rescan leaves it untouched and the
    seeded metadata survives; deleting the file is what makes a rescan drop it,
    which is the scan assertion both suites make.
    """
    full = os.path.join(MUSIC_DIR, SEED_PATH)
    with open(full, "wb"):
        pass
    with mcmusic.app.app_context():
        c = _db()
        c.execute(
            "insert or ignore into tracks(path,title,artist,album,track_no,genre,"
            "year,duration,mtime,added) values(?,?,?,?,?,?,?,?,?,?)",
            (SEED_PATH, "Seeded Song", "Test Artist", "Test Album", 1, "",
             "2026", 180.0, os.path.getmtime(full), time.time()),
        )
        c.commit()
        row = c.execute("select id from tracks where path=?", (SEED_PATH,)).fetchone()
        print(f"SEEDED {row['id']}", flush=True)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    import mcmusic  # noqa: E402  (imports config, initialises the schema, runs boot())
    from config import MUSIC_DIR  # noqa: E402
    from database import _db  # noqa: E402
    from werkzeug.serving import make_server

    seed()
    port = int(os.environ["PORT"])
    srv = make_server("127.0.0.1", port, mcmusic.app, threaded=True)
    print(f"READY {port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass

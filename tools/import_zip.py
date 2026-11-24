#!/usr/bin/env python3
"""Import MP3s from a ZIP into the server library (server-side only).

See src/zip_import.py for the importer itself. Example:

    python tools/import_zip.py tracks.zip --dry-run
    python tools/import_zip.py tracks.zip
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from zip_import import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

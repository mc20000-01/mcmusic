"""Keep the test suite away from the operator's live database.

``database.DB_PATH`` is computed once at import time. Several test modules used
to set ``DATA_DIR`` themselves, but any module imported earlier could pin the
path to the real ``data/mcmusic.db`` first. Set an isolated directory before
collection so no test can delete or mutate live accounts (including the ones
protected by ``DO_NOT_DELETE`` notes).
"""
import atexit
import os
import shutil
import tempfile

if not os.environ.get("DATA_DIR"):
    _TEST_DATA_DIR = tempfile.mkdtemp(prefix="mcmusic-tests-")
    os.environ["DATA_DIR"] = _TEST_DATA_DIR
    atexit.register(shutil.rmtree, _TEST_DATA_DIR, True)

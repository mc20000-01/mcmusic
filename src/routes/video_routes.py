"""Locally cached music videos for native clients.

No YouTube iframe is involved: the app plays the same file the request cached,
so the picture follows the library track. Copies expire four hours after the
last time they were viewed.
"""
from flask import Blueprint, jsonify, request, send_file

from auth import login_required
import video_cache

bp = Blueprint("video_api", __name__)


@bp.get("/api/videos")
@login_required
def videos_list():
    return jsonify(videos=video_cache.listing(), ttl=video_cache.TTL_SECONDS)


@bp.get("/api/videos/<vid>")
@login_required
def videos_status(vid):
    prepare = str(request.args.get("prepare", "")) in ("1", "true", "yes")
    return jsonify(video_cache.status(vid, prepare=prepare))


@bp.post("/api/videos/<vid>/prepare")
@login_required
def videos_prepare(vid):
    return jsonify(video_cache.status(vid, prepare=True))


@bp.get("/video-cache/<vid>.mp4")
@login_required
def videos_stream(vid):
    path = video_cache.path(vid)
    if not path:
        return jsonify(error="video not cached"), 404
    return send_file(path, conditional=True, mimetype="video/mp4")

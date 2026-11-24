"""Route blueprint registration."""
from .auth_routes import bp as auth_bp
from .library_routes import bp as library_bp
from .personal_routes import bp as personal_bp
from .system_routes import bp as system_bp
from .channel_routes import bp as channel_bp
from .video_routes import bp as video_bp

__all__ = ["auth_bp", "library_bp", "personal_bp", "system_bp", "channel_bp", "video_bp"]

"""Routes package initialization."""
from .api import api_bp
from . import socketio_events

__all__ = ['api_bp', 'socketio_events']

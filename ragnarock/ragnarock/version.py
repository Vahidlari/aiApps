"""Version information for the RAG system package."""

try:
    from ._version import __version__, __version_info__
except ImportError:
    # Fallback for development/editable installs
    __version__ = "0.1.0-dev"
    __version_info__ = (0, 1, 0, "dev")

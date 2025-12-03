"""
Behaverse Data Downloader

A Python package for downloading and managing data from the Behaverse API.

Versioning: CalVer format vYY.MMDD[.dev#]
- Stable releases: v25.1202 (December 2, 2025)
- Development versions: v25.1202.dev1 (first dev iteration on that date)
"""

__version__ = "25.1202"
__author__ = "Behaverse"
__email__ = "pedro@xcit.org"

from .manager import BehaverseDataDownloader

__all__ = ["BehaverseDataDownloader"]
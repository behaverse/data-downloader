"""
Behaverse Data Downloader Commands

Command Pattern implementation for the BDD CLI.
Each command is implemented in its own module.
"""

from .base import BaseCommand
from .study import StudyCommand
from .remote import RemoteCommand
from .config import ConfigCommand
from .status import StatusCommand
from .log import LogCommand
from .download import DownloadCommand
from .fetch import FetchCommand
from .rm import RmCommand
from .test_connection import TestConnectionCommand

__all__ = [
    'BaseCommand',
    'StudyCommand',
    'RemoteCommand',
    'ConfigCommand',
    'StatusCommand',
    'LogCommand',
    'DownloadCommand',
    'FetchCommand',
    'RmCommand',
    'TestConnectionCommand',
]

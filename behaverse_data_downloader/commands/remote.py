"""Remote Command - List available studies from API"""

from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class RemoteCommand(BaseCommand):
    """List all studies available from API"""
    
    @property
    def name(self) -> str:
        return 'remote'
    
    @property
    def help(self) -> str:
        return 'List all studies available from API'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        # No additional arguments needed
        pass
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        print("Available studies:")
        studies = downloader.get_studies()
        for study in studies:
            print(f"  - {study}")
        return 0

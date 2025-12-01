"""Status Command - Show study information"""

from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class StatusCommand(BaseCommand):
    """Show study information"""
    
    @property
    def name(self) -> str:
        return 'status'
    
    @property
    def help(self) -> str:
        return 'Show study information'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('study', help='Study name')
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        study_name = args.study
        print(f"Study: {study_name}")
        info = downloader.get_study_info(study_name)
        print(f"  Status: {info['status']}")
        print(f"  Local events: {info['local_events']}")
        if info['last_update']:
            print(f"  Last update: {info['last_update']}")
        return 0

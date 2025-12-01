"""Fetch Command - Check for new events available remotely"""

from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class FetchCommand(BaseCommand):
    """Check for new events available remotely"""
    
    @property
    def name(self) -> str:
        return 'fetch'
    
    @property
    def help(self) -> str:
        return 'Check for new events available remotely'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('study', help='Study name')
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        study_name = args.study
        print(f"Checking for updates: {study_name}")
        
        result = downloader.check_updates(study_name)
        
        if 'error' in result:
            print(f"✗ Error: {result['error']}")
            return 1
        
        print(f"\n  Local events:  {result['local_count']}")
        print(f"  Remote events: {result['remote_count']}")
        print(f"  New available: {result['new_events_available']}")
        
        if result['has_updates']:
            print(f"\n✓ Updates available! Run 'bdd download {study_name}' to get new events.")
        else:
            print(f"\n✓ No new events available. Local data is up to date.")
        
        return 0

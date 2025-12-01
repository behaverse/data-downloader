"""Download Command - Download study data"""

from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class DownloadCommand(BaseCommand):
    """Download study data (incremental by default)"""
    
    @property
    def name(self) -> str:
        return 'download'
    
    @property
    def help(self) -> str:
        return 'Download study data (incremental by default)'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('study', help='Study name to download')
        parser.add_argument('--fresh', '-f', action='store_true',
                          help='Download all events from scratch (ignore local data)')
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        study_name = args.study
        # Incremental is now the default behavior
        incremental = not (hasattr(args, 'fresh') and args.fresh)
        
        print(f"Downloading study: {study_name}")
        if args.fresh:
            print("Using fresh download mode (ignoring local data)...")
        else:
            print("Using incremental update mode (default)...")
        
        def progress_callback(progress):
            print(f"  Page {progress.get('page', '?')}: "
                  f"{progress.get('events_in_page', 0)} events "
                  f"(Total: {progress.get('total_events', 0)})")
        
        result = downloader.download_study(
            study_name, 
            incremental=incremental,
            progress_callback=progress_callback
        )
        
        if result['success']:
            print(f"✓ {result['message']}")
            if result['save_path']:
                print(f"  Saved to: {result['save_path']}")
            return 0
        else:
            print(f"✗ Download failed: {result['message']}")
            return 1

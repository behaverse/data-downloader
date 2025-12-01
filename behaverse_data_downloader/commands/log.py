"""Log Command - Show download history"""

import json
from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class LogCommand(BaseCommand):
    """Show download history"""
    
    @property
    def name(self) -> str:
        return 'log'
    
    @property
    def help(self) -> str:
        return 'Show download history'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('study', help='Study name')
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        study_name = args.study
        print(f"Download history for: {study_name}")
        
        # Try to load metadata and history
        data_dir = downloader.get_data_directory()
        study_dir = Path(data_dir) / study_name
        
        metadata_file = study_dir / ".metadata.json"
        history_file = study_dir / ".download_history.json"
        
        if not study_dir.exists():
            print(f"  No data found for study '{study_name}'")
        else:
            # Show metadata
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                print(f"\nMetadata:")
                print(f"  Total events: {metadata.get('total_events', 'unknown')}")
                print(f"  First download: {metadata.get('first_download', 'unknown')}")
                print(f"  Last updated: {metadata.get('last_updated', 'unknown')}")
                print(f"  Storage format: {metadata.get('storage_format', 'unknown')}")
            
            # Show download history
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
                print(f"\nDownload History ({len(history)} downloads):")
                for i, record in enumerate(history, 1):
                    print(f"  {i}. {record['timestamp']}")
                    print(f"     Type: {record['download_type']}")
                    print(f"     Events: {record['events_downloaded']}")
            else:
                print("  No download history found")
        
        return 0

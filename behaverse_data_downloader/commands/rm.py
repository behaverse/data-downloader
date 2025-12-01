"""Rm Command - Delete local study data"""

from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class RmCommand(BaseCommand):
    """Delete local study data"""
    
    @property
    def name(self) -> str:
        return 'rm'
    
    @property
    def help(self) -> str:
        return 'Delete local study data'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('study', help='Study name')
        parser.add_argument('--force', '-f', action='store_true',
                          help='Skip confirmation prompt')
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        study_name = args.study
        
        # Check if data exists
        data_dir = Path(downloader.get_data_directory())
        study_dir = data_dir / study_name
        
        if not study_dir.exists():
            print(f"✗ No local data found for study: {study_name}")
            return 1
        
        # Confirm deletion unless --force is used
        if not args.force:
            response = input(f"Are you sure you want to delete all data for '{study_name}'? [y/N]: ")
            if response.lower() not in ['y', 'yes']:
                print("Deletion cancelled.")
                return 0
        
        result = downloader.delete_study_data(study_name)
        
        if result['success']:
            print(f"✓ {result['message']}")
            if 'deleted_path' in result:
                print(f"  Deleted: {result['deleted_path']}")
            return 0
        else:
            print(f"✗ {result['message']}")
            return 1

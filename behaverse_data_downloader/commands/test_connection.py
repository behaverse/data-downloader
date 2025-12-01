"""TestConnection Command - Test API connection"""

from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class TestConnectionCommand(BaseCommand):
    """Test API connection"""
    
    @property
    def name(self) -> str:
        return 'test-connection'
    
    @property
    def help(self) -> str:
        return 'Test API connection'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        # No additional arguments needed
        pass
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        print("Testing API connection...")
        if downloader.test_connection():
            print("✓ Connection successful!")
            return 0
        else:
            print("✗ Connection failed. Check your API key.")
            return 1

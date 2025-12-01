"""Remote Command - Manage remote API endpoints"""

import json
from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class RemoteCommand(BaseCommand):
    """Manage remote API endpoints"""
    
    @property
    def name(self) -> str:
        return 'remote'
    
    @property
    def help(self) -> str:
        return 'Manage remote API endpoints'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        # Create subparsers for remote subcommands
        subparsers = parser.add_subparsers(dest='remote_subcommand', help='Remote operations')
        
        # remote list - List available studies from API
        list_parser = subparsers.add_parser('list', help='List studies available from remote API')
        
        # remote show - Show remote endpoint details
        show_parser = subparsers.add_parser('show', help='Show remote endpoint information')
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        subcommand = args.remote_subcommand
        
        # Default to 'list' if no subcommand specified
        if not subcommand:
            subcommand = 'list'
        
        if subcommand == 'list':
            return self._list_studies(downloader)
        elif subcommand == 'show':
            return self._show_remote(downloader)
        else:
            print(f"Unknown remote subcommand: {subcommand}")
            return 1
    
    def _list_studies(self, downloader: Optional[BehaverseDataDownloader]) -> int:
        """List available studies from remote API"""
        print("Studies available from remote API:")
        studies = downloader.get_studies()
        for study in studies:
            print(f"  - {study}")
        return 0
    
    def _show_remote(self, downloader: Optional[BehaverseDataDownloader]) -> int:
        """Show remote endpoint information"""
        config = downloader.get_config()
        api_config = config.get('api', {})
        
        print("Remote API endpoint:")
        print(f"  Base URL: {api_config.get('base_url', 'N/A')}")
        print(f"  Timeout: {api_config.get('timeout', 'N/A')}s")
        
        api_key = api_config.get('api_key', '')
        if api_key:
            if api_key.startswith('${'):
                print(f"  API Key: {api_key} (from environment)")
            else:
                masked_key = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else '***'
                print(f"  API Key: {masked_key}")
        else:
            print(f"  API Key: ✗ not configured")
        
        # Test connection
        print(f"\n  Testing connection...")
        if downloader.test_connection():
            print(f"  ✓ Connection successful")
        else:
            print(f"  ✗ Connection failed")
        
        return 0

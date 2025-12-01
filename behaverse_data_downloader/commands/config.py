"""Config Command - Manage app-level configuration"""

import json
from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class ConfigCommand(BaseCommand):
    """Manage app-level configuration (storage, cache, defaults)"""
    
    @property
    def name(self) -> str:
        return 'config'
    
    @property
    def help(self) -> str:
        return 'Show or modify app-level configuration'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        # Create subparsers for config subcommands
        subparsers = parser.add_subparsers(dest='config_subcommand', help='Config operations')
        
        # config show - Show current app config
        show_parser = subparsers.add_parser('show', help='Show current app configuration')
        
        # config get - Get a specific config value
        get_parser = subparsers.add_parser('get', help='Get a configuration value')
        get_parser.add_argument('key', help='Config key (e.g., storage.data_directory)')
        
        # config set - Set a config value
        set_parser = subparsers.add_parser('set', help='Set a configuration value')
        set_parser.add_argument('key', help='Config key (e.g., storage.data_directory)')
        set_parser.add_argument('value', help='New value')
    
    def requires_downloader(self) -> bool:
        return False
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        subcommand = args.config_subcommand
        
        # Default to 'show' if no subcommand specified
        if not subcommand:
            subcommand = 'show'
        
        if subcommand == 'show':
            return self._show_config()
        elif subcommand == 'get':
            return self._get_config(args.key)
        elif subcommand == 'set':
            return self._set_config(args.key, args.value)
        else:
            print(f"Unknown config subcommand: {subcommand}")
            return 1
    
    def _show_config(self) -> int:
        """Show current app configuration"""
        config_file = Path("settings/default_config.json")
        
        if not config_file.exists():
            print(f"✗ App configuration not found: {config_file}")
            return 1
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print("App Configuration:")
            print(f"  Config file: {config_file}")
            print(f"\n  API (defaults):")
            print(f"    Base URL: {config.get('api', {}).get('base_url', 'N/A')}")
            print(f"    Timeout: {config.get('api', {}).get('timeout', 'N/A')}s")
            
            print(f"\n  Storage:")
            print(f"    Data directory: {config.get('storage', {}).get('data_directory', 'N/A')}")
            print(f"    Default format: {config.get('storage', {}).get('default_format', 'N/A')}")
            print(f"    Organization: {config.get('storage', {}).get('default_organization', 'N/A')}")
            
            print(f"\n  Download (defaults):")
            print(f"    Page size: {config.get('download', {}).get('default_page_size', 'N/A')}")
            
            return 0
        except Exception as e:
            print(f"✗ Error reading configuration: {e}")
            return 1
    
    def _get_config(self, key: str) -> int:
        """Get a specific config value"""
        config_file = Path("settings/default_config.json")
        
        if not config_file.exists():
            print(f"✗ App configuration not found: {config_file}")
            return 1
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Navigate nested keys (e.g., "storage.data_directory")
            keys = key.split('.')
            value = config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    print(f"✗ Configuration key not found: {key}")
                    return 1
            
            print(value)
            return 0
        except Exception as e:
            print(f"✗ Error reading configuration: {e}")
            return 1
    
    def _set_config(self, key: str, value: str) -> int:
        """Set a config value"""
        config_file = Path("settings/default_config.json")
        
        if not config_file.exists():
            print(f"✗ App configuration not found: {config_file}")
            return 1
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Navigate nested keys and set value
            keys = key.split('.')
            current = config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Try to parse value as JSON (for numbers, booleans, etc.)
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError:
                # If not valid JSON, treat as string
                parsed_value = value
            
            current[keys[-1]] = parsed_value
            
            # Save config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✓ Set {key} = {parsed_value}")
            return 0
        except Exception as e:
            print(f"✗ Error setting configuration: {e}")
            return 1

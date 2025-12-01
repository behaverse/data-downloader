"""Study Command - Manage local study configurations"""

import json
from pathlib import Path
from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class StudyCommand(BaseCommand):
    """Manage local study configurations"""
    
    @property
    def name(self) -> str:
        return 'study'
    
    @property
    def help(self) -> str:
        return 'Manage local study configurations'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        # Create subparsers for study subcommands
        subparsers = parser.add_subparsers(dest='study_subcommand', help='Study operations')
        
        # study list - List all local study configs
        list_parser = subparsers.add_parser('list', help='List all local study configurations')
        
        # study create - Create new study config
        create_parser = subparsers.add_parser('create', help='Create new study configuration')
        create_parser.add_argument('name', help='Study name')
        
        # study show - Show study details
        show_parser = subparsers.add_parser('show', help='Show study configuration details')
        show_parser.add_argument('name', help='Study name')
    
    def requires_downloader(self) -> bool:
        return False
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        subcommand = args.study_subcommand
        
        if not subcommand:
            print("Error: study command requires a subcommand (list, create, show)")
            print("Usage: bdd study {list|create|show}")
            return 1
        
        if subcommand == 'list':
            return self._list_studies()
        elif subcommand == 'create':
            return self._create_study(args.name)
        elif subcommand == 'show':
            return self._show_study(args.name)
        else:
            print(f"Unknown study subcommand: {subcommand}")
            return 1
    
    def _list_studies(self) -> int:
        """List all local study configurations"""
        print("Local study configurations:")
        config_dir = Path("study_configs")
        config_files = sorted(config_dir.glob("*.json"))
        
        for config_file in config_files:
            # Skip template and default
            if config_file.name in ["config_template.json", "default_config.json"]:
                continue
            
            study_name = config_file.stem
            
            # Try to read the config to show API key status
            key_status = "? unknown"
            try:
                with open(str(config_file), 'r') as f:
                    cfg = json.load(f)
                    api_key = cfg.get('api', {}).get('api_key', '')
                    key_status = "✓ has API key" if api_key else "✗ missing API key"
            except Exception as e:
                key_status = f"? error: {type(e).__name__}"
            
            print(f"  - {study_name:30s} {key_status}")
        
        if not config_files:
            print("  (No study configs found. Use 'bdd study create STUDY' to create one)")
        
        return 0
    
    def _create_study(self, study_name: str) -> int:
        """Create new study configuration"""
        config_file = Path(f"study_configs/{study_name}.json")
        
        if config_file.exists():
            print(f"✗ Study configuration already exists: {config_file}")
            return 1
        
        # Create from template
        BehaverseDataDownloader._create_study_config_from_template(study_name, "")
        print(f"✓ Created study configuration: {config_file}")
        print(f"  Edit the file to add your API key for '{study_name}'")
        return 0
    
    def _show_study(self, study_name: str) -> int:
        """Show study configuration details"""
        config_file = Path(f"study_configs/{study_name}.json")
        
        if not config_file.exists():
            print(f"✗ Study configuration not found: {study_name}")
            print(f"  Use 'bdd study create {study_name}' to create it")
            return 1
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"Study configuration: {study_name}")
            print(f"  Config file: {config_file}")
            print(f"  Study name: {config.get('study_name', 'N/A')}")
            print(f"\n  API:")
            print(f"    Base URL: {config.get('api', {}).get('base_url', 'N/A')}")
            api_key = config.get('api', {}).get('api_key', '')
            if api_key:
                # Show partial key for security
                if api_key.startswith('${'):
                    print(f"    API Key: {api_key} (from environment)")
                else:
                    masked_key = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else '***'
                    print(f"    API Key: {masked_key}")
            else:
                print(f"    API Key: ✗ not set")
            print(f"    Timeout: {config.get('api', {}).get('timeout', 'N/A')}s")
            
            print(f"\n  Download:")
            print(f"    Page size: {config.get('download', {}).get('default_page_size', 'N/A')}")
            print(f"    Max concurrent: {config.get('download', {}).get('max_concurrent_requests', 'N/A')}")
            
            print(f"\n  Storage:")
            print(f"    Directory: {config.get('storage', {}).get('data_directory', 'N/A')}")
            print(f"    Format: {config.get('storage', {}).get('default_format', 'N/A')}")
            folder_structure = config.get('storage', {}).get('folder_structure', [])
            if folder_structure:
                print(f"    Organization: {' → '.join(folder_structure)}")
            
            return 0
        except Exception as e:
            print(f"✗ Error reading configuration: {e}")
            return 1

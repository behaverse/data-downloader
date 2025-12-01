"""Config Command - List local study config files"""

import json
from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class ConfigCommand(BaseCommand):
    """List all local study config files"""
    
    @property
    def name(self) -> str:
        return 'config'
    
    @property
    def help(self) -> str:
        return 'List all local study config files'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        # No additional arguments needed
        pass
    
    def requires_downloader(self) -> bool:
        return False
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        print("Available study config files:")
        config_dir = Path("study_configs")
        config_files = sorted(config_dir.glob("*.json"))
        
        for config_file in config_files:
            # Skip template and default
            if config_file.name in ["config_template.json", "default_config.json"]:
                continue
            
            study_name_str = config_file.stem
            
            # Try to read the config to show API key status
            key_status = "? unknown"
            try:
                with open(str(config_file), 'r') as f:
                    cfg = json.load(f)
                    api_key = cfg.get('api', {}).get('api_key', '')
                    key_status = "✓ has API key" if api_key else "✗ missing API key"
            except Exception as e:
                key_status = f"? error: {type(e).__name__}"
            
            print(f"  - {study_name_str:30s} {key_status}")
        
        if not config_files:
            print("  (No study configs found. Use 'bdd create-config STUDY' to create one)")
        
        return 0

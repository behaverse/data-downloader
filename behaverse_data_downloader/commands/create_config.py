"""CreateConfig Command - Create new study config"""

from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class CreateConfigCommand(BaseCommand):
    """Create new study config"""
    
    @property
    def name(self) -> str:
        return 'create-config'
    
    @property
    def help(self) -> str:
        return 'Create new study config'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('study', help='Study name')
    
    def requires_downloader(self) -> bool:
        return False
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        study_name_arg = args.study
        config_file = Path(f"study_configs/{study_name_arg}.json")
        
        if config_file.exists():
            print(f"✗ Config file already exists: {config_file}")
            return 1
        
        # Create from template
        BehaverseDataDownloader._create_study_config_from_template(study_name_arg, "")
        print(f"✓ Created config file: {config_file}")
        print(f"  Edit the file to add your API key for '{study_name_arg}'")
        return 0

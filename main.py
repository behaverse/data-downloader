#!/usr/bin/env python3
"""
Behaverse Data Downloader - Command-Line Interface

Entry point for the Behaverse Data Downloader application.
Provides CLI interface for downloading and managing Behaverse data.

Uses the Command Pattern for extensibility and maintainability.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict

# Add the package to Python path
package_dir = Path(__file__).parent
sys.path.insert(0, str(package_dir))

from behaverse_data_downloader.manager import BehaverseDataDownloader
from behaverse_data_downloader.commands import (
    BaseCommand,
    RemoteCommand,
    ConfigCommand,
    StatusCommand,
    LogCommand,
    DownloadCommand,
    FetchCommand,
    RmCommand,
    TestConnectionCommand,
    CreateConfigCommand,
)


def get_available_commands() -> List[BaseCommand]:
    """
    Get all available commands.
    
    This function provides auto-discovery of commands.
    To add a new command, simply import it above and add it to this list.
    """
    return [
        RemoteCommand(),
        ConfigCommand(),
        StatusCommand(),
        LogCommand(),
        DownloadCommand(),
        FetchCommand(),
        RmCommand(),
        TestConnectionCommand(),
        CreateConfigCommand(),
    ]


def register_commands(subparsers, commands: List[BaseCommand]) -> Dict[str, BaseCommand]:
    """
    Register all commands with the argument parser.
    
    Args:
        subparsers: ArgumentParser subparsers object
        commands: List of command instances
    
    Returns:
        Dictionary mapping command names to command instances
    """
    command_map = {}
    
    for cmd in commands:
        parser = subparsers.add_parser(cmd.name, help=cmd.help)
        cmd.add_arguments(parser)
        command_map[cmd.name] = cmd
    
    return command_map


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        prog='bdd',
        description='Behaverse Data Downloader - Download and manage data from Behaverse API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show help
  bdd help
  
  # List available studies from API (git-style: like 'git remote')
  bdd remote
  
  # Download a study (incremental by default)
  bdd download demo-study
  
  # Download from scratch (ignore local data)
  bdd download demo-study --fresh
  
  # Show study information (git-style: like 'git status')
  bdd status demo-study
  
  # Show download history (git-style: like 'git log')
  bdd log demo-study
  
  # Test API connection
  bdd test-connection
  
  # Check for new events available (git-style: like 'git fetch')
  bdd fetch demo-study
  
  # Delete local study data (git-style: like 'git rm')
  bdd rm demo-study
  
  # List local config files (git-style: like 'git config')
  bdd config
  
  # Create new study config
  bdd create-config my-study

Note: Command names follow git-style conventions for familiarity and ease of use.
      You can also use 'python main.py' or 'behaverse-data-downloader' instead of 'bdd'.
        """
    )
    
    # Global options
    parser.add_argument(
        '--config', '-c',
        metavar='STUDY_NAME',
        help='Use study-specific config file (study_configs/STUDY_NAME.json)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    # Create subparsers for subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # help command (special case, not part of command pattern)
    help_parser = subparsers.add_parser('help', help='Show help message')
    
    # Auto-discover and register all commands
    available_commands = get_available_commands()
    command_map = register_commands(subparsers, available_commands)
    
    args = parser.parse_args()
    
    # If no command or just 'help', show help
    if not args.command or args.command == 'help':
        parser.print_help()
        sys.exit(0)
    
    # Ensure directories exist
    Path("settings").mkdir(parents=True, exist_ok=True)
    Path("study_configs").mkdir(parents=True, exist_ok=True)
    
    try:
        # Get the command instance
        command = command_map.get(args.command)
        
        if not command:
            # Unknown command, show help
            parser.print_help()
            sys.exit(0)
        
        # Determine which config to use
        study_name = None
        config_path = "settings/default_config.json"
        
        if args.config:
            # User specified a study name, use study-specific config
            study_name = args.config
            config_path = f"study_configs/{study_name}.json"
            
            # Create from template if doesn't exist
            if not Path(config_path).exists():
                print(f"Config file for '{study_name}' not found. Creating from template...")
                # We'll let the manager create it with the template
        
        # For download/info/history commands, use study-specific config if available
        target_study = None
        if hasattr(args, 'study'):
            target_study = args.study
            
        if target_study and not args.config:
            study_config_path = Path(f"study_configs/{target_study}.json")
            if study_config_path.exists():
                config_path = str(study_config_path)
                study_name = target_study
                print(f"Using study-specific config: {config_path}")
        
        # Initialize downloader if command requires it
        downloader = None
        if command.requires_downloader():
            downloader = BehaverseDataDownloader(config_path, study_name)
        
        # Execute the command
        exit_code = command.execute(args, downloader)
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
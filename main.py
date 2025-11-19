#!/usr/bin/env python3
"""
Behaverse Data Downloader - Command-Line Interface

Entry point for the Behaverse Data Downloader application.
Provides CLI interface for downloading and managing Behaverse data.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Optional

# Add the package to Python path
package_dir = Path(__file__).parent
sys.path.insert(0, str(package_dir))

from behaverse_data_downloader.manager import BehaverseDataDownloader


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
  
  # List available studies from API
  bdd list-studies
  
  # Download a study (incremental by default)
  bdd download demo-study
  
  # Download from scratch (ignore local data)
  bdd download demo-study --fresh
  
  # Show study information
  bdd info demo-study
  
  # Show download history
  bdd history demo-study
  
  # Test API connection
  bdd test-connection
  
  # Check for new events available
  bdd check-updates demo-study
  
  # Delete local study data
  bdd delete demo-study
  
  # List local config files
  bdd list-configs
  
  # Create new study config
  bdd create-config my-study

Note: You can also use 'python main.py' or 'behaverse-data-downloader' instead of 'bdd'.
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
    
    # help command
    help_parser = subparsers.add_parser('help', help='Show help message')
    
    # list commands
    list_studies_parser = subparsers.add_parser('list-studies', help='List all studies available from API')
    list_configs_parser = subparsers.add_parser('list-configs', help='List all local study config files')
    
    # download command
    download_parser = subparsers.add_parser('download', help='Download study data (incremental by default)')
    download_parser.add_argument('study', help='Study name to download')
    download_parser.add_argument('--fresh', '-f', action='store_true',
                                 help='Download all events from scratch (ignore local data)')
    
    # info command
    info_parser = subparsers.add_parser('info', help='Show study information')
    info_parser.add_argument('study', help='Study name')
    
    # history command
    history_parser = subparsers.add_parser('history', help='Show download history')
    history_parser.add_argument('study', help='Study name')
    
    # test-connection command
    test_parser = subparsers.add_parser('test-connection', help='Test API connection')
    
    # check-updates command
    check_updates_parser = subparsers.add_parser('check-updates', help='Check for new events available remotely')
    check_updates_parser.add_argument('study', help='Study name')
    
    # delete command
    delete_parser = subparsers.add_parser('delete', help='Delete local study data')
    delete_parser.add_argument('study', help='Study name')
    delete_parser.add_argument('--force', '-f', action='store_true',
                               help='Skip confirmation prompt')
    
    # create-config command
    create_parser = subparsers.add_parser('create-config', help='Create new study config')
    create_parser.add_argument('study', help='Study name')
    
    args = parser.parse_args()
    
    # If no command or just 'help', show help
    if not args.command or args.command == 'help':
        parser.print_help()
        sys.exit(0)
    
    # Ensure directories exist
    Path("settings").mkdir(parents=True, exist_ok=True)
    Path("study_configs").mkdir(parents=True, exist_ok=True)
    
    try:
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
        
        # Handle commands that don't need downloader initialization
        if args.command == 'create-config':
            study_name_arg = args.study
            config_file = Path(f"study_configs/{study_name_arg}.json")
            
            if config_file.exists():
                print(f"✗ Config file already exists: {config_file}")
                sys.exit(1)
            
            # Create from template
            BehaverseDataDownloader._create_study_config_from_template(study_name_arg, "")
            print(f"✓ Created config file: {config_file}")
            print(f"  Edit the file to add your API key for '{study_name_arg}'")
            sys.exit(0)
        
        elif args.command == 'list-configs':
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
                        import json as json_mod
                        cfg = json_mod.load(f)
                        api_key = cfg.get('api', {}).get('api_key', '')
                        key_status = "✓ has API key" if api_key else "✗ missing API key"
                except Exception as e:
                    key_status = f"? error: {type(e).__name__}"
                
                print(f"  - {study_name_str:30s} {key_status}")
            
            if not config_files:
                print("  (No study configs found. Use 'bdd create-config STUDY' to create one)")
            sys.exit(0)
        
        # Initialize the downloader for commands that need it
        downloader = BehaverseDataDownloader(config_path, study_name)
        
        # Handle commands that need downloader
        if args.command == 'test-connection':
            print("Testing API connection...")
            if downloader.test_connection():
                print("✓ Connection successful!")
            else:
                print("✗ Connection failed. Check your API key.")
                sys.exit(1)
        
        elif args.command == 'list-studies':
            print("Available studies:")
            studies = downloader.get_studies()
            for study in studies:
                print(f"  - {study}")
        
        elif args.command == 'info':
            study_name = args.study
            print(f"Study: {study_name}")
            info = downloader.get_study_info(study_name)
            print(f"  Status: {info['status']}")
            print(f"  Local events: {info['local_events']}")
            if info['last_update']:
                print(f"  Last update: {info['last_update']}")
        
        elif args.command == 'history':
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
                    import json
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    print(f"\nMetadata:")
                    print(f"  Total events: {metadata.get('total_events', 'unknown')}")
                    print(f"  First download: {metadata.get('first_download', 'unknown')}")
                    print(f"  Last updated: {metadata.get('last_updated', 'unknown')}")
                    print(f"  Storage format: {metadata.get('storage_format', 'unknown')}")
                
                # Show download history
                if history_file.exists():
                    import json
                    with open(history_file, 'r') as f:
                        history = json.load(f)
                    print(f"\nDownload History ({len(history)} downloads):")
                    for i, record in enumerate(history, 1):
                        print(f"  {i}. {record['timestamp']}")
                        print(f"     Type: {record['download_type']}")
                        print(f"     Events: {record['events_downloaded']}")
                else:
                    print("  No download history found")
        
        elif args.command == 'download':
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
            else:
                print(f"✗ Download failed: {result['message']}")
                sys.exit(1)
        
        elif args.command == 'check-updates':
            study_name = args.study
            print(f"Checking for updates: {study_name}")
            
            result = downloader.check_updates(study_name)
            
            if 'error' in result:
                print(f"✗ Error: {result['error']}")
                sys.exit(1)
            
            print(f"\n  Local events:  {result['local_count']}")
            print(f"  Remote events: {result['remote_count']}")
            print(f"  New available: {result['new_events_available']}")
            
            if result['has_updates']:
                print(f"\n✓ Updates available! Run 'bdd download {study_name}' to get new events.")
            else:
                print(f"\n✓ No new events available. Local data is up to date.")
        
        elif args.command == 'delete':
            study_name = args.study
            
            # Check if data exists
            data_dir = Path(downloader.get_data_directory())
            study_dir = data_dir / study_name
            
            if not study_dir.exists():
                print(f"✗ No local data found for study: {study_name}")
                sys.exit(1)
            
            # Confirm deletion unless --force is used
            if not args.force:
                response = input(f"Are you sure you want to delete all data for '{study_name}'? [y/N]: ")
                if response.lower() not in ['y', 'yes']:
                    print("Deletion cancelled.")
                    sys.exit(0)
            
            result = downloader.delete_study_data(study_name)
            
            if result['success']:
                print(f"✓ {result['message']}")
                if 'deleted_path' in result:
                    print(f"  Deleted: {result['deleted_path']}")
            else:
                print(f"✗ {result['message']}")
                sys.exit(1)
        
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
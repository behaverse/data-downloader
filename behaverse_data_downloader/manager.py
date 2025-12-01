#!/usr/bin/env python3
"""
Behaverse Data Downloader

Professional Python application for downloading and managing data from the Behaverse API.
"""

import os
import json
import time
import threading
from typing import Dict, Any, List, Optional, Callable, Iterator
from datetime import datetime
from pathlib import Path

# Import the existing modules with proper relative imports
from .api.client import BehaverseAPIClient, EventData
from .storage.manager import DataStorageManager
from .downloader.manager import DownloadManager


class BehaverseDataDownloader:
    """
    Main downloader class that orchestrates all Behaverse data operations.
    This is the primary interface for downloading and managing Behaverse data.
    """
    
    def __init__(self, config_path: str = "settings/default_config.json", study_name: Optional[str] = None):
        self.config_path = config_path
        self.study_name = study_name
        self.study_configs = {}  # Cache for study-specific configs
        
        # If study_name provided and config doesn't exist, try to create it
        if study_name and not Path(config_path).exists():
            BehaverseDataDownloader._create_study_config_from_template(study_name, "")
        
        self.config = self._load_config()
        
        # Core components
        self.api_client = None
        self.download_manager = None
        self.data_manager = DataStorageManager(self.config)
        
        # State
        self.is_initialized = False
        self.available_studies = []
        
        # Initialize if we have an API key
        self._initialize()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            # Resolve environment variable references in config
            config = self._resolve_env_vars(config)
        except FileNotFoundError:
            # Default configuration
            config = {
                'api': {
                    'base_url': 'https://api.behaverse.org', 
                    'api_key': '', 
                    'timeout': 30
                },
                'storage': {
                    'default_format': 'json', 
                    'default_organization': 'by_study', 
                    'data_directory': 'data'
                },
                'download': {
                    'default_page_size': 1000
                },
                'datasets': {
                    # Dataset-specific configurations
                    # Format: 'dataset_name': {'api_key': 'specific_key', 'description': 'Optional description'}
                }
            }
        
        # Load environment variables
        self._load_env_variables()
        
        # Override with environment variables if available
        api_key = os.getenv('BEHAVERSE_API_KEY')
        if api_key:
            config['api']['api_key'] = api_key
        elif not config['api'].get('api_key'):
            # Fallback to placeholder
            config['api']['api_key'] = 'placeholder_key_required'
        
        # Auto-detect dataset-specific API keys from environment variables
        self._load_dataset_keys_from_env(config)
        
        return config
    
    def _resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve environment variable references in config (${VAR_NAME})"""
        import re
        
        def resolve_value(value):
            if isinstance(value, str):
                # Match ${VAR_NAME} pattern
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                for var_name in matches:
                    env_value = os.getenv(var_name, '')
                    value = value.replace(f'${{{var_name}}}', env_value)
                return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            return value
        
        return resolve_value(config)
    
    def _load_dataset_keys_from_env(self, config: Dict[str, Any]):
        """Load dataset-specific API keys from environment variables"""
        # Look for environment variables that end with _KEY
        for env_var, value in os.environ.items():
            if env_var.endswith('_KEY') and env_var != 'BEHAVERSE_API_KEY' and value.strip():
                # Convert env var name to dataset name
                # e.g., TG_RELEASE_TEST_KEY -> tg_release_test
                dataset_name = env_var[:-4].lower().replace('_', '-')
                
                # Initialize datasets config if not present
                if 'datasets' not in config:
                    config['datasets'] = {}
                
                # Add dataset configuration if not already configured
                if dataset_name not in config['datasets']:
                    config['datasets'][dataset_name] = {
                        'api_key': value.strip(),
                        'description': f'Auto-loaded from {env_var} environment variable'
                    }
                    print(f"Auto-detected API key for dataset '{dataset_name}' from environment variable '{env_var}'")
        
        # Specific handling for known datasets (override generic detection)
        tg_key = os.getenv('TG_RELEASE_TEST_KEY')
        if tg_key:
            if 'datasets' not in config:
                config['datasets'] = {}
            # Remove the generic detection version if it exists
            if 'tg-release-test' in config['datasets']:
                del config['datasets']['tg-release-test']
            # Set the correct dataset name
            config['datasets']['tg_release_test'] = {
                'api_key': tg_key.strip(),
                'description': 'TG Release Test dataset API key from environment'
            }
    
    def _load_env_variables(self):
        """Load environment variables from .env file if available"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            # If python-dotenv is not available, try to load .env manually
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
            except FileNotFoundError:
                pass
    
    def _initialize(self):
        """Initialize the core components"""
        try:
            api_config = self.config.get('api', {})
            api_key = api_config.get('api_key', '')
            
            if api_key:
                self.api_client = BehaverseAPIClient(
                    api_key=api_key,
                    base_url=api_config.get('base_url', 'https://api.behaverse.org'),
                    timeout=api_config.get('timeout', 30)
                )
                self.download_manager = DownloadManager(self.api_client)
                self.is_initialized = True
                
                # Load available studies
                self._refresh_studies()
            
        except Exception as e:
            print(f"Warning: Failed to initialize Behaverse core: {e}")
            # Still partially functional without API
            self.is_initialized = False
    
    def _refresh_studies(self):
        """Refresh the list of available studies"""
        if not self.api_client:
            self.available_studies = ['demo-study']  # Default fallback
            return
        
        try:
            studies = self.api_client.get_studies()
            # Always include demo-study if not present
            if 'demo-study' not in studies:
                studies = ['demo-study'] + studies
            self.available_studies = studies
        except Exception as e:
            print(f"Warning: Failed to fetch studies from API: {e}")
            self.available_studies = ['demo-study']  # Fallback
    
    def _load_study_config(self, study_name: str) -> Optional[Dict[str, Any]]:
        """Load study-specific configuration file"""
        study_config_path = Path("study_configs") / f"{study_name}.json"
        
        if study_config_path.exists():
            try:
                with open(study_config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config for {study_name}: {e}")
        
        return None
    
    @staticmethod
    def _create_study_config_from_template(study_name: str, api_key: str = "") -> Dict[str, Any]:
        """Create a new study config from template"""
        template_path = Path("settings/config_template.json")
        
        # Load template
        if template_path.exists():
            with open(template_path, 'r') as f:
                config = json.load(f)
        else:
            # Minimal template if file doesn't exist
            config = {
                "study_name": "",
                "api": {
                    "base_url": "https://api.behaverse.org",
                    "api_key": "",
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1
                },
                "download": {
                    "default_page_size": 1000,
                    "max_concurrent_requests": 3
                },
                "storage": {
                    "data_directory": "data",
                    "default_format": "json",
                    "organization_mode": "by_study",
                    "folder_structure": ["by_user_id", "by_date"]
                }
            }
        
        # Customize for this study
        config["study_name"] = study_name
        if api_key:
            config["api"]["api_key"] = api_key
        
        # Save to file
        study_config_path = Path("study_configs") / f"{study_name}.json"
        study_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(study_config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Created config file for {study_name} at {study_config_path}")
        return config
    
    def get_study_config(self, study_name: str) -> Dict[str, Any]:
        """Get configuration for a specific study (loads from file or creates from template)"""
        # Check cache first
        if study_name in self.study_configs:
            return self.study_configs[study_name]
        
        # Try to load existing config
        study_config = self._load_study_config(study_name)
        
        if not study_config:
            # Check if we have dataset-specific config in old format
            dataset_config = self.config.get('datasets', {}).get(study_name, {})
            api_key = dataset_config.get('api_key', '')
            
            # Create from template (using staticmethod)
            study_config = BehaverseDataDownloader._create_study_config_from_template(study_name, api_key)
        
        # Cache it
        self.study_configs[study_name] = study_config
        return study_config
    
    def get_api_key_for_dataset(self, dataset_name: str) -> str:
        """
        Get the appropriate API key for a specific dataset
        Priority order:
        1. Environment variable: BEHAVERSE_API_KEY_<STUDY_NAME>
        2. Study-specific config file
        3. Dataset config in main config
        4. Default API key from environment or config
        """
        # Check for study-specific environment variable first
        # Convert study name to env var format: demo-study -> DEMO_STUDY
        env_var_name = f"BEHAVERSE_API_KEY_{dataset_name.upper().replace('-', '_')}"
        study_api_key = os.getenv(env_var_name)
        if study_api_key:
            return study_api_key
        
        # Check if there's a study-specific config file
        study_config = self._load_study_config(dataset_name)
        if study_config:
            api_key = study_config.get('api', {}).get('api_key')
            if api_key:
                return api_key
        
        # Check if dataset has a specific API key configured in old format
        datasets_config = self.config.get('datasets', {})
        if dataset_name in datasets_config:
            dataset_key = datasets_config[dataset_name].get('api_key')
            if dataset_key:
                return dataset_key
        
        # Fall back to default API key from environment or config
        default_key = os.getenv('BEHAVERSE_API_KEY')
        if default_key:
            return default_key
        
        return self.config.get('api', {}).get('api_key', '')
    
    def set_dataset_api_key(self, dataset_name: str, api_key: str, description: str = ""):
        """Set a specific API key for a dataset"""
        if 'datasets' not in self.config:
            self.config['datasets'] = {}
        
        self.config['datasets'][dataset_name] = {
            'api_key': api_key,
            'description': description
        }
        
        # Save configuration
        self.save_config()
    
    def get_dataset_config(self, dataset_name: str) -> Dict[str, Any]:
        """Get the configuration for a specific dataset"""
        datasets_config = self.config.get('datasets', {})
        return datasets_config.get(dataset_name, {})
    
    def remove_dataset_config(self, dataset_name: str):
        """Remove dataset-specific configuration"""
        datasets_config = self.config.get('datasets', {})
        if dataset_name in datasets_config:
            del datasets_config[dataset_name]
            self.save_config()

    def save_config(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save configuration: {e}")
    
    def get_studies(self) -> List[str]:
        """Get list of available studies"""
        return self.available_studies.copy()
    
    def get_study_info(self, study_name: str) -> Dict[str, Any]:
        """Get detailed information about a study"""
        info = {
            'name': study_name,
            'format': self.config['storage']['default_format'],
            'organization': 'by_study',  # Always by_study
            'local_events': 0,
            'last_update': None,
            'has_local_data': False,
            'status': 'No local data'
        }
        
        try:
            # Check for metadata file first (most reliable for hierarchical storage)
            data_dir = Path(self.config['storage']['data_directory'])
            study_dir = data_dir / study_name
            metadata_file = study_dir / '.metadata.json'
            
            if metadata_file.exists():
                import json
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                info['local_events'] = metadata.get('total_events', 0)
                info['last_update'] = metadata.get('last_updated')
                info['has_local_data'] = True
                info['status'] = 'Has local data (can use incremental update)'
                return info
            
            # Fallback: Check for existing data using old method
            last_timestamp = self.data_manager.get_last_timestamp(study_name)
            if last_timestamp:
                info['last_update'] = last_timestamp
                info['has_local_data'] = True
                info['status'] = 'Has local data (can use incremental update)'
            
            # Try to count events if no metadata
            try:
                events = self.data_manager.load_events(study_name)
                info['local_events'] = len(events)
                if not last_timestamp and events:
                    info['has_local_data'] = True
                    info['status'] = 'Has local data files'
            except Exception:
                if last_timestamp:
                    info['status'] = 'Has timestamp but can\'t load events'
                else:
                    # Check if old-style files exist
                    json_file = data_dir / f"{study_name}_events.json"
                    csv_file = data_dir / f"{study_name}_events.csv"
                    
                    if json_file.exists() or csv_file.exists():
                        info['status'] = 'Data files exist but can\'t load'
        
        except Exception as e:
            info['status'] = f'Error checking local data: {e}'
        
        return info
    
    def download_study(
        self, 
        study_name: str, 
        incremental: bool = False,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Download data for a study using dataset-specific API key if configured
        
        Returns:
            Dict with 'success', 'message', 'events_count', 'save_path' keys
        """
        if not self.is_initialized or not self.download_manager:
            return {
                'success': False,
                'message': 'API client not configured',
                'events_count': 0,
                'save_path': None
            }
        
        # Get the appropriate API key for this dataset
        dataset_api_key = self.get_api_key_for_dataset(study_name)
        
        # Create a temporary API client with dataset-specific key if different
        api_client = self.api_client
        temporary_client = False
        
        if dataset_api_key != self.config.get('api', {}).get('api_key', ''):
            # Create temporary API client with dataset-specific key
            api_config = self.config.get('api', {})
            temp_api_client = BehaverseAPIClient(
                api_key=dataset_api_key,
                base_url=api_config.get('base_url', 'https://api.behaverse.org'),
                timeout=api_config.get('timeout', 30)
            )
            # Create temporary download manager
            temp_download_manager = DownloadManager(temp_api_client)
            api_client = temp_api_client
            download_manager = temp_download_manager
            temporary_client = True
        else:
            download_manager = self.download_manager
        
        try:
            events_collected = []
            since_timestamp = None
            
            if incremental:
                since_timestamp = self.data_manager.get_last_timestamp(study_name)
            
            # Download events
            for event in download_manager.download_study_data(
                study_name, 
                progress_callback=progress_callback,
                since_timestamp=since_timestamp
            ):
                events_collected.append(event)
            
            # Save data
            if events_collected:
                save_path = self.data_manager.save_events(
                    events_collected, 
                    study_name,
                    format_type=self.config['storage']['default_format'],
                    organization='by_study'  # Always by_study
                )
                
                return {
                    'success': True,
                    'message': f'Saved {len(events_collected)} events',
                    'events_count': len(events_collected),
                    'save_path': save_path
                }
            else:
                return {
                    'success': True,
                    'message': 'No new events found',
                    'events_count': 0,
                    'save_path': None
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'events_count': 0,
                'save_path': None
            }
    
    def download_study_async(
        self,
        study_name: str,
        incremental: bool = False,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        completion_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> threading.Thread:
        """
        Download data for a study asynchronously
        
        Returns the thread object for monitoring
        """
        def worker():
            result = self.download_study(study_name, incremental, progress_callback)
            if completion_callback:
                completion_callback(result)
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread
    
    def download_all_studies(
        self,
        incremental: bool = True,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Download data for all available studies"""
        results = {}
        
        for study in self.available_studies:
            def study_progress(progress):
                if progress_callback:
                    progress_callback(study, progress)
            
            results[study] = self.download_study(study, incremental, study_progress)
        
        return results
    
    def load_study_events(self, study_name: str) -> List[EventData]:
        """Load events for a study from local storage"""
        return self.data_manager.load_events(study_name)
    
    def export_study_data(
        self,
        study_name: str,
        export_path: str,
        export_format: Optional[str] = None
    ) -> str:
        """Export study data to a specific file"""
        if export_format is None:
            # Detect format from file extension
            extension = Path(export_path).suffix.lower()
            format_map = {'.json': 'json', '.csv': 'csv', '.db': 'sqlite'}
            export_format = format_map.get(extension, 'json')
        
        events = self.load_study_events(study_name)
        if not events:
            raise Exception("No data to export")
        
        # Create temporary data manager for export
        export_dir = os.path.dirname(export_path)
        temp_manager = DataStorageManager({
            'storage': {
                'data_directory': export_dir,
                'default_format': export_format
            }
        })
        
        # Use the basename without extension as study name for export
        export_study_name = os.path.splitext(os.path.basename(export_path))[0]
        
        return temp_manager.save_events(events, export_study_name, export_format)
    
    def get_download_manager(self) -> Optional[DownloadManager]:
        """Get the download manager (for pause/resume/cancel operations)"""
        return self.download_manager
    
    def test_connection(self) -> bool:
        """Test API connection"""
        if not self.api_client:
            return False
        
        try:
            # Use the configured study_name if available
            study_name = self.study_name if self.study_name else 'demo-study'
            return self.api_client.test_connection(study_name)
        except:
            return False
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration and reinitialize if needed"""
        self.config.update(new_config)
        
        # Check if we need to reinitialize
        api_config = self.config.get('api', {})
        current_key = self.api_client.api_key if self.api_client else None
        new_key = api_config.get('api_key', '')
        
        if current_key != new_key:
            self._initialize()
        
        # Update data manager
        self.data_manager = DataStorageManager(self.config)
    
    def get_data_directory(self) -> str:
        """Get the data directory path"""
        return self.config['storage']['data_directory']
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()
    
    def check_updates(self, study_name: str) -> Dict[str, Any]:
        """
        Check if there are new events available remotely
        Returns dict with local_count, remote_count, and new_events_available
        """
        if not self.api_client:
            return {
                'error': 'API client not initialized',
                'local_count': 0,
                'remote_count': 0,
                'new_events_available': 0
            }
        
        # Get the appropriate API key for this dataset (same as download_study)
        dataset_api_key = self.get_api_key_for_dataset(study_name)
        
        # Create a temporary API client with dataset-specific key if different
        api_client = self.api_client
        if dataset_api_key != self.config.get('api', {}).get('api_key', ''):
            # Create temporary API client with dataset-specific key
            api_config = self.config.get('api', {})
            api_client = BehaverseAPIClient(
                api_key=dataset_api_key,
                base_url=api_config.get('base_url', 'https://api.behaverse.org'),
                timeout=api_config.get('timeout', 30)
            )
        
        try:
            # Get remote total count with a minimal query
            data = api_client.get_events_with_offset(study_name, offset=0, limit=1)
            remote_total = data.get('total', 0)
            
            # Get local info
            local_info = self.get_study_info(study_name)
            local_count = local_info.get('local_events', 0)
            
            # Calculate new events
            # Note: This is an approximation since we use deduplication
            # The actual new events might be different
            new_available = max(0, remote_total - local_count)
            
            return {
                'local_count': local_count,
                'remote_count': remote_total,
                'new_events_available': new_available,
                'has_updates': new_available > 0
            }
        except Exception as e:
            return {
                'error': str(e),
                'local_count': 0,
                'remote_count': 0,
                'new_events_available': 0
            }
    
    def delete_study_data(self, study_name: str) -> Dict[str, Any]:
        """
        Delete all local data for a study
        Returns dict with success status and message
        """
        import shutil
        
        data_dir = Path(self.config['storage']['data_directory'])
        study_dir = data_dir / study_name
        
        if not study_dir.exists():
            return {
                'success': False,
                'message': f'No local data found for study: {study_name}'
            }
        
        try:
            # Remove the study directory
            shutil.rmtree(study_dir)
            
            return {
                'success': True,
                'message': f'Successfully deleted data for study: {study_name}',
                'deleted_path': str(study_dir)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deleting study data: {str(e)}'
            }
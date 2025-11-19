"""
Data Storage and Organization System
Handles different storage formats and organization strategies
"""

import json
import csv
import sqlite3
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict

from ..api.client import EventData


class DataStorage:
    """Base class for data storage backends"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_events(self, events: List[EventData], study_name: str, **kwargs) -> str:
        """Save events and return the file path"""
        raise NotImplementedError
    
    def load_events(self, file_path: str) -> List[EventData]:
        """Load events from file"""
        raise NotImplementedError
    
    def load_events_by_study(self, study_name: str) -> List[EventData]:
        """Load events by study name - optional override"""
        raise NotImplementedError
    
    def get_last_timestamp(self, study_name: str) -> Optional[str]:
        """Get the timestamp of the most recent event for incremental updates"""
        raise NotImplementedError


class JSONStorage(DataStorage):
    """JSON file storage backend"""
    
    def save_events(self, events: List[EventData], study_name: str, 
                   organization: str = 'by_study', **kwargs) -> str:
        """Save events to JSON file(s)"""
        
        # Create study directory
        study_dir = self.base_path / study_name
        study_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for folder structure (hierarchical organization)
        folder_structure = kwargs.get('folder_structure', [])
        if folder_structure and isinstance(folder_structure, list) and len(folder_structure) > 0:
            message, new_count = self._save_hierarchical(events, study_dir, folder_structure)
            return message
        
        if organization == 'by_study':
            # Save to data/study_name/events.json
            file_path = study_dir / "events.json"
            new_count = self._save_json_file(events, file_path)
            self._update_metadata(study_dir, new_count)
            return str(file_path)
            
        elif organization == 'by_date':
            files_saved = []
            new_events_total = 0
            events_by_date = self._group_by_date(events)
            
            for date_str, date_events in events_by_date.items():
                file_path = study_dir / f"{date_str}_events.json"
                new_count = self._save_json_file(date_events, file_path)
                new_events_total += new_count
                files_saved.append(str(file_path))
            
            self._update_metadata(study_dir, new_events_total)
            return f"Saved to {len(files_saved)} files in {study_dir}"
            
        elif organization == 'by_event_type':
            files_saved = []
            new_events_total = 0
            events_by_type = self._group_by_event_type(events)
            
            for event_type, type_events in events_by_type.items():
                safe_type = self._safe_filename(event_type)
                file_path = study_dir / f"{safe_type}_events.json"
                new_count = self._save_json_file(type_events, file_path)
                new_events_total += new_count
                files_saved.append(str(file_path))
            
            self._update_metadata(study_dir, new_events_total)
            return f"Saved to {len(files_saved)} files in {study_dir}"
        
        elif organization == 'by_user_id':
            files_saved = []
            new_events_total = 0
            events_by_user = self._group_by_user_id(events)
            
            for user_id, user_events in events_by_user.items():
                safe_user_id = self._safe_filename(user_id)
                file_path = study_dir / f"{safe_user_id}_events.json"
                new_count = self._save_json_file(user_events, file_path)
                new_events_total += new_count
                files_saved.append(str(file_path))
            
            self._update_metadata(study_dir, new_events_total)
            return f"Saved to {len(files_saved)} files in {study_dir}"
            
        else:  # flat
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = study_dir / f"{timestamp}_events.json"
            new_count = self._save_json_file(events, file_path)
            self._update_metadata(study_dir, new_count)
            return str(file_path)
    
    def _save_hierarchical(self, events: List[EventData], study_dir: Path, 
                          hierarchy: List[str]) -> tuple[str, int]:
        """
        Save events with hierarchical organization (e.g., by_user_id -> by_event_type)
        Returns tuple of (message, new_events_count)
        """
        if not hierarchy or len(hierarchy) == 0:
            return ("No hierarchy specified", 0)
        
        files_saved = []
        new_events_total = 0
        
        # First level of hierarchy
        first_level = hierarchy[0]
        if first_level == 'by_user_id':
            groups = self._group_by_user_id(events)
        elif first_level == 'by_date':
            groups = self._group_by_date(events)
        elif first_level == 'by_event_type':
            groups = self._group_by_event_type(events)
        else:
            return (f"Unknown organization mode: {first_level}", 0)
        
        # Process each group
        for group_key, group_events in groups.items():
            safe_key = self._safe_filename(group_key)
            
            if len(hierarchy) == 1:
                # Last level - save file
                file_path = study_dir / f"{safe_key}_events.json"
                new_count = self._save_json_file(group_events, file_path)
                new_events_total += new_count
                files_saved.append(str(file_path))
            else:
                # More levels - create subfolder and recurse
                subfolder = study_dir / safe_key
                subfolder.mkdir(parents=True, exist_ok=True)
                
                # Second level of hierarchy
                second_level = hierarchy[1]
                if second_level == 'by_user_id':
                    subgroups = self._group_by_user_id(group_events)
                elif second_level == 'by_date':
                    subgroups = self._group_by_date(group_events)
                elif second_level == 'by_event_type':
                    subgroups = self._group_by_event_type(group_events)
                else:
                    continue
                
                # Save subgroups
                for subgroup_key, subgroup_events in subgroups.items():
                    safe_subkey = self._safe_filename(subgroup_key)
                    file_path = subfolder / f"{safe_subkey}_events.json"
                    new_count = self._save_json_file(subgroup_events, file_path)
                    new_events_total += new_count
                    files_saved.append(str(file_path))
        
        self._update_metadata(study_dir, new_events_total)
        message = f"Saved to {len(files_saved)} files in {study_dir} (hierarchical: {' -> '.join(hierarchy)})"
        return (message, new_events_total)
    
    def _save_json_file(self, events: List[EventData], file_path: Path) -> int:
        """
        Save events to a single JSON file, merging with existing events if file exists
        Returns the number of NEW events actually added (not duplicates)
        """
        # Load existing events if file exists
        existing_events = []
        existing_event_signatures = set()
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if 'events' in existing_data:
                        existing_events = existing_data['events']
                        # Create signatures for deduplication
                        # Use ID if present and non-empty, otherwise use data content hash
                        for ev in existing_events:
                            event_id = ev.get('id', '')
                            if event_id and event_id != '':
                                existing_event_signatures.add(('id', event_id))
                            else:
                                # For events without ID, use stored timestamp + data hash
                                stored = ev.get('stored_timestamp', '') or ev.get('timestamp', '')
                                data_str = json.dumps(ev.get('data', {}), sort_keys=True)
                                existing_event_signatures.add(('hash', stored + '|' + str(hash(data_str))))
            except (FileNotFoundError, json.JSONDecodeError) as e:
                # If we can't load, just overwrite
                pass
        
        # Merge new events with existing ones (avoid duplicates)
        new_events_to_add = []
        for event in events:
            event_dict = asdict(event)
            event_id = event_dict.get('id', '')
            
            # Create signature for this event
            if event_id and event_id != '':
                signature = ('id', event_id)
            else:
                stored = event_dict.get('stored_timestamp', '') or event_dict.get('timestamp', '')
                data_str = json.dumps(event_dict.get('data', {}), sort_keys=True)
                signature = ('hash', stored + '|' + str(hash(data_str)))
            
            # Only add if not already present
            if signature not in existing_event_signatures:
                new_events_to_add.append(event_dict)
                existing_event_signatures.add(signature)
        
        # Combine existing and new events
        all_events = existing_events + new_events_to_add
        
        data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'total_events': len(all_events),
                'format': 'behaverse_events_v1'
            },
            'events': all_events
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return len(new_events_to_add)
    
    def load_events(self, file_path: str) -> List[EventData]:
        """Load events from JSON file"""
        # Check if file exists first
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load {file_path}: {e}")
            return []
        
        events = []
        for event_dict in data.get('events', []):
            events.append(EventData(**event_dict))
        
        return events
    
    def get_last_timestamp(self, study_name: str) -> Optional[str]:
        """Get the most recent stored timestamp for incremental updates"""
        try:
            study_dir = self.base_path / study_name
            
            # For hierarchical storage we may have many files (user/date subfolders)
            # Walk the study directory and inspect all JSON event files to find
            # the most recent stored_timestamp. This handles flat `events.json`
            # and hierarchical files saved under subfolders.
            if not study_dir.exists():
                return None

            latest_dt = None
            # Consider any JSON file that isn't the metadata or history file
            for path in study_dir.rglob('*.json'):
                if path.name.startswith('.') or path.name in ('.metadata.json', '.download_history.json'):
                    continue

                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    continue

                # Prefer stored timestamps inside events if present
                events_list = []
                if isinstance(data, dict) and 'events' in data and isinstance(data['events'], list):
                    events_list = data['events']
                elif isinstance(data, list):
                    # Some legacy files may be a plain list of events
                    events_list = data

                for ev in events_list:
                    try:
                        st = None
                        # ev may be a dict or already a mapping
                        if isinstance(ev, dict):
                            st = ev.get('stored_timestamp') or ev.get('timestamp')
                        if not st:
                            continue

                        st_dt = datetime.fromisoformat(st.replace('Z', '+00:00'))
                        if latest_dt is None or st_dt > latest_dt:
                            latest_dt = st_dt
                    except Exception:
                        # Ignore unparsable timestamps
                        continue

                # Fallback: consider file-level exported_at in metadata
                if isinstance(data, dict) and 'metadata' in data:
                    exported = data['metadata'].get('exported_at')
                    if exported:
                        try:
                            exp_dt = datetime.fromisoformat(exported.replace('Z', '+00:00'))
                            if latest_dt is None or exp_dt > latest_dt:
                                latest_dt = exp_dt
                        except Exception:
                            pass

            if latest_dt:
                # Return in ISO Z format
                return latest_dt.isoformat().replace('+00:00', 'Z')
            return None
            
        except Exception as e:
            print(f"Error getting last timestamp: {e}")
            return None
    
    def _group_by_date(self, events: List[EventData]) -> Dict[str, List[EventData]]:
        """Group events by date"""
        groups = {}
        for event in events:
            try:
                # Use stored timestamp for grouping
                dt = datetime.fromisoformat(event.stored_timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
                
                if date_str not in groups:
                    groups[date_str] = []
                groups[date_str].append(event)
                
            except (ValueError, AttributeError):
                # If timestamp parsing fails, put in 'unknown' group
                if 'unknown' not in groups:
                    groups['unknown'] = []
                groups['unknown'].append(event)
        
        return groups
    
    def _group_by_event_type(self, events: List[EventData]) -> Dict[str, List[EventData]]:
        """Group events by event type"""
        groups = {}
        for event in events:
            event_type = event.event_type or 'unknown'
            
            if event_type not in groups:
                groups[event_type] = []
            groups[event_type].append(event)
        
        return groups
    
    
    def _group_by_user_id(self, events: List[EventData]) -> Dict[str, List[EventData]]:
        """Group events by user ID"""
        groups = {}
        for event in events:
            user_id = 'unknown'
            
            # Try to extract userId from event data
            if event.data:
                # Check data.base.userId
                if 'base' in event.data and isinstance(event.data['base'], dict):
                    user_id = event.data['base'].get('userId', 'unknown')
                # Check data.object.userId
                elif 'object' in event.data and isinstance(event.data['object'], dict):
                    user_id = event.data['object'].get('userId', 'unknown')
                # Check top-level userId in data
                elif 'userId' in event.data:
                    user_id = event.data['userId']
            
            if user_id not in groups:
                groups[user_id] = []
            groups[user_id].append(event)
        
        return groups

    def _safe_filename(self, name: str) -> str:
        """Convert string to safe filename"""
        import re
        return re.sub(r'[^\w\-_\.]', '_', name)
    
    def _update_metadata(self, study_dir: Path, events_count: int):
        """Update study metadata including download history"""
        metadata_path = study_dir / ".metadata.json"
        download_history_path = study_dir / ".download_history.json"
        
        # Check if this is first download before updating metadata
        is_first_download = not metadata_path.exists()
        
        # Update main metadata
        metadata = {
            'study_name': study_dir.name,
            'last_updated': datetime.now().isoformat(),
            'total_events': events_count,
            'storage_format': 'json'
        }
        
        # Load existing metadata to accumulate total
        if not is_first_download:
            try:
                with open(metadata_path, 'r') as f:
                    old_metadata = json.load(f)
                    # Keep track of total across all downloads
                    metadata['total_events'] = old_metadata.get('total_events', 0) + events_count
                    metadata['first_download'] = old_metadata.get('first_download', metadata['last_updated'])
            except:
                pass
        else:
            metadata['first_download'] = metadata['last_updated']
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update download history
        download_record = {
            'timestamp': datetime.now().isoformat(),
            'events_downloaded': events_count,
            'download_type': 'full' if is_first_download else 'incremental'
        }
        
        history = []
        if download_history_path.exists():
            try:
                with open(download_history_path, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        history.append(download_record)
        
        with open(download_history_path, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_events_by_study(self, study_name: str) -> List[EventData]:
        """Load events by study name for JSON storage"""
        study_dir = self.base_path / study_name
        
        # Try new structure first (data/study_name/events.json)
        file_path = study_dir / "events.json"
        if file_path.exists():
            return self.load_events(str(file_path))
        
        # Fall back to old structure (data/study_name_events.json)
        old_file_path = self.base_path / f"{study_name}_events.json"
        if old_file_path.exists():
            return self.load_events(str(old_file_path))
        
        return []


class CSVStorage(DataStorage):
    """CSV file storage backend"""
    
    def save_events(self, events: List[EventData], study_name: str, 
                   organization: str = 'by_study', **kwargs) -> str:
        """Save events to CSV file(s)"""
        
        # Create study directory
        study_dir = self.base_path / study_name
        study_dir.mkdir(parents=True, exist_ok=True)
        
        if organization == 'by_study':
            file_path = study_dir / "events.csv"
            self._save_csv_file(events, file_path)
            self._update_metadata(study_dir, len(events))
            return str(file_path)
            
        elif organization == 'by_date':
            files_saved = []
            events_by_date = self._group_by_date(events)
            
            for date_str, date_events in events_by_date.items():
                file_path = study_dir / f"{date_str}_events.csv"
                self._save_csv_file(date_events, file_path)
                files_saved.append(str(file_path))
            
            self._update_metadata(study_dir, len(events))
            return f"Saved to {len(files_saved)} files in {study_dir}"
            
        elif organization == 'by_event_type':
            files_saved = []
            events_by_type = self._group_by_event_type(events)
            
            for event_type, type_events in events_by_type.items():
                safe_type = self._safe_filename(event_type)
                file_path = study_dir / f"{safe_type}_events.csv"
                self._save_csv_file(type_events, file_path)
                files_saved.append(str(file_path))
            
            self._update_metadata(study_dir, len(events))
            return f"Saved to {len(files_saved)} files in {study_dir}"
        
        elif organization == 'by_user_id':
            files_saved = []
            events_by_user = self._group_by_user_id(events)
            
            for user_id, user_events in events_by_user.items():
                safe_user_id = self._safe_filename(user_id)
                file_path = study_dir / f"{safe_user_id}_events.csv"
                self._save_csv_file(user_events, file_path)
                files_saved.append(str(file_path))
            
            self._update_metadata(study_dir, len(events))
            return f"Saved to {len(files_saved)} files in {study_dir}"
            
        else:  # flat
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = study_dir / f"{timestamp}_events.csv"
            self._save_csv_file(events, file_path)
            self._update_metadata(study_dir, len(events))
            return str(file_path)
    
    def _save_csv_file(self, events: List[EventData], file_path: Path):
        """Save events to a single CSV file"""
        if not events:
            return
            
        # Convert to DataFrame for easier CSV handling
        df = pd.DataFrame([self._flatten_event(event) for event in events])
        df.to_csv(file_path, index=False, encoding='utf-8')
    
    def _flatten_event(self, event: EventData) -> Dict[str, Any]:
        """Flatten event data for CSV format"""
        flat = {
            'id': event.id,
            'study_name': event.study_name,
            'event_type': event.event_type,
            'element_id': event.element_id,
            'timestamp': event.timestamp,
            'stored_timestamp': event.stored_timestamp,
            'page_url': event.page_url,
        }
        
        # Add flattened data fields
        if event.data:
            for key, value in event.data.items():
                if key not in flat:  # Avoid overwriting main fields
                    flat[f"data_{key}"] = value if not isinstance(value, (dict, list)) else json.dumps(value)
        
        return flat
    
    def load_events(self, file_path: str) -> List[EventData]:
        """Load events from CSV file"""
        # Check if file exists first
        if not os.path.exists(file_path):
            return []
        
        try:
            df = pd.read_csv(file_path)
        except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            print(f"Warning: Could not load {file_path}: {e}")
            return []
        
        events = []
        
        for _, row in df.iterrows():
            # Reconstruct data dict from data_* columns
            data = {}
            for col in df.columns:
                if col.startswith('data_'):
                    key = col[5:]  # Remove 'data_' prefix
                    data[key] = row[col]
            
            event = EventData(
                id=str(row.get('id', '')),
                study_name=str(row.get('study_name', '')),
                event_type=str(row.get('event_type', '')),
                element_id=str(row.get('element_id', '')) if pd.notna(row.get('element_id')) else None,
                timestamp=str(row.get('timestamp', '')),
                stored_timestamp=str(row.get('stored_timestamp', '')),
                page_url=str(row.get('page_url', '')) if pd.notna(row.get('page_url')) else None,
                data=data
            )
            events.append(event)
        
        return events
    
    def get_last_timestamp(self, study_name: str) -> Optional[str]:
        """Get the most recent stored timestamp"""
        try:
            study_dir = self.base_path / study_name
            
            # Try new structure first
            file_path = study_dir / "events.csv"
            if not file_path.exists():
                # Try old structure
                file_path = self.base_path / f"{study_name}_events.csv"
            
            if not file_path.exists():
                return None
                
            df = pd.read_csv(file_path)
            if df.empty or 'stored_timestamp' not in df.columns:
                return None
                
            return df['stored_timestamp'].max()
            
        except Exception as e:
            print(f"Error getting last timestamp: {e}")
            return None
    
    def _group_by_date(self, events: List[EventData]) -> Dict[str, List[EventData]]:
        """Group events by date"""
        groups = {}
        for event in events:
            try:
                # Use stored timestamp for grouping
                dt = datetime.fromisoformat(event.stored_timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
                
                if date_str not in groups:
                    groups[date_str] = []
                groups[date_str].append(event)
                
            except (ValueError, AttributeError):
                # If timestamp parsing fails, put in 'unknown' group
                if 'unknown' not in groups:
                    groups['unknown'] = []
                groups['unknown'].append(event)
        
        return groups
    
    def _group_by_event_type(self, events: List[EventData]) -> Dict[str, List[EventData]]:
        """Group events by event type"""
        groups = {}
        for event in events:
            event_type = event.event_type or 'unknown'
            
            if event_type not in groups:
                groups[event_type] = []
            groups[event_type].append(event)
        
        return groups
    
    
    def _group_by_user_id(self, events: List[EventData]) -> Dict[str, List[EventData]]:
        """Group events by user ID"""
        groups = {}
        for event in events:
            user_id = 'unknown'
            
            # Try to extract userId from event data
            if event.data:
                # Check data.base.userId
                if 'base' in event.data and isinstance(event.data['base'], dict):
                    user_id = event.data['base'].get('userId', 'unknown')
                # Check data.object.userId
                elif 'object' in event.data and isinstance(event.data['object'], dict):
                    user_id = event.data['object'].get('userId', 'unknown')
                # Check top-level userId in data
                elif 'userId' in event.data:
                    user_id = event.data['userId']
            
            if user_id not in groups:
                groups[user_id] = []
            groups[user_id].append(event)
        
        return groups

    def _safe_filename(self, name: str) -> str:
        """Convert string to safe filename"""
        import re
        return re.sub(r'[^\w\-_\.]', '_', name)
    
    def _update_metadata(self, study_dir: Path, events_count: int):
        """Update study metadata including download history"""
        metadata_path = study_dir / ".metadata.json"
        download_history_path = study_dir / ".download_history.json"
        
        # Check if this is first download before updating metadata
        is_first_download = not metadata_path.exists()
        
        # Update main metadata
        metadata = {
            'study_name': study_dir.name,
            'last_updated': datetime.now().isoformat(),
            'total_events': events_count,
            'storage_format': 'csv'
        }
        
        # Load existing metadata to accumulate total
        if not is_first_download:
            try:
                with open(metadata_path, 'r') as f:
                    old_metadata = json.load(f)
                    metadata['total_events'] = old_metadata.get('total_events', 0) + events_count
                    metadata['first_download'] = old_metadata.get('first_download', metadata['last_updated'])
            except:
                pass
        else:
            metadata['first_download'] = metadata['last_updated']
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update download history
        download_record = {
            'timestamp': datetime.now().isoformat(),
            'events_downloaded': events_count,
            'download_type': 'full' if is_first_download else 'incremental'
        }
        
        history = []
        if download_history_path.exists():
            try:
                with open(download_history_path, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        history.append(download_record)
        
        with open(download_history_path, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_events_by_study(self, study_name: str) -> List[EventData]:
        """Load events by study name for CSV storage"""
        study_dir = self.base_path / study_name
        
        # Try new structure first
        file_path = study_dir / "events.csv"
        if file_path.exists():
            return self.load_events(str(file_path))
        
        # Fall back to old structure
        old_file_path = self.base_path / f"{study_name}_events.csv"
        if old_file_path.exists():
            return self.load_events(str(old_file_path))
        
        return []


class SQLiteStorage(DataStorage):
    """SQLite database storage backend"""
    
    def __init__(self, base_path: str):
        super().__init__(base_path)
        self.db_path = self.base_path / "behaverse_data.db"
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize SQLite database with tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    study_name TEXT NOT NULL,
                    event_type TEXT,
                    element_id TEXT,
                    timestamp TEXT,
                    stored_timestamp TEXT,
                    page_url TEXT,
                    data_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_study_stored 
                ON events(study_name, stored_timestamp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_event_type 
                ON events(event_type)
            ''')
    
    def save_events(self, events: List[EventData], study_name: str, **kwargs) -> str:
        """Save events to SQLite database"""
        
        with sqlite3.connect(self.db_path) as conn:
            for event in events:
                conn.execute('''
                    INSERT OR REPLACE INTO events 
                    (id, study_name, event_type, element_id, timestamp, 
                     stored_timestamp, page_url, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.id,
                    event.study_name,
                    event.event_type,
                    event.element_id,
                    event.timestamp,
                    event.stored_timestamp,
                    event.page_url,
                    json.dumps(event.data) if event.data else None
                ))
        
        return f"Saved {len(events)} events to database: {self.db_path}"
    
    def load_events_by_study(self, study_name: Optional[str] = None) -> List[EventData]:
        """Load events from SQLite database"""
        query = "SELECT * FROM events"
        params = ()
        
        if study_name:
            query += " WHERE study_name = ?"
            params = (study_name,)
        
        query += " ORDER BY stored_timestamp"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            events = []
            for row in cursor:
                data = json.loads(row['data_json']) if row['data_json'] else {}
                
                event = EventData(
                    id=row['id'],
                    study_name=row['study_name'],
                    event_type=row['event_type'],
                    element_id=row['element_id'],
                    timestamp=row['timestamp'],
                    stored_timestamp=row['stored_timestamp'],
                    page_url=row['page_url'],
                    data=data
                )
                events.append(event)
        
        return events
    
    def get_last_timestamp(self, study_name: str) -> Optional[str]:
        """Get the most recent stored timestamp"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT MAX(stored_timestamp) FROM events WHERE study_name = ?",
                (study_name,)
            )
            result = cursor.fetchone()
            return result[0] if result and result[0] else None


class DataStorageManager:
    """Main data management class that coordinates storage backends"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.storage_backends = {
            'json': JSONStorage,
            'csv': CSVStorage,
            'sqlite': SQLiteStorage,
        }
        
        # Initialize default storage backend
        self.default_format = config.get('storage', {}).get('default_format', 'json')
        self.data_directory = config.get('storage', {}).get('data_directory', 'data')
        # Organization mode is always by_study (not user-configurable)
        self.organization_mode = 'by_study'
        self.folder_structure = config.get('storage', {}).get('folder_structure', [])
        
    def get_storage_backend(self, format_type: Optional[str] = None) -> DataStorage:
        """Get storage backend instance"""
        format_type = format_type or self.default_format
        
        if format_type not in self.storage_backends:
            raise ValueError(f"Unsupported format: {format_type}")
        
        backend_class = self.storage_backends[format_type]
        return backend_class(self.data_directory)
    
    def save_events(self, events: List[EventData], study_name: str, 
                   format_type: Optional[str] = None, organization: Optional[str] = None) -> str:
        """Save events using specified format and organization"""
        
        if not events:
            return "No events to save"
        
        format_type = format_type or self.default_format
        organization = organization or self.organization_mode
        
        backend = self.get_storage_backend(format_type)
        return backend.save_events(events, study_name, organization=organization, 
                                   folder_structure=self.folder_structure)
    
    def get_last_timestamp(self, study_name: str, format_type: Optional[str] = None) -> Optional[str]:
        """Get last timestamp for incremental updates"""
        format_type = format_type or self.default_format
        backend = self.get_storage_backend(format_type)
        return backend.get_last_timestamp(study_name)
    
    def load_events(self, study_name: str, format_type: Optional[str] = None) -> List[EventData]:
        """Load events from storage"""
        format_type = format_type or self.default_format
        backend = self.get_storage_backend(format_type)
        
        # Use load_events_by_study method for all backends
        try:
            return backend.load_events_by_study(study_name)
        except Exception as e:
            print(f"Warning: Could not load events for study '{study_name}': {e}")
            return []
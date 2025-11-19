"""
Behaverse API Client
Handles authentication and data fetching from api.behaverse.org
"""

import requests
import time
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Generator, Callable
from dataclasses import dataclass, asdict


@dataclass
class EventData:
    """Represents a single event from Behaverse API"""
    id: str
    study_name: str
    event_type: str
    element_id: Optional[str]
    timestamp: str
    stored_timestamp: str
    page_url: Optional[str]
    data: Dict[str, Any]
    
    @classmethod
    def from_api_response(cls, study_name: str, event_dict: Dict[str, Any]) -> 'EventData':
        """Create EventData from API response format"""
        # Extract timestamp from various possible locations
        timestamp = ''
        stored_timestamp = ''
        event_id = ''
        event_type = ''
        
        # CRITICAL: Always prefer top-level 'stored' field for stored_timestamp
        # This is the API's authoritative timestamp for when the event was stored
        # and MUST be used for incremental downloads (get_events_since filtering)
        if 'stored' in event_dict:
            stored_timestamp = event_dict['stored']
        
        # Try standard fields for timestamp (event generation time)
        if 'timestamp' in event_dict:
            timestamp = event_dict['timestamp']
            if not stored_timestamp:
                stored_timestamp = event_dict.get('stored_timestamp', timestamp)
        
        # Try nested timestamp fields (for tg_release_test format)
        elif 'object' in event_dict and isinstance(event_dict['object'], dict):
            timestamp = event_dict['object'].get('tsGenerated', '')
            event_id = event_dict['object'].get('userId', '') + '_' + str(event_dict['object'].get('index', ''))
            # Only use tsGenerated for stored_timestamp if no top-level 'stored' exists
            if not stored_timestamp:
                stored_timestamp = timestamp
        elif 'base' in event_dict and isinstance(event_dict['base'], dict):
            timestamp = event_dict['base'].get('tsGenerated', '')
            event_id = event_dict['base'].get('userId', '') + '_' + str(event_dict['base'].get('index', ''))
            # Only use tsGenerated for stored_timestamp if no top-level 'stored' exists
            if not stored_timestamp:
                stored_timestamp = timestamp
        
        # If still no timestamp, use stored as fallback
        if not timestamp and stored_timestamp:
            timestamp = stored_timestamp
        
        # Try types for event type
        if 'types' in event_dict and isinstance(event_dict['types'], list) and event_dict['types']:
            event_type = event_dict['types'][0]  # Use first type
        elif 'event_type' in event_dict:
            event_type = event_dict['event_type']
        
        # Use standard ID if available
        if not event_id:
            event_id = event_dict.get('id', timestamp)
        
        return cls(
            id=event_id,
            study_name=study_name,
            event_type=event_type,
            element_id=event_dict.get('element_id'),
            timestamp=timestamp,
            stored_timestamp=stored_timestamp,
            page_url=event_dict.get('page_url'),
            data=event_dict  # Store the entire event as data
        )


class BehaverseAPIClient:
    """Client for interacting with Behaverse API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.behaverse.org", 
                 timeout: int = 30, max_retries: int = 3, retry_delay: float = 1.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with retries and error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method, url, timeout=self.timeout, **kwargs
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise Exception(f"Failed after {self.max_retries + 1} attempts: {str(e)}")
                
                print(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))
                    
        raise Exception("Unexpected error in request retry loop")
    
    def test_connection(self, study_name: str = 'demo-study') -> bool:
        """Test if API key is valid and connection works"""
        try:
            # Test with specified study using offset-based pagination
            response = self._make_request('GET', f'/v1/studies/{study_name}/events?offset=0&limit=1')
            return response.status_code == 200
        except Exception:
            return False
    
    def get_studies(self) -> List[str]:
        """Get list of available studies"""
        # Since the API doesn't have a studies endpoint, return known studies
        # In a real implementation, this would need to be configured by the user
        # or discovered through some other means
        return ['demo-study']  # Return the known working study
    
    def get_events_page(self, study_name: str, page: int = 1, 
                       page_size: int = 1000) -> Dict[str, Any]:
        """Get a single page of events for a study (deprecated - use offset-based)"""
        # Convert page to offset for backward compatibility
        offset = (page - 1) * page_size
        params = {
            'offset': offset,
            'limit': page_size
        }
        
        endpoint = f'/v1/studies/{study_name}/events'
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def get_events_with_offset(self, study_name: str, offset: int = 0, 
                              limit: int = 1000) -> Dict[str, Any]:
        """Get events using offset-based pagination"""
        params = {
            'offset': offset,
            'limit': limit
        }
        
        endpoint = f'/v1/studies/{study_name}/events'
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def get_all_events(self, study_name: str, page_size: int = 1000, 
                      progress_callback: Optional[Callable] = None) -> Generator[EventData, None, None]:
        """
        Get all events for a study with offset-based pagination
        Yields EventData objects one at a time
        """
        offset = 0
        total_events = 0
        
        while True:
            try:
                data = self.get_events_with_offset(study_name, offset, page_size)
                events = data.get('events', [])
                total_count = data.get('total', 0)
                
                if not events:
                    break
                
                # Process events
                for event_dict in events:
                    event = EventData.from_api_response(study_name, event_dict)
                    total_events += 1
                    yield event
                
                # Update progress
                if progress_callback:
                    progress_callback({
                        'page': offset // page_size + 1,
                        'events_in_page': len(events),
                        'total_events': total_events,
                        'total_available': total_count,
                        'study_name': study_name
                    })
                
                # Check if we've retrieved all events
                offset += len(events)
                if offset >= total_count or len(events) < page_size:
                    break
                
            except Exception as e:
                print(f"Error at offset {offset}: {e}")
                break
    
    def get_events_since(self, study_name: str, since_timestamp: str, 
                        page_size: int = 1000) -> Generator[EventData, None, None]:
        """
        Get events that occurred after a specific timestamp
        This is useful for incremental updates
        """
        since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
        
        for event in self.get_all_events(study_name, page_size):
            try:
                # Parse stored timestamp (when event was stored in API)
                stored_dt = datetime.fromisoformat(
                    event.stored_timestamp.replace('Z', '+00:00')
                )
                
                if stored_dt > since_dt:
                    yield event
                    
            except (ValueError, AttributeError) as e:
                # If timestamp parsing fails, include the event to be safe
                print(f"Warning: Could not parse timestamp for event {event.id}: {e}")
                yield event
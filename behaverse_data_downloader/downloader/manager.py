#!/usr/bin/env python3
"""
Download Manager Module

This module provides the DownloadManager class for coordinating downloads from the Behaverse API.
It handles pagination, progress callbacks, and download state management (pause/resume/cancel).
"""

import time
import threading
from typing import Iterator, Dict, Any, Callable, Optional
from ..api.client import BehaverseAPIClient, EventData
from ..storage.manager import DataStorageManager


class DownloadManager:
    """Manages downloads from the Behaverse API with pause/resume/cancel functionality"""
    
    def __init__(self, api_client: BehaverseAPIClient):
        self.api_client = api_client
        self.is_paused = False
        self.is_cancelled = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # Start unpaused
    
    def pause(self):
        """Pause the current download"""
        self.is_paused = True
        self._pause_event.clear()
    
    def resume(self):
        """Resume a paused download"""
        self.is_paused = False
        self._pause_event.set()
    
    def cancel(self):
        """Cancel the current download"""
        self.is_cancelled = True
        self._pause_event.set()  # Unblock if paused
    
    def download_study_data(
        self, 
        study_name: str, 
        page_size: int = 1000,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        since_timestamp: Optional[str] = None
    ) -> Iterator[EventData]:
        """
        Download data for a study with pagination, pause/resume/cancel support
        
        Args:
            study_name: Name of the study to download
            page_size: Number of events per page
            progress_callback: Function to call with progress updates
            since_timestamp: Only download events after this timestamp
            
        Yields:
            EventData objects for each event downloaded
            
        Raises:
            Exception: If download is cancelled or API error occurs
        """
        if since_timestamp:
            # Use the get_events_since method for incremental updates
            total_events = 0
            for event in self.api_client.get_events_since(study_name, since_timestamp, page_size):
                # Check if cancelled
                if self.is_cancelled:
                    raise Exception("Download cancelled by user")
                
                # Wait if paused
                self._pause_event.wait()
                
                # Check if cancelled again after unpausing
                if self.is_cancelled:
                    raise Exception("Download cancelled by user")
                
                total_events += 1
                if progress_callback:
                    progress_callback({
                        'study_name': study_name,
                        'page': 'incremental',
                        'events_in_page': 1,
                        'total_events': total_events
                    })
                
                yield event
        else:
            # Full download with pagination
            page = 1
            total_events = 0
            
            while True:
                # Check if cancelled
                if self.is_cancelled:
                    raise Exception("Download cancelled by user")
                
                # Wait if paused
                self._pause_event.wait()
                
                # Check if cancelled again after unpausing
                if self.is_cancelled:
                    raise Exception("Download cancelled by user")
                
                try:
                    # Download page of events
                    data = self.api_client.get_events_page(study_name, page, page_size)
                    events = data.get('events', [])
                    
                    # Update progress
                    events_in_page = len(events)
                    total_events += events_in_page
                    
                    if progress_callback:
                        progress_callback({
                            'study_name': study_name,
                            'page': page,
                            'events_in_page': events_in_page,
                            'total_events': total_events
                        })
                    
                    # Process and yield events
                    for event_dict in events:
                        # Check for cancellation even within a page
                        if self.is_cancelled:
                            raise Exception("Download cancelled by user")
                        event = EventData.from_api_response(study_name, event_dict)
                        yield event
                    
                    # If we got fewer events than page size, we're done
                    if events_in_page < page_size:
                        break
                    
                    page += 1
                    
                    # Small delay to prevent overwhelming the API
                    time.sleep(0.1)
                    
                except Exception as e:
                    if self.is_cancelled:
                        raise Exception("Download cancelled by user")
                    else:
                        raise e
    
    def reset_state(self):
        """Reset download state for a new download"""
        self.is_paused = False
        self.is_cancelled = False
        self._pause_event.set()
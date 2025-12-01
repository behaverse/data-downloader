"""
Base Command Class

Provides the base class for all BDD commands following the Command Pattern.
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Optional
from ..manager import BehaverseDataDownloader


class BaseCommand(ABC):
    """
    Base class for all BDD commands.
    
    Each command must implement:
    - name: Command name (e.g., 'remote', 'status')
    - help: Short help text
    - add_arguments: Method to add command-specific arguments to parser
    - execute: Method to execute the command logic
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name (used in CLI)"""
        pass
    
    @property
    @abstractmethod
    def help(self) -> str:
        """Short help text for the command"""
        pass
    
    @abstractmethod
    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Add command-specific arguments to the argument parser.
        
        Args:
            parser: ArgumentParser for this command's subparser
        """
        pass
    
    @abstractmethod
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        """
        Execute the command.
        
        Args:
            args: Parsed command-line arguments
            downloader: BehaverseDataDownloader instance (None for commands that don't need it)
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        pass
    
    def requires_downloader(self) -> bool:
        """
        Whether this command requires a BehaverseDataDownloader instance.
        
        Returns:
            True if command needs downloader, False otherwise
        """
        return True

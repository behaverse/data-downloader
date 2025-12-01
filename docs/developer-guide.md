# Developer Guide: Adding New Commands

This guide explains how to add new commands to the Behaverse Data Downloader using the Command Pattern.

## Architecture Overview

The BDD CLI uses the **Command Pattern** for organizing commands. Each command is:
- Self-contained in its own module
- Implements a consistent interface (`BaseCommand`)
- Automatically discovered and registered at runtime
- Independent and testable

## Command Structure

All commands are located in `behaverse_data_downloader/commands/` and inherit from `BaseCommand`:

```
behaverse_data_downloader/
├── commands/
│   ├── __init__.py          # Exports all commands
│   ├── base.py              # BaseCommand abstract class
│   ├── remote.py            # List studies from API
│   ├── config.py            # List local configs
│   ├── status.py            # Show study info
│   ├── log.py               # Show download history
│   ├── download.py          # Download study data
│   ├── fetch.py             # Check for updates
│   ├── rm.py                # Delete study data
│   ├── test_connection.py  # Test API connection
│   └── create_config.py     # Create study config
```

## BaseCommand Interface

Every command must implement:

### Properties

- **`name`** (str): Command name used in CLI (e.g., 'remote', 'status')
- **`help`** (str): Short help text shown in command list

### Methods

- **`add_arguments(parser)`**: Add command-specific arguments to argparse parser
- **`execute(args, downloader)`**: Execute command logic, return exit code (0 = success)
- **`requires_downloader()`**: Return True if command needs BehaverseDataDownloader instance (default: True)

## Step-by-Step: Adding a New Command

### Step 1: Create Command Module

Create `behaverse_data_downloader/commands/mycommand.py`:

```python
"""MyCommand - Brief description"""

from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class MyCommand(BaseCommand):
    """Detailed description of what this command does"""
    
    @property
    def name(self) -> str:
        return 'mycommand'
    
    @property
    def help(self) -> str:
        return 'Brief help text for command list'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command-specific arguments"""
        parser.add_argument('study', help='Study name')
        parser.add_argument('--option', '-o', help='Optional flag')
    
    def requires_downloader(self) -> bool:
        """Override if command doesn't need downloader"""
        return True  # Default value
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        """Execute the command logic"""
        # Your command implementation here
        print(f"Executing mycommand for {args.study}")
        
        # Use downloader if needed
        if downloader:
            studies = downloader.get_studies()
            print(f"Available studies: {studies}")
        
        # Return exit code (0 = success, non-zero = error)
        return 0
```

### Step 2: Export Command

Add your command to `behaverse_data_downloader/commands/__init__.py`:

```python
from .mycommand import MyCommand

__all__ = [
    # ... existing commands ...
    'MyCommand',
]
```

### Step 3: Register Command

Add to `main.py` in the `get_available_commands()` function:

```python
def get_available_commands() -> List[BaseCommand]:
    return [
        # ... existing commands ...
        MyCommand(),
    ]
```

### Step 4: Test Your Command

```bash
# Test basic execution
bdd mycommand demo-study

# Test with options
bdd mycommand demo-study --option value

# Check help text
bdd --help  # Should show your command in the list
```

## Examples

### Example 1: Simple Command Without Downloader

```python
"""Version Command - Show version information"""

from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class VersionCommand(BaseCommand):
    @property
    def name(self) -> str:
        return 'version'
    
    @property
    def help(self) -> str:
        return 'Show version information'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        pass  # No arguments needed
    
    def requires_downloader(self) -> bool:
        return False  # No API access needed
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        print("Behaverse Data Downloader v1.0.0")
        return 0
```

### Example 2: Command With Multiple Arguments

```python
"""Export Command - Export study data to file"""

from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class ExportCommand(BaseCommand):
    @property
    def name(self) -> str:
        return 'export'
    
    @property
    def help(self) -> str:
        return 'Export study data to file'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('study', help='Study name')
        parser.add_argument('output', help='Output file path')
        parser.add_argument('--format', '-f', 
                          choices=['json', 'csv', 'sqlite'],
                          default='json',
                          help='Export format')
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        print(f"Exporting {args.study} to {args.output} as {args.format}...")
        
        try:
            result = downloader.export_study_data(
                args.study,
                args.output,
                args.format
            )
            print(f"✓ Exported to: {result}")
            return 0
        except Exception as e:
            print(f"✗ Export failed: {e}")
            return 1
```

### Example 3: Composite Command

```python
"""Pull Command - Fetch and download in one step (like git pull)"""

from argparse import ArgumentParser, Namespace
from typing import Optional
from .base import BaseCommand
from ..manager import BehaverseDataDownloader


class PullCommand(BaseCommand):
    """Composite command: fetch + download"""
    
    @property
    def name(self) -> str:
        return 'pull'
    
    @property
    def help(self) -> str:
        return 'Check for updates and download (like git pull)'
    
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument('study', help='Study name')
    
    def execute(self, args: Namespace, downloader: Optional[BehaverseDataDownloader]) -> int:
        study = args.study
        
        # Step 1: Check for updates (like fetch)
        print(f"Checking for updates: {study}")
        result = downloader.check_updates(study)
        
        if 'error' in result:
            print(f"✗ Error: {result['error']}")
            return 1
        
        if not result['has_updates']:
            print("✓ Already up to date.")
            return 0
        
        print(f"New events available: {result['new_events_available']}")
        
        # Step 2: Download (incremental)
        print(f"\nDownloading updates...")
        download_result = downloader.download_study(study, incremental=True)
        
        if download_result['success']:
            print(f"✓ {download_result['message']}")
            return 0
        else:
            print(f"✗ Download failed: {download_result['message']}")
            return 1
```

## Best Practices

### 1. Command Naming
- Use git-style names when applicable (`status`, `log`, `fetch`, `rm`)
- Use clear, action-oriented names (`download`, `export`, `verify`)
- Avoid abbreviations unless they're universally understood

### 2. Help Text
- Keep help text concise (one line for command list)
- Provide detailed descriptions in docstrings
- Include examples in the command's module docstring

### 3. Error Handling
- Always return proper exit codes (0 = success, non-zero = error)
- Print user-friendly error messages
- Use ✓ and ✗ symbols for success/failure messages

### 4. Arguments
- Use consistent naming across commands (`study` for study name)
- Provide short forms for common flags (`-f`, `-v`, `-h`)
- Set reasonable defaults
- Use argparse features (choices, required, default, help)

### 5. Output Format
- Keep output clean and scannable
- Use indentation for hierarchical data
- Show progress for long-running operations
- Use consistent formatting (timestamps, counts, paths)

### 6. Dependencies
- Only require downloader if you need API access
- Don't import heavy dependencies at module level
- Handle missing dependencies gracefully

## Command Lifecycle

1. **Parsing**: argparse creates Namespace with command arguments
2. **Discovery**: `get_available_commands()` returns all command instances
3. **Registration**: `register_commands()` adds commands to argparse subparsers
4. **Initialization**: Downloader initialized if `requires_downloader()` is True
5. **Execution**: `execute()` method called with args and downloader
6. **Exit**: Exit code from `execute()` determines process exit status

## Testing Commands

### Manual Testing
```bash
# Test basic execution
bdd mycommand arg1 arg2

# Test help
bdd mycommand --help

# Test error cases
bdd mycommand invalid-study
```

### Automated Testing
Create `tests/test_mycommand.py`:

```python
import pytest
from behaverse_data_downloader.commands.mycommand import MyCommand

def test_command_name():
    cmd = MyCommand()
    assert cmd.name == 'mycommand'

def test_command_help():
    cmd = MyCommand()
    assert 'brief description' in cmd.help.lower()

def test_command_execution():
    # Your test implementation
    pass
```

## Troubleshooting

### Command Not Found
- Check command is imported in `commands/__init__.py`
- Check command is added to `get_available_commands()` in `main.py`
- Verify class inherits from `BaseCommand`

### AttributeError on downloader
- Check `requires_downloader()` returns True
- Handle `downloader` being None in your code
- Type hint as `Optional[BehaverseDataDownloader]`

### Arguments Not Working
- Check `add_arguments()` implementation
- Verify argument names match usage in `execute()`
- Test with `bdd mycommand --help`

## Advanced Features

### Hierarchical Commands
For complex commands with subcommands (e.g., `bdd remote show`, `bdd remote add`):

```python
class RemoteCommand(BaseCommand):
    def add_arguments(self, parser: ArgumentParser) -> None:
        subparsers = parser.add_subparsers(dest='remote_command')
        
        # remote show
        show = subparsers.add_parser('show')
        show.add_argument('name')
        
        # remote add
        add = subparsers.add_parser('add')
        add.add_argument('name')
        add.add_argument('url')
    
    def execute(self, args, downloader):
        if args.remote_command == 'show':
            return self.show(args, downloader)
        elif args.remote_command == 'add':
            return self.add(args, downloader)
```

### Plugin System (Future)
The command pattern enables third-party plugins:

```python
# ~/.bdd/plugins/myplugin.py
from behaverse_data_downloader.commands import BaseCommand

class MyPluginCommand(BaseCommand):
    # Implementation
    pass
```

## Resources

- [Command Pattern on Refactoring.Guru](https://refactoring.guru/design-patterns/command)
- [argparse Documentation](https://docs.python.org/3/library/argparse.html)
- GitHub Issue #2: [Project Structure] Organize codebase on commands

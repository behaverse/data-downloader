# Behaverse Data Downloader

A lightweight application to facilitate the downloading and local managing of data from [the Behaverse API](https://api.behaverse.org/docs#/).

The Behaverse Data Downloader has three interfaces: 
- a command-line interface (CLI) for direct user interaction
- a programmatic API for integration into Python applications.
- a graphic user interface (GUI) implemented in electron



## About

The Behaverse Data Downloader simplifies the process of downloading data via the API by:

 - Storing config file information (i.e., names of datasets, Access Keys)
 - Allowing you to specify how information is organized and stored locally
 - Organizing data into separate files (by user-id, date, or event type) instead of one massive file
 - Keeping track of the current state of local data and download history
 - Allowing incremental updates (download only new data without re-downloading everything from scratch)
 - Downloading data in smaller packets to prevent interruption issues
 - Providing progress tracking and time estimates
 - Supporting multiple datasets with dataset-specific API keys

### Design Philosophy

The CLI follows **git-style command naming** for familiarity and ease of use. Commands use verbs and patterns inspired by git (e.g., `status`, `log`, `fetch`, `rm`) to make the tool intuitive for developers already familiar with version control systems.

#### Command Pattern Architecture

The codebase uses the **Command Pattern** for extensibility and maintainability:

- **One file per command**: Each CLI command is implemented in its own module under `behaverse_data_downloader/commands/`
- **Auto-discovery**: Commands are automatically registered at startup
- **Consistent interface**: All commands inherit from `BaseCommand` with standardized methods
- **Easy extensibility**: Add new commands by creating a new file and importing it in `commands/__init__.py`
- **Plugin support**: Future support for third-party command plugins
- **Hierarchical commands**: Framework supports composite commands (e.g., `push=fetch+merge`)

**Adding a new command:**
1. Create `behaverse_data_downloader/commands/mycommand.py`
2. Inherit from `BaseCommand` and implement required methods
3. Import your command in `behaverse_data_downloader/commands/__init__.py`
4. Add to the list in `get_available_commands()` in `main.py`




## Quick Start

### Installation

1. **Clone or download** this project
2. **Create and activate virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Linux/Mac
   # or
   .venv\Scripts\activate     # On Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Install the package** (to enable the `bdd` command):
   ```bash
   pip install -e .
   ```
5. **Configure your API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Behaverse API key
   ```

### Usage

**First, activate your virtual environment:**

```bash
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows
```


## Command Line Interface (CLI)

### Git-Style Commands

The `bdd` CLI follows **git-style naming conventions** with hierarchical commands for intuitive use:

| Command | Git Equivalent | Description |
|---------|----------------|-------------|
| `bdd study` | `git branch` | Manage local study configurations (list, create, show) |
| `bdd remote` | `git remote` | Manage remote API endpoints (list studies, show endpoint) |
| `bdd config` | `git config` | Manage app-level configuration (storage, cache, defaults) |
| `bdd status` | `git status` | Show study information and local data status |
| `bdd log` | `git log` | Show download history |
| `bdd fetch` | `git fetch` | Check for new events available remotely |
| `bdd rm` | `git rm` | Delete local study data |

**Key concepts:**
- **study**: Local study configurations (domain objects you work with)
- **remote**: Remote API endpoints and available datasets
- **config**: App-level settings (tool configuration, not study metadata)

This design separates domain objects (studies) from tool configuration, making the CLI more intuitive and extensible.

## CLI Commands

### Getting Help

```bash
# Show all available commands and options
bdd help
bdd --help

# Show version
bdd --version
```

### Study Management (Local Configurations)

```bash
# List all local study configurations
bdd study list

# Create a new study configuration from template
bdd study create my-new-study
# This creates study_configs/my-new-study.json

# Show details of a study configuration
bdd study show demo-study
```

### Remote API Operations

```bash
# List studies available from remote API
bdd remote list

# Show remote API endpoint information
bdd remote show

# Test API connection and authentication
bdd test-connection
```

### App Configuration

```bash
# Show app-level configuration
bdd config show

# Get a specific configuration value
bdd config get storage.data_directory

# Set a configuration value
bdd config set storage.data_directory /path/to/data
bdd config set download.default_page_size 500
```

### Download Data

```bash
# Download study data (incremental by default - only fetches new events)
bdd download demo-study

# Fresh download (download all events from scratch, ignoring local data)
bdd download demo-study --fresh

# Download using explicit config file (optional, auto-detected if study_configs/<study>.json exists)
# Note: Global options like --config must come BEFORE the subcommand
bdd --config demo-study download demo-study
```

**Smart Config Selection:** If you have `study_configs/demo-study.json`, running `bdd download demo-study` automatically uses it. The `--config` flag is only needed if the config filename differs from the study name.

**Note on Flag Order:** Global options (`--config`, `--version`) must be placed **before** the subcommand. Command-specific options (`--fresh`) go **after** the subcommand and study name.

### Local Data Information

```bash
# Show download history for a study (timestamps, event counts, download types)
bdd log demo-study

# Show information about local data (event counts, last update, storage location)
bdd status demo-study
```

### Data Management

```bash
# Check for new events available remotely
bdd fetch demo-study

# Delete local study data (with confirmation)
bdd rm demo-study

# Delete without confirmation prompt
bdd rm --force demo-study
```

### Planned Features

The following commands would be useful additions:

```bash
# Export data to different format
bdd export demo-study --format csv --output my-data.csv

# Validate local data integrity
bdd verify demo-study
# Would check for corrupt files, missing events, etc.
```







### Configuration System

The application supports **per-study configuration files**, allowing each study/dataset to have its own:
- API key
- Storage settings (format, organization mode)
- Download settings (page size, concurrent requests)

#### Configuration Files

- **`settings/config_template.json`** - Template used when automatically creating new study-specific configs
- **`settings/default_config.json`** - Fallback config used when no study-specific config exists
- **`study_configs/{study-name}.json`** - Study-specific configuration files (one per study/dataset)


#### Creating Study Configs

1. **Using the CLI (Recommended)**:
   ```bash
   bdd study create my-study
   # Creates study_configs/my-study.json from template
   # Then add API key to .env: BEHAVERSE_API_KEY_MY_STUDY=your_key
   ```

2. **Manual creation**: Copy the template and customize:
   ```bash
   cp settings/config_template.json study_configs/my-study.json
   # Edit study_configs/my-study.json and add API key to .env
   ```

#### Study Config Structure

```json
{
  "study_name": "my-study",
  "api": {
    "base_url": "https://api.behaverse.org",
    "api_key": "your-api-key-here",
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
    "folder_structure": ["by_user_id", "by_date"]
  }
}
```

#### Configuration Reference

##### `study_name` (string)
The name of the study. This should match the study identifier used in the API.

##### `api` section
- **`base_url`** (string): The base URL for the Behaverse API. Default: `https://api.behaverse.org`
- **`api_key`** (string): Your API authentication key. Required for accessing study data. Each study can have its own API key.
- **`timeout`** (integer): Request timeout in seconds. Default: `30`
- **`max_retries`** (integer): Number of times to retry failed requests. Default: `3`
- **`retry_delay`** (integer): Delay in seconds between retries. Default: `1`

##### `download` section
- **`default_page_size`** (integer): Number of events to fetch per API request. Higher values mean fewer requests but larger responses. Default: `1000`
- **`max_concurrent_requests`** (integer): Maximum number of parallel API requests. Increase for faster downloads, but be mindful of API rate limits. Default: `3`

##### `storage` section
- **`data_directory`** (string): Root directory where downloaded data is stored. Default: `data`
- **`default_format`** (string): File format for saved data. Options: `json`, `csv`, `sqlite`, `parquet`. Default: `json`
- **`folder_structure`** (array): Define nested folder hierarchy for organizing data within each study folder. Each element specifies a grouping level. Example: `["by_user_id", "by_date"]` creates `data/study_name/user_123/2025-01-15/events.json`. Available options:
  - `by_user_id`: Group by user ID
  - `by_date`: Organize by date (day only, not datetime)
  - `by_event_type`: Group by event type
  
  Default: `["by_user_id", "by_date"]`

**Note:** All studies are automatically organized in `by_study` mode (one folder per study). The `folder_structure` setting controls the organization *within* each study folder.

#### Smart Config Selection

The CLI automatically selects the appropriate config:
- If `--config STUDY_NAME` is specified, uses `study_configs/STUDY_NAME.json`
- If downloading/querying a study, checks for `study_configs/{study-name}.json`
- Falls back to `settings/default_config.json` if no study-specific config exists






#### Programmatic Usage

```python
from behaverse_data_downloader.manager import BehaverseDataDownloader

# Initialize downloader
downloader = BehaverseDataDownloader("settings/default_config.json")

# Download with progress tracking
def progress_callback(progress):
    print(f"Downloaded {progress['total_events']} events...")

result = downloader.download_study(
    "demo-study", 
    incremental=True,
    progress_callback=progress_callback
)

# Load downloaded data
events = downloader.load_study_events("demo-study")
print(f"Loaded {len(events)} events")

# Get study information
info = downloader.get_study_info("demo-study")
print(f"Status: {info['status']}")
print(f"Local events: {info['local_events']}")
``` 




## Project Structure

```
behaverse-data-downloader/
├── behaverse_data_downloader/ # Main package
│   ├── __init__.py           # Package initialization
│   ├── manager.py            # Main downloader class (orchestrates everything)
│   ├── cli.py                # CLI entry point wrapper
│   ├── commands/             # Command Pattern implementation
│   │   ├── __init__.py       # Exports all commands
│   │   ├── base.py           # BaseCommand abstract class
│   │   ├── study.py          # Manage local study configs (list, create, show)
│   │   ├── remote.py         # Manage remote API endpoints (list, show)
│   │   ├── config.py         # Manage app-level configuration (show, get, set)
│   │   ├── status.py         # Show study info
│   │   ├── log.py            # Show download history
│   │   ├── download.py       # Download study data
│   │   ├── fetch.py          # Check for updates
│   │   ├── rm.py             # Delete study data
│   │   └── test_connection.py # Test API connection
│   ├── api/                  # API client modules
│   │   ├── __init__.py
│   │   └── client.py         # BehaverseAPIClient & EventData
│   ├── storage/              # Data storage modules
│   │   ├── __init__.py
│   │   └── manager.py        # Storage backends (JSON, CSV, SQLite)
│   └── downloader/           # Download management
│       ├── __init__.py
│       └── manager.py        # DownloadManager with pause/resume
├── settings/                 # Template and default app configuration
│   ├── config_template.json  # Template for new study configs
│   └── default_config.json   # Default app-level settings
├── study_configs/            # Study-specific configurations
│   ├── demo-study.json       # Example study config
│   └── README.md             # Study config documentation
├── data/                     # Downloaded data (auto-created)
├── tests/                    # Test files
│   ├── test_core_functionality.py
│   ├── test_api.py
│   └── test_dataset_api_keys.py
├── .env                      # Environment variables (create from .env.example)
├── .env.example             # Example environment file
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup
├── main.py                  # CLI entry point with command auto-discovery
├── docs/
│   └── developer-guide.md   # Guide for adding new commands
└── README.md                # This file
```



## How Downloaded Data is Organized

By default, downloaded data is stored in the `data/` folder. You can specify a different location in the config file.

The app creates a folder for each study (dataset) with organized event files and tracking metadata:

```
data/
└── study-name/
    ├── .metadata.json          # Study metadata and statistics
    ├── .download_history.json  # Complete download history
    └── [event files]           # Organized based on configuration
```

### Organization Modes

You can configure how events are organized using the `default_organization` setting:

- **`by_study`** (default) - One file per study: `data/demo-study/events.json`
- **`by_date`** - Separate files per date: `data/demo-study/2025-09-05_events.json`
- **`by_event_type`** - Separate files per event type: `data/demo-study/click_events.json`
- **`by_user_id`** - Separate files per user: `data/demo-study/user-id-123_events.json`
- **`flat`** - Timestamped files for each download: `data/demo-study/20251018_143022_events.json`

**Folder Structure**: You can create nested folder structures within each study folder by setting `folder_structure` in your config:
```json
{
  "folder_structure": ["by_user_id", "by_event_type"]
}
```
This creates: `data/study_name/user_123/click/events.json`

Supported combinations: `by_user_id → by_event_type`, `by_user_id → by_date`, `by_date → by_event_type`, etc.

Default: `["by_user_id", "by_date"]` creates `data/study_name/user_123/2025-01-15/events.json`

See `DATA_ORGANIZATION.md` for detailed examples.

### Storage Formats

Choose your preferred format with `default_format`:

- **`json`** (default) - JSON files with metadata
- **`csv`** - CSV files for easy import to Excel/R/Python
- **`sqlite`** - SQLite database for efficient querying

### Download Tracking

Every study folder includes:

- **`.metadata.json`** - Total events, first download, last update, storage format
- **`.download_history.json`** - Complete history of all downloads with timestamps and event counts

View download information:
```bash
# Show study info
bdd status demo-study

# Show complete download history
bdd log demo-study
```

See `DATA_ORGANIZATION.md` for detailed documentation on data organization and tracking.


## Configuration

The application can be configured via:
- **Environment variables** (`.env` file)
- **Configuration file** (`settings/default_config.json`)
- **Command-line arguments**

### Environment Variables (Recommended)

**API keys are now managed via environment variables for security.** This keeps sensitive credentials out of version control.

Create a `.env` file (copy from `.env.example`):

```bash
# Default API key for all studies
BEHAVERSE_API_KEY=your_default_api_key_here

# Study-specific API keys (optional, takes precedence)
# Format: BEHAVERSE_API_KEY_<STUDY_NAME> where STUDY_NAME is uppercase with hyphens replaced by underscores
BEHAVERSE_API_KEY_DEMO_STUDY=your_demo_study_key
```

**Priority order for API keys:**
1. Study-specific environment variable (`BEHAVERSE_API_KEY_<STUDY_NAME>`)
2. Study-specific config file (`study_configs/{study-name}.json`)
3. Default environment variable (`BEHAVERSE_API_KEY`)
4. Default config file (`settings/default_config.json`)

**Important:** The `.env` file is gitignored and should never be committed to version control.


### Configuration File

If you need custom settings per study, edit `settings/default_config.json`:

```json
{
  "api": {
    "base_url": "https://api.behaverse.org",
    "api_key": "your_key_here",
    "timeout": 30
  },
  "storage": {
    "data_directory": "data",
    "default_format": "json"
  }
}
```


## Features

### Currently Implemented

- **API Client** - Robust HTTP client with retry logic
- **Pagination** - Automatic handling of large datasets
- **Incremental Downloads** - Download only new events since last update
- **Multiple Storage Formats** - JSON, CSV, SQLite
- **Flexible Organization** - Organize by study, date, or event type
- **Progress Tracking** - Real-time download progress
- **Dataset-Specific Keys** - Different API keys for different studies
- **CLI Interface** - Full command-line functionality
- **Programmatic API** - Use as a Python library

### Planned Features

- Data export (ZIP per study)
- Volume estimation (number of events, dataset size)
- Data quality checks
- GUI


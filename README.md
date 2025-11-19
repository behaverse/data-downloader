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

```bash


## CLI Commands

### Getting Help

```bash
# Show all available commands and options
bdd help
bdd --help

# Show version
bdd --version
```

### Setup & Configuration

```bash
# List all available study config files (shows which have API keys configured)
bdd list-configs

# Create a new study config from template
bdd create-config my-new-study
# This creates study_configs/my-new-study.json with ${BEHAVERSE_API_KEY_MY_NEW_STUDY} reference
```

### Remote API Operations

```bash
# Test API connection and authentication
bdd test-connection

# List all studies available via the API (studies you have access to)
bdd list-studies
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
bdd history demo-study

# Show information about local data (event counts, last update, storage location)
bdd info demo-study
```

### Data Management

```bash
# Check for new events available remotely
bdd check-updates demo-study

# Delete local study data (with confirmation)
bdd delete demo-study

# Delete without confirmation prompt
bdd delete demo-study --force
```

### Missing/Planned Commands

The following commands would be useful additions:

```bash
# Show only remote API information (without querying local data)
bdd remote-info demo-study
# Would show: study metadata, total event count from API

# Export data to different format
bdd export demo-study --format csv --output my-data.csv

# Validate local data integrity
bdd verify demo-study
# Would check for corrupt files, missing events, etc.
```








### Command Design Philosophy

**Modern Subcommand Architecture:**
- Uses verb-noun structure: `bdd download study` (action first, target second)
- Follows industry standards like git, docker, kubectl
- Global options use flags: `--config`, `--version`
- Command-specific options use flags: `--incremental` for download
- Clear, intuitive: reads like natural language

**Why `--config` is optional (not useless):**
- **Auto-detection works 95% of the time**: `bdd download demo-study` finds `study_configs/demo-study.json`
- **Explicit needed for edge cases**: 
  - Config file named differently than study: `bdd --config my-custom-config download actual-study-name`
  - Testing with different configs: `bdd --config test-api-key list-studies`
  - Multiple studies sharing one config: `bdd --config shared-key download study1`

**Design Principles:**
1. **Sensible defaults** - Most common usage should be simplest
2. **Explicit when needed** - Advanced usage available but optional  
3. **Industry standards** - Follow conventions (--help, --version, etc.)
4. **Progressive disclosure** - Simple commands first, complexity optional





```





### Configuration System

The application now supports **per-study configuration files**, allowing each study/dataset to have its own:
- API key
- Storage settings (format, organization mode)
- Download settings (page size, concurrent requests)

#### Configuration Files

- **`settings/config_template.json`** - Template used when automatically creating new study-specific configs
- **`settings/default_config.json`** - Fallback config used when no study-specific config exists
- **`study_configs/{study-name}.json`** - Study-specific configuration files (one per study/dataset)

**Note:** All config files use environment variable references like `${BEHAVERSE_API_KEY_DEMO_STUDY}` instead of actual API keys, making them safe to commit to version control.

**Key Difference:**
- `config_template.json` - Has empty `study_name` and `api_key` fields (used as blueprint)
- `default_config.json` - Generic fallback (no `study_name` field, used when study config doesn't exist)
- Study configs (e.g., `demo-study.json`) - Have specific `study_name` and `api_key` for that study

#### Creating Study Configs

1. **Automatic creation**: When you use `--config` with a study name that doesn't have a config file, it's created from the template:
   ```bash
   bdd --config my-study download my-study
   # Creates study_configs/my-study.json from template
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

```





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
│   ├── api/                  # API client modules
│   │   ├── __init__.py
│   │   └── client.py         # BehaverseAPIClient & EventData
│   ├── storage/              # Data storage modules
│   │   ├── __init__.py
│   │   └── manager.py        # Storage backends (JSON, CSV, SQLite)
│   └── downloader/           # Download management
│       ├── __init__.py
│       └── manager.py        # DownloadManager with pause/resume
├── settings/                 # Templates and default config
├── study_configs/            # Study-specific configurations
│   └── default_config.json   # Default settings
├── data/                     # Downloaded data (auto-created)
├── tests/                    # Test files
│   ├── test_core_functionality.py
│   ├── test_api.py
│   └── test_dataset_api_keys.py
├── scripts/                  # Utility scripts
│   ├── build.sh             # Build executable
│   └── run.sh               # Run helper
├── docs/                     # Documentation
├── archive/                  # Archived/experimental code
│   ├── gui_experiments/     # GUI framework experiments
│   ├── gui_module/          # Original GUI (for future use)
│   └── old_scripts/         # Deprecated scripts
├── .env                      # Environment variables (create from .env.example)
├── .env.example             # Example environment file
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup
├── main.py                  # CLI entry point
├── cli_examples.sh          # CLI usage examples
├── PROJECT_STRUCTURE.md     # Detailed structure documentation
├── CLEANUP_SUMMARY.md       # Cleanup details
└── README.md                # This file
```

**See `PROJECT_STRUCTURE.md` for detailed module documentation.**


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
python main.py --info demo-study

# Show complete download history
python main.py --history demo-study
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
BEHAVERSE_API_KEY_TG_RELEASE_TEST=your_tg_release_test_key
```

**Priority order for API keys:**
1. Study-specific environment variable (`BEHAVERSE_API_KEY_<STUDY_NAME>`)
2. Study-specific config file (`study_configs/{study-name}.json`)
3. Default environment variable (`BEHAVERSE_API_KEY`)
4. Default config file (`settings/default_config.json`)

**Important:** The `.env` file is gitignored and should never be committed to version control.

### Configuration File (Optional)

**Note:** With the new .env-based system, configuration files are optional. You can manage everything via environment variables.

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

**For study-specific configs**, see the [Configuration](#configuration) section below.


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

- Data organization by user-id
- Data export (ZIP per study)
- Volume estimation (number of events, dataset size)
- Data exploration tools
- Event search and filtering
- Data quality checks
- GUI (after core features are complete)



## Development

### Running Tests
```bash
# Run core functionality tests
python tests/test_core_functionality.py

# Run API tests
python tests/test_api.py

# Run all tests with pytest (if installed)
pytest tests/

# Verify setup
python tests/verify_setup.py
```

### Building Executable
```bash
./scripts/build.sh
```

### Project Organization

This project follows professional Python development standards:

- **Clean Package Structure** - Proper Python package with `__init__.py` files
- **Separation of Concerns** - API, storage, download, and manager logic separated
- **Modular Design** - Easy to extend or replace components
- **Type Hints** - Type annotation support throughout
- **Error Handling** - Comprehensive exception handling
- **Testing** - Structured test framework
- **Documentation** - Extensive inline and external documentation

### Code Organization

- `behaverse_data_downloader/manager.py` - Main orchestrator
- `behaverse_data_downloader/api/client.py` - API communication
- `behaverse_data_downloader/storage/manager.py` - Data persistence
- `behaverse_data_downloader/downloader/manager.py` - Download control

Each module is focused and has a single responsibility.


## Testing

The project includes comprehensive tests:

- `test_core_functionality.py` - Tests all core features
- `test_api.py` - Tests API client functionality  
- `test_dataset_api_keys.py` - Tests dataset-specific API keys
- `verify_setup.py` - Verifies installation and setup

Run tests before making changes to ensure everything works correctly.


## Troubleshooting

### API Connection Issues
```bash
# Test your connection
python main.py --test-connection

# Check your API key in .env file
cat .env
```

### Import Errors
```bash
# Make sure dependencies are installed
pip install -r requirements.txt
```

### No Data Downloaded
- Verify your API key is correct
- Check that the study name is correct (use `--list-studies`)
- Look for error messages in the output


## Documentation

- **README.md** (this file) - Main documentation
- **PROJECT_STRUCTURE.md** - Detailed project structure and module documentation
- **CLEANUP_SUMMARY.md** - Details of project cleanup and organization
- **docs/** - Additional documentation
- **cli_examples.sh** - Example CLI commands


## Archive

The `archive/` directory contains:
- **gui_experiments/** - GUI framework research and experiments
- **gui_module/** - Original GUI code (preserved for future use)
- **old_scripts/** - Deprecated test and utility scripts

These files are preserved but not actively used. The focus is on core functionality first.


## Future Development

### Completed
- ✅ Data organization by study/date/event_type
- ✅ Data organization by user-id
- ✅ Hierarchical organization (nested folders)
- ✅ Download tracking and metadata
- ✅ Incremental downloads

### Near Term
1. Add data export features (ZIP per study)
2. Add dataset volume estimation
3. Implement data exploration and search
4. Add data quality validation
5. Extend hierarchical organization to CSV/SQLite backends

### Long Term
1. Build modern GUI (using research from archive)
2. Add real-time monitoring features
3. Implement data visualization
4. Add collaborative features
5. Cloud deployment options


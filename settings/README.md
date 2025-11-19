# Settings Directory

This directory contains template and default configuration files for the Behaverse Data Downloader.

## Files

### `config_template.json`
Template used when creating new study-specific configuration files. This is the blueprint that gets copied when you create a new study config.

**Usage:** Copy this file to `../study_configs/<study-name>.json` and customize as needed.

### `default_config.json`
Default/fallback configuration used when no study-specific config exists. This file contains:
- Default API endpoint URL
- Default timeout and retry settings
- Default download behavior
- Default storage organization

**Note:** The `api_key` field uses an environment variable reference: `${BEHAVERSE_API_KEY}`. This makes the file safe to commit to version control.

## Configuration Priority

When the application loads configuration, it follows this priority order:

1. **Study-specific config** (`../study_configs/<study-name>.json`)
2. **Default config** (`default_config.json`) - used as fallback

## Environment Variables

All API keys should be stored in the `.env` file at the project root:

```bash
# Default API key
BEHAVERSE_API_KEY=your_default_key

# Study-specific API keys
BEHAVERSE_API_KEY_DEMO_STUDY=your_demo_study_key
BEHAVERSE_API_KEY_TG_RELEASE_TEST=your_tg_release_test_key
```

See `.env.example` for the full template.

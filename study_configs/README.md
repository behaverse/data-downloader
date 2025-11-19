# Study Configuration Files

This directory contains study-specific configuration files for the Behaverse Data Downloader.

## API Key Management

**API keys are managed via environment variables (`.env` file) for security.**

The `api_key` field in these config files uses environment variable references like `${BEHAVERSE_API_KEY_DEMO_STUDY}`. The application automatically resolves these references by loading values from the `.env` file:

- For study `demo-study`: Looks for `BEHAVERSE_API_KEY_DEMO_STUDY` in `.env`
- For study `tg_release_test`: Looks for `BEHAVERSE_API_KEY_TG_RELEASE_TEST` in `.env`

**Format:** `BEHAVERSE_API_KEY_<STUDY_NAME>` where `<STUDY_NAME>` is uppercase with hyphens replaced by underscores.

## File Structure

Each study config file should have:
- `study_name`: The identifier for the study (matches the filename)
- `api`: API connection settings (leave `api_key` empty)
- `download`: Download behavior settings
- `storage`: Data storage and organization settings

## Creating New Study Configs

1. Copy `../settings/config_template.json` to this directory
2. Rename to `<study-name>.json`
3. Set the `study_name` field
4. Update `api_key` to `${BEHAVERSE_API_KEY_<STUDY_NAME>}` (use the template pattern)
5. Customize download and storage settings as needed
6. Add the actual API key to `.env` as `BEHAVERSE_API_KEY_<STUDY_NAME>=your_key_here`

**These config files are now safe to commit to version control** since they only contain variable references, not actual API keys!

## Priority Order

The application uses this priority for API keys:
1. Environment variable `BEHAVERSE_API_KEY_<STUDY_NAME>` (highest priority)
2. This config file's `api_key` field (if not empty)
3. Default environment variable `BEHAVERSE_API_KEY`
4. Default config in `../settings/default_config.json`

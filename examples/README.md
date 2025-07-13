# Symposia Configuration Examples

This directory contains example configuration files for the Symposia framework.

## Files

- **`symposia.yaml`** - Production-ready configuration example with multiple LLM providers and a fact-checking committee
- **`symposia.local.yaml`** - Development configuration with mock services for testing

## Usage

### For Development/Testing
Copy the local config to your project root or a `config/` directory:
```bash
cp examples/symposia.local.yaml config/symposia.local.yaml
```

### For Production
Copy and customize the production config:
```bash
cp examples/symposia.yaml config/symposia.yaml
# Edit config/symposia.yaml with your actual API keys and settings
```

## Configuration Priority

The system looks for configuration files in this order:
1. `SYMPOSIA_CONFIG` environment variable
2. `config/symposia.local.yaml`
3. `config/symposia.yaml`
4. `symposia.yaml` (in project root)
5. `examples/symposia.local.yaml`
6. `examples/symposia.yaml`
7. Default configuration (if no files found)

## Security Note

- Never commit `config/symposia.local.yaml` to version control
- Keep your API keys in environment variables or `.env` files
- The `config/` directory is gitignored by default 
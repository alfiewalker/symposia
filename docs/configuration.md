# Configuration Guide

## Overview

Symposia uses YAML configuration files to define LLM services and intelligence pools (committees). The system follows a hierarchical configuration approach with sensible defaults.

## Configuration Structure

### Package Structure
```
symposia/
├── symposia/
│   └── config/
│       ├── __init__.py
│       ├── loader.py      # Configuration loading logic
│       ├── factory.py     # Committee factory
│       ├── models.py      # Pydantic models
│       └── defaults.py    # Minimal default config
├── examples/
│   ├── symposia.yaml      # Production example
│   └── symposia.local.yaml # Development example
└── config/                # User configs (gitignored)
    └── symposia.local.yaml
```

## Configuration Priority

The system searches for configuration files in this order:

1. **Environment Variable**: `SYMPOSIA_CONFIG`
2. **User Configs**: `config/symposia.local.yaml`
3. **User Configs**: `config/symposia.yaml`
4. **Project Root**: `symposia.yaml`
5. **Examples**: `examples/symposia.local.yaml`
6. **Examples**: `examples/symposia.yaml`
7. **Default**: Built-in minimal configuration

## Configuration Format

### LLM Services
```yaml
llm_services:
  service_name:
    provider: openai|anthropic|google
    model: model-name
    cost_per_token: 0.000005
    api_key: optional-api-key  # Can use env vars instead
```

### Intelligence Pools
```yaml
intelligence_pools:
  pool_name:
    name: "Human Readable Name"
    reputation_management: true|false
    agreement_bonus: 0.1
    dissent_penalty: 0.05
    members:
      - name: "Member Name"
        service: "service_name"
        weight: 1.0
        initial_reputation: 1.0
        role_prompt: "Role description"
```

## Best Practices

### Development
1. Copy `examples/symposia.local.yaml` to `config/symposia.local.yaml`
2. Use mock services for testing
3. Keep local configs out of version control

### Production
1. Copy `examples/symposia.yaml` to `config/symposia.yaml`
2. Use environment variables for API keys
3. Customize committee compositions for your use case

### Security
- Never commit API keys to version control
- Use environment variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`
- The `config/` directory is gitignored by default

### Library env loading
- CLI auto-loads `.env.local` and `.env` for convenience.
- Library import does not auto-load env files.
- If you want opt-in env loading from code, use `from symposia.env import load_env` and call `load_env()` explicitly.

## Usage Examples

### Basic Usage
```python
from symposia.config.loader import load_config
from symposia.config import CommitteeFactory

config = load_config()
factory = CommitteeFactory(config)
committee = factory.create_committee('my_pool', 'WeightedMajorityVote')
```

### Custom Config Path
```python
config = load_config('/path/to/my/config.yaml')
```

### Environment Variable
```bash
export SYMPOSIA_CONFIG=/path/to/config.yaml
python -m symposia.main
``` 
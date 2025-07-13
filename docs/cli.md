# Symposia CLI Documentation

## Overview

The Symposia CLI provides an elegant command-line interface for managing and running AI committee deliberations. It offers both interactive and command-line modes with comprehensive help and error handling.

## Installation

### Development Installation
```bash
# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### Global Installation
```bash
pip install symposia
```

## Usage

### Basic Commands

#### List Available Intelligence Pools
```bash
symposia list-pools
# or
symposia pools
# or
symposia lp
```

**Verbose output:**
```bash
symposia list-pools --verbose
```

#### List Available LLM Services
```bash
symposia list-services
# or
symposia services
# or
symposia ls
```

#### Check Environment Configuration
```bash
symposia check
# or
symposia env
```

#### Run a Single Deliberation
```bash
symposia ask <pool_name> "<question>"
```

**Examples:**
```bash
symposia ask clone_committee "Is artificial intelligence safe for humanity?"
symposia ask fact_check_committee "What are the benefits of renewable energy?"
```

**With custom voting strategy:**
```bash
symposia ask clone_committee "Is quantum computing a threat?" --strategy UnanimousVote
```

#### Interactive Mode
```bash
symposia interactive
# or
symposia i
```

## Interactive Mode Commands

When in interactive mode, you can use these commands:

- `ask <pool> <question>` - Run deliberation with specific pool and question
- `pools` - List available intelligence pools
- `services` - List available LLM services
- `help` - Show help message
- `quit` - Exit interactive mode

**Example interactive session:**
```
🎯 Interactive Deliberation Mode
========================================
Available pools: clone_committee, fact_check_committee
Type 'quit' to exit, 'help' for commands

🤖 symposia> ask clone_committee "Is AI beneficial for society?"
🤖 Running deliberation with: Multi-Personality Test Committee
📝 Question: Is AI beneficial for society?
🎯 Strategy: WeightedMajorityVote
============================================================
[Deliberation results...]

🤖 symposia> pools
🤖 Available Intelligence Pools:
==================================================
📋 clone_committee
   Name: Multi-Personality Test Committee
   Members: 3
   Reputation: 🟢 Active

🤖 symposia> quit
👋 Goodbye!
```

## Configuration

The CLI automatically loads configuration from:
1. `SYMPOSIA_CONFIG` environment variable
2. `config/symposia.local.yaml` (for local development)
3. `config/symposia.yaml`
4. `examples/symposia.yaml`
5. Default configuration (fallback)

## Environment Variables

Required API keys (at least one):
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GOOGLE_API_KEY` - Google API key

Optional:
- `SYMPOSIA_CONFIG` - Path to configuration file

## Examples

### Quick Start
```bash
# Check your setup
symposia check

# List available pools
symposia list-pools

# Run a quick deliberation
symposia ask clone_committee "What is the future of AI?"

# Start interactive mode for multiple questions
symposia interactive
```

### Advanced Usage
```bash
# Use verbose output to see detailed pool information
symposia list-pools --verbose

# Run with specific voting strategy
symposia ask clone_committee "Is blockchain revolutionary?" --strategy UnanimousVote

# Check environment and configuration
symposia check
```

## Error Handling

The CLI provides clear error messages for common issues:

- **Missing API keys**: Shows which keys are missing and how to set them
- **Invalid pool names**: Lists available pools when an invalid name is provided
- **Configuration errors**: Shows the source of configuration and any validation errors
- **Network errors**: Provides helpful error messages for API connection issues

## Backward Compatibility

The original `main.py` interface is still available for backward compatibility:

```bash
# Legacy mode (still works)
python -m symposia.main --pool clone_committee

# New CLI mode (recommended)
symposia ask clone_committee "Your question here"
```

## Troubleshooting

### Common Issues

1. **"No API keys found"**
   - Create a `.env` file with your API keys
   - Set at least one of: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`

2. **"Pool not found"**
   - Use `symposia list-pools` to see available pools
   - Check your configuration file for correct pool names

3. **"Configuration not loaded"**
   - Ensure you have a valid YAML configuration file
   - Check the configuration priority order above
   - Use `symposia check` to diagnose issues

4. **"Import errors"**
   - Install dependencies: `pip install -r requirements.txt`
   - For development: `pip install -r requirements-dev.txt`

### Getting Help

```bash
# Show general help
symposia --help

# Show help for specific command
symposia ask --help
symposia list-pools --help

# Check environment
symposia check
```

## Development

### Running Tests
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=symposia
```

### Adding New Commands

To add new CLI commands, modify `symposia/cli.py`:

1. Add a new method to `SymposiaCLI` class
2. Add a new subparser in `create_parser()`
3. Add the command handling in `main()`

### CLI Structure

```
symposia/
├── cli.py              # Main CLI implementation
├── main.py             # Backward compatibility
└── config/
    ├── loader.py       # Configuration loading
    ├── factory.py      # Committee factory
    └── models.py       # Pydantic models
```

## Contributing

When contributing to the CLI:

1. Follow the existing code style
2. Add comprehensive help text for new commands
3. Include error handling and validation
4. Add tests for new functionality
5. Update this documentation

## License

This CLI is part of the Symposia framework and follows the same license terms. 
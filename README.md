# Symposia

A modular LLM ensemble voting framework for committee-based deliberation.

## Overview

Symposia enables AI committee deliberation through configurable LLM services, voting strategies, and reputation management. It provides both a Python API and CLI interface for creating intelligent committees that can validate information, make decisions, and provide detailed reasoning.

## Features

- **Multi-LLM Support**: OpenAI, Anthropic, Google, and local models
- **Configurable Committees**: YAML-based configuration for easy setup
- **Multiple Voting Strategies**: Majority, mean, median, and custom strategies
- **Reputation Management**: Track and weight committee member performance
- **CLI Interface**: Command-line tools for committee management
- **Comprehensive Documentation**: Architecture diagrams, validation reports, and specifications

## Project Structure

```
symposia/
├── core/                   # Core domain logic
│   ├── llm_service.py     # LLM service implementations
│   ├── member.py          # Committee member representation
│   ├── reputation.py      # Reputation management
│   ├── result.py          # Deliberation results
│   └── committee.py       # Committee orchestration
├── strategies/            # Voting strategies
│   ├── base.py           # Abstract base class
│   ├── majority.py       # Weighted majority voting
│   ├── mean.py           # Weighted mean scoring
│   └── median.py         # Median scoring
├── config/               # Configuration and factory
│   ├── models.py         # Pydantic configuration models
│   └── factory.py        # Committee factory
├── terminal/             # CLI interface
│   ├── cli.py           # Command-line interface
│   └── services.py      # CLI service implementations
├── utils/                # Utilities
│   ├── cache.py          # Simple caching
│   └── parsing.py        # JSON parsing utilities
└── __init__.py           # Package initialization
```

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd Symposia

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

## Configuration

### Environment Variables

Create a `.env.local` file in your project root:

```bash
# Copy the example
cp examples/env.example .env.local

# Edit with your API keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
```

### Committee Configuration

Symposia uses YAML configuration files to define committees. See `examples/symposia.local.yaml` for a complete example:

```yaml
committee:
  name: "Validation Committee"
  members:
    - name: "Health Expert"
      service: "openai"
      model: "gpt-4"
      prompt: "You are a health expert..."
    - name: "Financial Analyst"
      service: "anthropic"
      model: "claude-3-sonnet"
      prompt: "You are a financial analyst..."
```

## Usage

### CLI Interface

The CLI provides commands for managing committees and running deliberations:

```bash
# List available intelligence pools
symposia list-pools

# List available LLM services
symposia list-services

# Check configuration
symposia check --config examples/symposia.local.yaml

# Ask a question
symposia ask "Is this investment advice sound?" --config examples/symposia.local.yaml

# Interactive mode
symposia interactive --config examples/symposia.local.yaml
```

### Python API

```python
from symposia.config.factory import CommitteeFactory
from symposia.config.loader import load_config

# Load configuration
config = load_config("examples/symposia.local.yaml")

# Create committee
factory = CommitteeFactory()
committee = factory.create_committee(config)

# Run deliberation
result = committee.deliberate("Is this health advice accurate?")
print(result.final_answer)
print(result.reasoning)
```

### Example Script

Run the example script to see Symposia in action:

```bash
python examples/main.py
```

This will run a validation committee on health, financial, and coding advice questions.

## Documentation

- **[Architecture Diagram](docs/architecture-diagram.md)**: System components and data flow
- **[Validation Report](docs/validation-report.md)**: Committee performance analysis
- **[CLI Documentation](docs/cli.md)**: Command-line interface guide
- **[Configuration Guide](docs/configuration.md)**: YAML configuration reference
- **[Specifications](docs/specifications.md)**: Technical specifications
- **[Whitepaper](docs/Whitepaper_%20Symposia%20-%20Latest.pdf)**: Detailed project overview

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black symposia/ tests/

# Lint code
flake8 symposia/ tests/
```

## Architecture Principles

- **Modularity**: Each component has a single responsibility
- **Separation of concerns**: Configuration, strategies, and core logic are decoupled
- **Composition over inheritance**: Services and strategies are composable
- **Clean interfaces**: Clear boundaries between modules
- **Progressive discovery**: Easy to understand and extend
- **Reactive execution**: Step-by-step deliberation with adaptive tool selection

## License

[Add your license information here] 


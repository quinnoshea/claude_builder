# Claude Builder - Universal Claude Code Environment Generator

[![PyPI version](https://img.shields.io/badge/PyPI-coming%20soon-orange.svg)](https://pypi.org/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI](https://github.com/quinnoshea/claude_builder/workflows/CI/badge.svg)](https://github.com/quinnoshea/claude_builder/actions)
[![Tests](https://img.shields.io/badge/tests-27%2B%20files-green.svg)](https://github.com/quinnoshea/claude_builder/tree/main/tests)
[![Coverage](https://img.shields.io/badge/coverage-85%25%2B-brightgreen.svg)](https://github.com/quinnoshea/claude_builder)
[![Code Quality](https://img.shields.io/badge/code%20quality-A-brightgreen.svg)](https://github.com/quinnoshea/claude_builder)
[![GitHub stars](https://img.shields.io/github/stars/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/network)
[![GitHub issues](https://img.shields.io/github/issues/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/issues)
[![Last Commit](https://img.shields.io/github/last-commit/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/commits/main)

Transform any project into an optimized Claude Code development environment with intelligent analysis and automated setup.

## Overview

Claude Builder analyzes your project directory and generates comprehensive Claude Code documentation, agent configurations, and development workflows tailored to your specific project type, framework, and domain.

## Key Features

- **🧠 Intelligent Project Detection** - Automatically identifies languages, frameworks, and architecture patterns
- **🎯 Dynamic Agent Selection** - Chooses optimal Claude Code agents based on your project characteristics  
- **📝 Adaptive Templates** - Generates appropriate documentation for any project type
- **🔒 Safe Git Integration** - Optional git integration with backup/rollback capabilities
- **⚙️ Claude Mention Control** - Configurable Claude reference policies (forbidden/minimal/allowed)
- **🌍 Universal Support** - Works with Python, Rust, JavaScript, Java, Go, and more

## Quick Start

```bash
# Install claude-builder
pip install claude-builder

# Basic usage - analyze and generate with intelligent defaults
claude-builder /path/to/your/project

# Advanced usage with options
claude-builder /path/to/project --git-exclude --claude-mentions=minimal --template=web-api
```

## Installation

### From PyPI (recommended)
```bash
pip install claude-builder
```

### From Source
```bash
git clone https://github.com/claude-builder/claude-builder.git
cd claude-builder
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/claude-builder/claude-builder.git
cd claude-builder
pip install -e ".[dev]"
pre-commit install
```

## Usage Examples

### Basic Project Analysis
```bash
# Analyze and generate for any project
claude-builder ./my-python-project
claude-builder ./my-rust-cli
claude-builder ./my-react-app

# Preview what would be generated
claude-builder ./project --dry-run --verbose
```

### Git Integration Options
```bash
# Add generated files to .git/info/exclude (local only)
claude-builder ./project --git-exclude

# Control Claude mentions in generated content
claude-builder ./project --claude-mentions=forbidden  # No Claude references
claude-builder ./project --claude-mentions=minimal    # Minimal references
claude-builder ./project --claude-mentions=allowed    # Full attribution
```

### Template and Configuration
```bash
# Use specific template (override detection)
claude-builder ./project --template=python-web

# Use custom configuration
claude-builder ./project --config=claude-builder.json

# Generate configuration file
claude-builder config init ./project
```

### Advanced Workflows
```bash
# Analysis only (no file generation)
claude-builder analyze ./project --output=analysis.json

# Generate from existing analysis
claude-builder generate ./project --from-analysis=analysis.json

# Template management
claude-builder templates list
claude-builder templates install community/ecommerce-django

# Agent management
claude-builder agents list
claude-builder agents configure ./project
```

## Project Structure

```
claude-builder/
├── claude_builder/
│   ├── core/           # Core analysis and generation logic
│   ├── cli/            # Command-line interface
│   ├── templates/      # Built-in templates
│   ├── agents/         # Agent configurations
│   └── utils/          # Utility functions
├── tests/              # Test suite
├── docs/               # Documentation
└── examples/           # Example projects and configurations
```

## Configuration

Create a `claude-builder.json` file for project-specific settings:

```json
{
  "analysis": {
    "ignore_patterns": ["vendor/", "node_modules/"],
    "confidence_threshold": 80
  },
  "templates": {
    "preferred_templates": ["python-web", "api-first"]
  },
  "agents": {
    "exclude_agents": ["ai-engineer"],
    "priority_agents": ["python-pro", "backend-developer"]
  },
  "git_integration": {
    "mode": "exclude_generated",
    "claude_mention_policy": "minimal"
  }
}
```

## Generated Output

Claude Builder generates a comprehensive development environment:

- **CLAUDE.md** - Project-specific Claude Code guidelines
- **AGENTS.md** - Agent configurations and workflows  
- **.claude/** - Directory with detailed planning documents
- **Agent configs** - Ready-to-use agent configurations
- **Development workflows** - Multi-phase development processes

## Supported Project Types

### Languages
- Python (Django, Flask, FastAPI, CLI tools, data science)
- Rust (CLI tools, web services, systems programming)
- JavaScript/TypeScript (React, Vue, Node.js, APIs)
- Java (Spring Boot, microservices)
- Go (CLI tools, web services, microservices)
- And more...

### Domains
- Web applications and APIs
- Command-line tools
- Data science and ML projects
- E-commerce platforms
- DevOps and infrastructure tools
- Media management systems
- And more...

## Development

### Running Tests
```bash
pytest
pytest --cov=claude_builder  # With coverage
```

### Code Quality
```bash
black claude_builder tests    # Format code
flake8 claude_builder tests   # Lint code
mypy claude_builder           # Type checking
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the original Radarr Rust planning generator
- Built for the Claude Code ecosystem
- Thanks to the awesome-claude-code-subagents community
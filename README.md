# Claude Builder - Universal Claude Code Environment Generator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-511%20passing-brightgreen.svg)](https://github.com/quinnoshea/claude_builder/tree/main/tests)
[![Development Status](https://img.shields.io/badge/status-infrastructure%20complete-yellow.svg)](https://github.com/quinnoshea/claude_builder)
[![CI](https://github.com/quinnoshea/claude_builder/workflows/CI/badge.svg)](https://github.com/quinnoshea/claude_builder/actions)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/c0920529ab54462387f217498a4e01db)](https://app.codacy.com/gh/quinnoshea/claude_builder/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/c0920529ab54462387f217498a4e01db)](https://app.codacy.com/gh/quinnoshea/claude_builder/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![GitHub stars](https://img.shields.io/github/stars/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/network)
[![GitHub issues](https://img.shields.io/github/issues/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/issues)
[![Last Commit](https://img.shields.io/github/last-commit/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/commits/main)

🚧 **Infrastructure Complete** - Core functionality operational, completion work in progress  
Transform any codebase into an optimized Claude Code development environment with intelligent analysis and adaptive templates.

## 🎯 Current Project Status

**Development Phase**: Core infrastructure complete, stabilization in progress  
**Core Functionality**: ✅ All major CLI commands operational  
**Test Coverage**: 67% (511 passing tests, 220 requiring fixes)  
**Next Milestone**: Test stabilization and agent integration completion  

## 🌟 What Claude Builder Does

Claude Builder automates the complex task of setting up optimized Claude Code development environments. Through intelligent project analysis, it detects languages, frameworks, and project characteristics, then generates tailored documentation, agent configurations, and development workflows.

### 🏆 **Current Capabilities**
- **Multi-Language Analysis**: Python, Rust, JavaScript, TypeScript, Java, Go, and more
- **Framework Detection**: Django, FastAPI, React, Vue, Axum, Spring Boot, Express, and others
- **CLI Interface**: Professional command-line tool with Rich UI components
- **Template System**: Hierarchical template composition working
- **Git Integration**: Safe backup/restore operations

### 🚧 **Completion Work Required**
- **Test Stabilization**: Fix 220 failing tests for production reliability
- **Agent Integration**: Complete TODO in main CLI flow for full agent functionality
- **Quality Gates**: Ensure all CI/CD checks pass consistently

## 🔧 Core Capabilities

### **🧠 Intelligent Project Analysis**
- **Multi-Language Detection**: Automatic recognition of primary and secondary languages
- **Framework Recognition**: Detects popular frameworks through dependency and pattern analysis  
- **Project Classification**: Web apps, CLI tools, libraries, data science projects
- **Confidence Scoring**: Reliability metrics for all detection results

### **🎯 Agent System Foundation**
- **Agent Selection Logic**: Intelligent matching of Claude Code agents to project characteristics
- **Configuration Generation**: Creates AGENTS.md files with recommended agent workflows
- **Custom Integration**: Support for custom agent directories and configurations
- **Workflow Patterns**: Multi-agent collaboration templates

### **📋 Template System**
- **Hierarchical Composition**: Base → Language → Framework template layers
- **Variable Substitution**: Dynamic content generation with project-specific data
- **Template Validation**: Built-in validation and error checking
- **Extensible Design**: Foundation ready for community template marketplace

### **🔒 Safe Git Integration**
- **Non-Destructive Operations**: Complete backup/restore system
- **Local Git Exclude**: Adds patterns to .git/info/exclude (not committed)
- **Claude Mention Control**: Configurable policies for AI references in generated content
- **Rollback Capabilities**: Full restore functionality for generated files

## 🚀 Installation & Setup

### **Development Installation**
```bash
# Clone the repository
git clone https://github.com/quinnoshea/claude_builder.git
cd claude_builder

# Install with development dependencies (prefer uv)
uv pip install -e ".[dev]"  # Recommended: faster, modern
# OR: pip install -e ".[dev]"  # Alternative: traditional pip

# Set up pre-commit hooks
pre-commit install
```

### **Basic Usage**
```bash
# Analyze and generate documentation for any project
claude-builder /path/to/your/project

# Preview what would be generated (safe)
claude-builder /path/to/project --dry-run --verbose

# Generate with git integration
claude-builder /path/to/project --git-exclude --claude-mentions=minimal
```

### **System Requirements**
- **Python**: 3.8+ (3.11+ recommended)
- **Memory**: 512MB minimum for analysis operations
- **Storage**: 100MB for development environment
- **OS**: Linux, macOS, Windows (WSL2 recommended on Windows)

## 📚 Usage Examples

### **Real-World Project Analysis**

#### **Python Web Application**
```bash
claude-builder ./fastapi-ecommerce
# ✅ Detects: Python 3.11, FastAPI, PostgreSQL dependencies
# ✅ Generates: API development workflow, backend agent configuration
# ✅ Creates: CLAUDE.md with FastAPI-specific patterns and best practices
```

#### **Rust CLI Tool**  
```bash
claude-builder ./cli-performance-monitor
# ✅ Detects: Rust, CLI patterns, system dependencies
# ✅ Generates: Systems development workflow with Rust-specific guidance
# ✅ Creates: Development environment optimized for Rust CLI development
```

#### **React TypeScript Frontend**
```bash
claude-builder ./next-dashboard
# ✅ Detects: TypeScript, Next.js, React patterns
# ✅ Generates: Frontend development workflow and component guidance
# ✅ Creates: TypeScript-aware development environment
```

### **Advanced Configuration**

#### **Git Integration Options**
```bash
# Add to local git exclude (recommended - safe)
claude-builder ./project --git-exclude

# Control Claude mentions in generated content
claude-builder ./project --claude-mentions=forbidden  # No AI references
claude-builder ./project --claude-mentions=minimal    # Minimal references  
claude-builder ./project --claude-mentions=allowed    # Full attribution

# Backup existing files before generation
claude-builder ./project --backup-existing
```

### **CLI Subcommands**

#### **Project Analysis**
```bash
# Detailed analysis with verbose output
claude-builder analyze ./project --verbose

# Export analysis to JSON for inspection
claude-builder analyze ./project --output=analysis.json
```

#### **Template Management** 
```bash
# List available built-in templates
claude-builder templates list

# Validate custom template structure
claude-builder templates validate ./custom-template
```

#### **Configuration Management**
```bash
# Initialize project configuration
claude-builder config init ./project

# Show current configuration
claude-builder config show ./project
```

## 🏗️ Project Architecture

### **Codebase Structure**
```
claude_builder/
├── src/claude_builder/           # Core application  
│   ├── core/                     # Business logic
│   │   ├── analyzer.py          # Project analysis engine
│   │   ├── template_manager.py  # Template system
│   │   ├── agents.py            # Agent selection logic
│   │   ├── generator.py         # Document generation
│   │   └── config.py            # Configuration management
│   ├── cli/                      # Command-line interface
│   │   ├── main.py              # Entry point and main workflow
│   │   ├── analyze_commands.py  # Analysis operations  
│   │   ├── generate_commands.py # Generation workflows
│   │   ├── template_commands.py # Template management
│   │   ├── config_commands.py   # Configuration operations
│   │   └── git_commands.py      # Git integration
│   ├── templates/                # Hierarchical template system
│   │   ├── base/                # Universal base templates
│   │   ├── languages/           # Language-specific templates
│   │   └── frameworks/          # Framework-specific overlays
│   └── utils/                    # Utility functions
│       ├── git.py               # Git operations and safety
│       ├── validation.py        # Input validation
│       └── exceptions.py        # Error handling
├── tests/                        # Comprehensive test suite
│   ├── unit/                    # Unit tests by phase
│   │   ├── phase1_core/         # Core functionality tests
│   │   ├── phase2_intelligence/ # Analysis and detection tests
│   │   └── phase3_advanced/     # Advanced feature tests
│   └── integration/             # End-to-end workflow tests
└── docs/                         # Project documentation
```

### **Generated Output Structure**
```
your-project/                     # Your analyzed project
├── CLAUDE.md                    # Project-specific Claude Code guidelines
├── AGENTS.md                    # Agent configuration and workflows
└── .claude/                     # Detailed development environment
    ├── development_workflow.md  # Development process guidance
    ├── agent_coordination.md    # Multi-agent collaboration patterns
    └── project_context.md       # Analysis results and project insights
```

## 🎯 Language & Framework Support

### **Languages** (Detection Working)
| Language | Status | Confidence | Common Frameworks |
|----------|--------|------------|-------------------|
| **Python** | ✅ Operational | High | Django, Flask, FastAPI |
| **Rust** | ✅ Operational | High | Axum, Actix, Tokio |
| **JavaScript/TypeScript** | ✅ Operational | High | React, Vue, Express, Next.js |
| **Java** | ✅ Operational | Good | Spring Boot, Maven |
| **Go** | ✅ Operational | Good | Gin, Echo, CLI tools |
| **C#** | ✅ Basic | Fair | ASP.NET Core |
| **PHP** | ✅ Basic | Fair | Laravel, Symfony |
| **Ruby** | ✅ Basic | Fair | Rails, Sinatra |

### **Project Types** (Auto-Detected)
- **Web Applications**: API servers, full-stack applications, microservices
- **CLI Tools**: Command-line utilities, system tools, automation scripts
- **Libraries**: Reusable packages, frameworks, shared components
- **Data Science**: Jupyter notebooks, ML pipelines, analysis projects
- **Mobile**: React Native, Flutter, native mobile applications

## 🧪 Development & Testing

### **Running Tests**
```bash
# Run core functionality tests
pytest tests/unit/phase1_core/ -v

# Check current test coverage
pytest --cov=claude_builder --cov-report=term-missing

# Run all tests (expect some failures - work in progress)
pytest tests/ -v
```

### **Code Quality**
```bash
# Format code
black claude_builder tests/

# Lint code
ruff claude_builder tests/

# Type checking
mypy claude_builder/

# Pre-commit checks (runs automatically)
pre-commit run --all-files
```

### **Performance Testing**
```bash
# Test analysis speed on sample projects
time claude-builder tests/fixtures/sample_projects/python_project --dry-run
time claude-builder tests/fixtures/sample_projects/rust_project --dry-run
```

## 🤝 Contributing

### **Current Development Focus**
We're in the infrastructure completion phase, focusing on:

1. **Test Stabilization**: Fixing failing tests for production reliability
2. **Agent Integration**: Completing the agent configuration in main CLI
3. **Quality Assurance**: Ensuring all CI/CD gates pass consistently
4. **Documentation**: Keeping docs aligned with implementation

### **How to Contribute**

#### **Phase 1: Infrastructure Completion** (Current Focus)
Perfect for developers wanting to learn testing and infrastructure work:

```bash
# Set up development environment
git clone https://github.com/quinnoshea/claude_builder.git
cd claude_builder
uv pip install -e ".[dev]"
pre-commit install

# Verify setup
pytest tests/unit/phase1_core/ -v  # Should pass
claude-builder --help              # Should show help

# Work on test fixes (see 12-TASKING.md for specific tasks)
```

#### **Future Phases**
- **Phase 2**: Production readiness and polish
- **Phase 3**: Community features and template marketplace
- **Phase 4**: Enterprise features and integrations

### **Contribution Areas**
- **Test Infrastructure**: Help fix failing tests and improve coverage
- **CLI Enhancement**: Improve user experience and error messages
- **Template Development**: Create templates for new languages/frameworks
- **Documentation**: Improve guides, examples, and API documentation

## 📄 License & Acknowledgments

### **License**
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **🙏 Acknowledgments** 
- **Inspired by**: Original Radarr Rust planning generator concept
- **Built for**: Claude Code ecosystem and developer productivity enhancement
- **Thanks to**: Beta testers and early adopters providing feedback

## 🎯 Project Roadmap

### **Current Phase: Infrastructure Completion**
- ✅ Core CLI functionality operational
- 🚧 Test stabilization (220 tests requiring fixes)
- 🚧 Agent integration completion
- ⏳ Documentation alignment

### **Next Phase: Production Readiness**
- Production-grade error handling
- Performance optimization and validation
- Comprehensive user testing
- Installation and distribution improvements

### **Future Vision**
- Community template marketplace
- IDE integrations (VS Code, JetBrains)
- Enterprise features and team management
- ML-enhanced project analysis

---

**Claude Builder has achieved significant infrastructure milestones and is positioned for successful completion with focused effort on test stabilization and agent integration.**
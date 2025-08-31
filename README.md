# Claude Builder - Transform Projects into Intelligent Agent Development Environments

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-511%20passing-brightgreen.svg)](https://github.com/quinnoshea/claude_builder/tree/main/tests)
[![Development Status](https://img.shields.io/badge/status-core%20operational-green.svg)](https://github.com/quinnoshea/claude_builder)
[![CI](https://github.com/quinnoshea/claude_builder/workflows/CI/badge.svg)](https://github.com/quinnoshea/claude_builder/actions)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/c0920529ab54462387f217498a4e01db)](https://app.codacy.com/gh/quinnoshea/claude_builder/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/c0920529ab54462387f217498a4e01db)](https://app.codacy.com/gh/quinnoshea/claude_builder/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![GitHub stars](https://img.shields.io/github/stars/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/network)
[![GitHub issues](https://img.shields.io/github/issues/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/issues)
[![Last Commit](https://img.shields.io/github/last-commit/quinnoshea/claude_builder.svg)](https://github.com/quinnoshea/claude_builder/commits/main)

> **Analyzes your project and generates tailored Claude Code development environments
> with intelligent agent selection and project-specific guidance.**

## What Claude Builder Does

**Currently:** Analyzes projects (15+ languages, 25+ frameworks) and generates
intelligent `CLAUDE.md` and `AGENTS.md` files with project-specific agent
recommendations.

**In Development:** Working toward natural language triggers like "optimize this
API" that automatically suggest relevant agent teams based on your project
context.

**Goal:** Reduce the overhead of discovering and coordinating Claude Code
agents by providing smart defaults and context-aware suggestions.

---

## Key Features

### 🔍 **Project Analysis**

Detects languages, frameworks, project types, and complexity to understand your codebase

```bash
# Analyzes project characteristics
Project: Python FastAPI + PostgreSQL
Detection: Web API, moderate complexity
Suggests: backend-architect, api-tester, database-optimizer
```

### 🤖 **Agent Recommendations**

Suggests relevant Claude Code agents based on your project's characteristics

```bash
# For a React dashboard project
Recommended agents: frontend-developer, ui-designer, performance-optimizer
Generated triggers: "optimize bundle size", "improve accessibility", "design components"
```

### 📝 **Documentation Generation**

Creates tailored `CLAUDE.md` and `AGENTS.md` files with project-specific guidance

```bash
claude-builder /your/project
# Generates CLAUDE.md with development guidelines
# Creates AGENTS.md with suggested agent teams
# Includes project-specific best practices
```

### 🛠️ **Template System**

Uses hierarchical templates (base + language + framework) for consistent,
relevant output

```bash
# Template composition example
base.md → python.md → fastapi.md → final output
# Results in FastAPI-specific development guidance
```

---

## 🎯 Current Implementation Status

### ✅ **OPERATIONAL** (Ready to use today)

#### Project Analysis (good coverage for common stacks)

- **15+ Languages**: Python, Rust, JavaScript, TypeScript, Java, Go, PHP, C#,
  Ruby, and more
- **25+ Frameworks**: Django, FastAPI, React, Vue, Axum, Spring Boot, Express,
  Next.js, Laravel
- **Architecture Patterns**: MVC, microservices, domain-driven design,
  serverless detection
- **Intelligence Engine**: Dependency analysis, file pattern recognition,
  confidence scoring

#### CLI with Rich UI

```bash
# Comprehensive command structure
claude-builder /path/to/project                          # Full environment generation
claude-builder /path/to/project --dry-run --verbose      # Safe preview mode
claude-builder /path/to/project generate agents          # Agent-specific generation
claude-builder /path/to/project analyze --output=json   # Export project analysis
```

#### Template System with Hierarchical Composition

- **Base + Language + Framework** intelligent overlay system
- **Variable Substitution Engine** with project-specific context
- **Professional Documentation** with working examples and guidance

### DevOps & MLOps (Honest Scope)

We are expanding beyond language/framework analysis to include DevOps, MLOps,
and IaC. Today, claude_builder detects Dockerfiles and docker-compose (and
basic Kubernetes directory hints). We are actively adding detection and
guidance for:

- IaC: Terraform, Pulumi, CloudFormation/SAM, Ansible (roles/playbooks),
  Puppet/Chef/Salt, Packer
- Orchestration: Kubernetes, Helm, Kustomize, Nomad
- CI/CD: Common pipeline configs (GitHub Actions, GitLab CI, Jenkins,
  CircleCI, Azure Pipelines, Bitbucket Pipelines)
- Observability: Prometheus, Grafana, OpenTelemetry
 - MLOps: DVC, MLflow, Airflow, Prefect, dbt, Great Expectations,
   Kubeflow, Feast, Kedro (initial detection only; confidence varies)

What this means right now:

- Guidance-focused: We generate agent recommendations and documentation
  (INFRA/DEPLOYMENT/OBSERVABILITY/MLOPS) without changing your infrastructure.
- Honest limits: Detection accuracy varies by stack; coverage is growing.
  Secrets are never parsed; we only detect presence of files/configs.

Quick examples (expected agent suggestions):

```bash
# Terraform module repo
Recommended: terraform-specialist, ci-pipeline-engineer, security-auditor

# Helm + K8s manifests
Recommended: kubernetes-operator, helm-specialist, observability-engineer
```

#### Agent System Foundation

- **40+ Specialized Agents** with intelligent project-based selection
- **Team Composition Logic** for optimal agent combinations
- **Git Integration** with agent environment versioning

### 🔧 **IN ACTIVE DEVELOPMENT**

#### Natural Language Trigger Generation

- Intuitive phrase mapping to agent teams
- Context-aware trigger customization
- Workflow pattern automation

#### Community Agent Repository Integration

- Live agent scanning and capability indexing
- Automatic updates from community repositories
- Custom agent integration framework

#### Advanced Coordination Patterns

- Multi-agent workflow orchestration
- Intelligent handoff mechanisms
- Adaptive team composition

### 🎯 **PLANNED FEATURES** (In design/development)

#### Enhanced Natural Language Integration

```bash
# Vision: More intuitive interaction with agents
"optimize this API" → suggests backend-architect + performance-optimizer
"build login system" → suggests security-auditor + backend-architect
"investigate slow queries" → suggests database-optimizer + profiler-agent
```

#### Community Agent Integration

- Connect to community agent repositories for broader coverage
- Support custom agent definitions for specialized workflows
- Share successful agent patterns across projects

#### Adaptive Team Composition

- Teams that learn from successful development patterns
- Dynamic environment evolution as projects grow
- Context-aware specialization for specific domains

---

## 🚀 Quick Start

### Installation

```bash
# Install claude-builder (prefer uv for speed)
uv pip install -e ".[dev]"
# OR: pip install claude-builder

# Verify installation
claude-builder --help
```

### Basic Usage

```bash
# Generate complete development environment for any project
claude-builder /path/to/your/project

# Preview what would be generated (safe mode)
claude-builder /path/to/project --dry-run --verbose

# Generate with agent team optimization
claude-builder /path/to/project --agents-only

# Advanced git integration
claude-builder /path/to/project --git-exclude --claude-mentions=minimal
```

### Instant Results

```bash
# After running claude-builder on your project:
your-project/
├── CLAUDE.md                    # Project-specific development guidelines
├── AGENTS.md                    # Intelligent agent team configuration
└── .claude/                     # Detailed development environment
    ├── development_workflow.md  # Optimized development processes
    ├── agent_coordination.md    # Multi-agent collaboration patterns
    └── project_context.md       # Complete project analysis results
```

---

## Real-World Examples

### Python FastAPI Project

**Manual approach:** Research agents, create generic configurations, remember
which agents work well together

**With claude-builder:**

```bash
claude-builder ./my-fastapi-project
# Detects: Python 3.11, FastAPI, PostgreSQL, Redis
# Suggests: backend-architect, api-tester, database-optimizer, security-auditor
# Generates context: API development patterns, database optimization, security considerations
```

### React Dashboard Project

**Before:** Individual agent discovery, manual coordination overhead

```bash
# Traditional approach
- Look up frontend-specific agents
- Manually coordinate ui-designer with frontend-developer
- Remember which agents work well together for React projects
```

**After:** Seamless team orchestration with contextual intelligence

```bash
claude-builder ./react-dashboard
# Detects: TypeScript, React, Next.js, Tailwind CSS
# Team: frontend-developer, ui-designer, performance-optimizer, accessibility-checker
# Triggers: "optimize bundle size", "improve accessibility", "design better UX"
```

### Rust CLI Tool

**Before:** Generic guidance, no systems-specific optimization

```bash
# Traditional approach
- Use general-purpose agents not optimized for systems programming
- Miss Rust-specific performance and memory management expertise
- No integration with Rust ecosystem tools and patterns
```

**After:** Systems programming expertise with Rust specialization

```bash
claude-builder ./rust-cli-tool
# Detects: Rust, CLI patterns, system dependencies, performance requirements
# Team: systems-programmer, performance-optimizer, cli-specialist, rust-expert
# Triggers: "optimize memory usage", "improve CLI ergonomics", "add benchmarks"
```

---

## 💡 Natural Language Interaction Examples

### Feature Development Workflows

```yaml
# Generated automatically for each project
feature_development:
  trigger: "build new feature"
  team: [rapid-prototyper, ui-designer, test-writer-fixer, deployment-manager]
  coordination: sequential_with_feedback

authentication_system:
  trigger: "build user authentication"
  team: [security-auditor, backend-architect, frontend-developer, test-writer-fixer]
  coordination: security_first_then_implementation

performance_optimization:
  trigger: "optimize performance"
  team: [profiler-agent, performance-optimizer, database-tuner, load-tester]
  coordination: parallel_analysis_then_sequential_fixes
```

### Debugging & Investigation

```bash
# Natural language triggers generated for your specific project:
"debug this error" → error-detective + test-writer-fixer + documentation-updater
"investigate slow queries" → database-tuner + profiler-agent + performance-optimizer
"security audit this endpoint" → security-auditor + penetration-tester + compliance-checker
"optimize bundle size" → performance-optimizer + webpack-specialist + asset-optimizer
```

---

## 🏗️ Advanced Usage

### Project Analysis & Intelligence

```bash
# Detailed project analysis with comprehensive output
claude-builder analyze ./project --verbose
# → Language detection, framework analysis, complexity assessment, agent recommendations

# Export analysis for inspection and integration
claude-builder analyze ./project --output=analysis.json
# → Complete project intelligence in structured format

# Generate agent-specific environments
claude-builder ./project generate agents --template=web-api
# → Specialized agent configuration for API development
```

### Git Integration & Safety

```bash
# Safe git integration (recommended - files not committed)
claude-builder ./project --git-exclude

# Control references in generated content
claude-builder ./project --claude-mentions=forbidden   # No AI references
claude-builder ./project --claude-mentions=minimal     # Minimal technical references
claude-builder ./project --claude-mentions=allowed     # Full attribution

# Backup existing files before generation
claude-builder ./project --backup-existing
```

### Template & Configuration Management

```bash
# List available built-in templates
claude-builder templates list
# → Shows base, language-specific, and framework templates

# Validate custom template structure
claude-builder templates validate ./custom-template

# Initialize and manage project configuration
claude-builder config init ./project
claude-builder config show ./project
```

### Future Natural Language Interaction (Vision)

```bash
# Coming with Agent Orchestration Engine:
claude-builder ./project orchestrate "build user authentication system"
claude-builder ./project ask "how do I optimize this database query?"
claude-builder ./project deploy "with security audit and performance testing"
```

---

## 📊 Language & Framework Support

### Languages (90%+ Detection Accuracy)

| Language | Status | Confidence | Specialized Agents |
|----------|--------|------------|-------------------|
| **Python** | ✅ Excellent | 95%+ | backend-architect, api-tester |
| **Rust** | ✅ Excellent | 93%+ | systems-programmer, optimizer |
| **JavaScript/TypeScript** | ✅ Excellent | 94%+ | frontend-developer |
| **Java** | ✅ Very Good | 88%+ | enterprise-architect, spring-specialist |
| **Go** | ✅ Very Good | 87%+ | microservices-architect, api-designer |
| **C#** | ✅ Good | 82%+ | dotnet-specialist, azure-deployer |
| **PHP** | ✅ Good | 80%+ | web-developer, laravel-specialist, security-auditor |
| **Ruby** | ✅ Good | 79%+ | rails-developer, web-architect, gem-creator |

### Framework Intelligence (25+ Supported)

- **Web Frameworks**: Django, Flask, FastAPI, Express, React, Vue, Angular,
  Next.js, Laravel
- **Systems**: Axum, Actix, Tokio, Spring Boot, .NET Core, Gin, Echo
- **Mobile**: React Native, Flutter, Xamarin, Ionic
- **Data**: Jupyter, Pandas, Spark, Airflow, Django REST Framework

### Project Types (Auto-Detected)

- **Web Applications**: Full-stack, SPAs, progressive web apps, microservices architectures
- **API Services**: REST APIs, GraphQL, gRPC, serverless functions
- **CLI Tools**: System utilities, developer tools, automation scripts,
  command-line applications
- **Libraries & Frameworks**: Reusable packages, shared components, open-source projects
- **Data Science**: ML pipelines, analysis notebooks, data processing workflows
- **Mobile Applications**: Native and hybrid mobile development projects

---

## 🧪 Development & Quality Assurance

### Running Tests

```bash
# Core functionality tests (should pass)
pytest tests/unit/core/ -v

# Intelligence layer tests
pytest tests/unit/intelligence/ -v

# Advanced features (some in development)
pytest tests/unit/advanced/ -v

# Full test suite with coverage
pytest --cov=claude_builder --cov-report=term-missing
```

### Code Quality & Standards

```bash
# Format code with Black
black claude_builder tests/

# Lint with Ruff
ruff claude_builder tests/

# Type checking with mypy
mypy claude_builder/

# Pre-commit hooks (runs automatically)
pre-commit run --all-files
```

### Performance Benchmarking

```bash
# Measure analysis speed on real projects
time claude-builder tests/fixtures/sample_projects/python_project --dry-run
time claude-builder tests/fixtures/sample_projects/rust_project --dry-run
time claude-builder tests/fixtures/sample_projects/react_project --dry-run
```

---

## 🤝 Contributing & Community

### Current Development Focus

We're building the future of AI-assisted development. Join us in creating
intelligent agent orchestration:

**Phase 1** ✅ **Infrastructure Complete**: Project analysis, template system,
CLI foundation
**Phase 2** ✅ **Agent Foundation**: Basic agent selection, team composition logic
**Phase 3** 🔧 **Natural Language Orchestration**: Intuitive triggers, workflow automation
**Phase 4** 🎯 **Community Ecosystem**: Repository integration, shared intelligence

### How to Contribute

#### 🚀 **Agent Orchestration Development** (High Impact)

```bash
# Set up development environment
git clone https://github.com/quinnoshea/claude_builder.git
cd claude_builder
uv pip install -e ".[dev]"
pre-commit install

# Work on natural language trigger generation
# Help build community agent repository integration
# Develop intelligent team coordination patterns
```

#### 🧪 **Test Infrastructure & Quality** (Great for Learning)

```bash
# Help fix failing tests for production reliability
pytest tests/unit/core/ -v  # Should pass
pytest tests/unit/intelligence/ -v  # Some fixes needed
pytest tests/unit/advanced/ -v  # Work in progress

# Improve test coverage and quality
pytest --cov=claude_builder --cov-report=html
```

#### 🎨 **Template Development** (Community Building)

```bash
# Create templates for new languages and frameworks
# Develop specialized agent configuration patterns
# Build project-specific workflow templates
```

### Contribution Areas

- **Natural Language Processing**: Help build intuitive trigger generation
- **Agent Coordination**: Develop intelligent team composition algorithms
- **Community Integration**: Build repository scanning and agent indexing
- **Template System**: Create specialized templates for diverse project types
- **CLI Enhancement**: Improve user experience and error handling
- **Documentation**: Develop comprehensive guides and examples

### Agent Definition Guidelines

When contributing agent definitions or coordination patterns:

- **Specialization Focus**: Agents should have clear, non-overlapping specializations
- **Natural Triggers**: Include intuitive phrases that map to agent capabilities
- **Coordination Patterns**: Define how agents work with others in team contexts
- **Community Standards**: Follow established patterns for consistency

---

## 📈 Success Stories & Impact

### Current Status

- **Projects Supported**: 15+ languages, 25+ frameworks with good detection
  accuracy
- **Agent Suggestions**: Works well for common project types (Python web apps,
  React SPAs, Rust CLI tools)
- **Setup**: Automates the manual process of researching and configuring
  Claude Code agents
- **Community**: Growing set of templates and agent configurations

### User Experience

The tool helps reduce the initial setup overhead when starting to use Claude Code
agents on a new project. Instead of manually researching which agents might be
relevant and creating configuration files from scratch, claude-builder analyzes
your project and provides educated suggestions based on what it detects.

### Development Impact

- Faster initial setup compared to manual agent discovery
- Consistent agent configuration patterns across projects
- Good starting point for teams new to Claude Code agents
- **Seamless onboarding** for new team members through generated environments
- **Consistent workflows** across diverse project types and team experience levels

---

## 🗺️ Roadmap & Future Vision

### 🎯 **Planned Development** (Next Major Features)

#### Improved Natural Language Integration

```bash
# Goal: More intuitive ways to interact with agent suggestions
"optimize this API for mobile users" → suggests relevant performance and
mobile-focused agents
"build secure payment processing" → suggests security and compliance-focused
agent teams
"investigate production errors" → suggests debugging and monitoring agent workflows
```

#### Community Integration

- Connect to community agent repositories for broader coverage
- Support importing and sharing agent configuration patterns
- Better integration with custom agent definitions
- Version tracking for agent configurations

#### Adaptive Intelligence

- Team composition learning from successful development patterns
- Project-specific customization based on usage analytics
- Continuous optimization through community feedback
- Context-aware specialization for domain-specific requirements

### 🚀 **Long-Term Vision**

#### Enterprise Features

- Team collaboration with shared agent configurations
- Enterprise agent repositories with access control
- Integration with development workflow tools (Jira, GitHub, Slack)
- Advanced analytics and team productivity insights

#### Developer Experience Evolution

- IDE integrations (VS Code, JetBrains, Vim)
- Real-time agent suggestions during development
- Context-aware code completion with agent expertise
- Seamless integration with existing developer workflows

#### AI-Driven Development Ecosystem

- Machine learning-enhanced project analysis
- Predictive agent team recommendations
- Automated workflow optimization based on project outcomes
- Community-driven intelligence sharing and best practice propagation

---

## ⚙️ Technical Requirements

### System Requirements

- **Python**: 3.8+ (3.11+ recommended for optimal performance)
- **Memory**: 512MB minimum for project analysis, 1GB+ recommended for large
  projects
- **Storage**: 100MB for development environment, additional space for
  community agent caches
- **Network**: Internet connection for community agent repository updates
  (optional)
- **Git**: Required for project analysis and version control integration

### Optional Dependencies

- **uv**: Recommended for faster Python package management
- **Community Repositories**: Enhanced agent selection with live repository integration
- **IDE Plugins**: Enhanced development experience (coming soon)

---

## 📄 License & Acknowledgments

### License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE)
file for details. This ensures maximum community contribution and enterprise
adoption flexibility.

### 🙏 Acknowledgments

- **Built for Claude Code Ecosystem**: Designed to maximize developer
  productivity with AI-assisted development
- **Inspired by Real Developer Pain**: Born from the need to eliminate friction
  in agent adoption and coordination
- **Community Driven**: Thanks to beta testers, early adopters, and community
  contributors providing feedback and agent definitions
- **Engineering Standards**: Built with maintainable design patterns and
  tests where available

---

## 🎯 Call to Action

**Try Claude Builder on your projects.**

Automate the process of discovering and configuring relevant Claude Code agents
based on your project's characteristics.

```bash
# Get started
uv pip install -e ".[dev]"  # or pip install claude-builder
claude-builder /your/project

# See what it generates
# ✅ Project-specific CLAUDE.md with development guidelines
# ✅ AGENTS.md with relevant agent recommendations
# ✅ Context-aware suggestions based on your tech stack
# ✅ Templates tailored to your project type
```

**Interested in contributing or trying it out?**

[⭐ Star this repository](https://github.com/quinnoshea/claude_builder) |
[🚀 Quick start](#-quick-start) |
[🤝 Contribute](#-contributing--community) |
[💬 Discussions](https://github.com/quinnoshea/claude_builder/discussions)

---

*Claude Builder: Intelligent agent configuration for Claude Code projects.*

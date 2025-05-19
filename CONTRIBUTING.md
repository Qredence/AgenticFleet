# Contributing to AgenticFleet

## 🤝 Welcome Contributors!

AgenticFleet is an open-source project that thrives on community contributions. Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated!

## 📋 Contribution Guidelines

### 1. Ways to Contribute

- Reporting bugs
- Suggesting enhancements
- Writing code
- Improving documentation
- Reviewing pull requests

### 2. Development Setup

#### Prerequisites

- Python 3.10-3.12
- `uv` package manager
- `pre-commit`

#### Local Development Environment

```bash
# Clone the repository
git clone https://github.com/qredence/agenticfleet.git
cd agenticfleet

# Create virtual environment
uv pip venv
source .venv/bin/activate

# Install development dependencies
uv pip install -e '.[dev]'
pre-commit install
```

### 3. ⚠️ Package Modification Warning

#### Editable Installation Risks

- **NOT recommended for production**
- May introduce unsupported behaviors
- Intended ONLY for core contributors
- Local modifications void official support

#### Modification Guidelines

1. For bug fixes or features:

   - Open a GitHub Issue first
   - Discuss proposed changes
   - Submit a Pull Request

2. Local Modifications:
   - Create a fork of the repository
   - Make changes in your fork
   - Submit a Pull Request
   - Do NOT modify the package directly

### 4. Contribution Process

#### Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run pre-commit checks
5. Write/update tests
6. Update documentation
7. Submit a Pull Request

#### Pre-Commit Checks

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Specific checks
pre-commit run black
pre-commit run ruff
pre-commit run mypy
```

### 5. Pull Request Guidelines

- Use descriptive commit messages
- Reference related issues
- Explain the motivation for changes
- Include tests for new functionality
- Update documentation

### 6. Code of Conduct

We follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Be respectful, inclusive, and constructive.

### 7. Licensing

- Contributions are under Apache 2.0 License
- Preserve original copyright notices
- Clearly document significant modifications

## 📞 Support and Communication

- 📧 Email: support@qredence.ai
- 🐛 Issues: https://github.com/Qredence/AgenticFleet/issues
- 💬 Discussions: https://github.com/Qredence/AgenticFleet/discussions

**Remember:** Collaboration, clear communication, and mutual respect are key to successful open-source development!

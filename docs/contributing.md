# Contributing to AgenticFleet

We love your input! We want to make contributing to AgenticFleet as easy and transparent as possible.

## Development Process

1. Fork the repo and create your branch from `main`.
2. Install development dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```
3. Make your changes.
4. Ensure your code follows our standards:

   ```bash
   # Format code
   black .
   isort .

   # Run linters
   ruff check .

   # Run tests
   pytest
   ```

5. Submit a pull request!

## Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **ruff** for linting
- **mypy** for type checking

Configuration for these tools is in `pyproject.toml`.

## Pull Request Process

1. Update documentation for any changed functionality
2. Update the README.md if needed
3. Update the CHANGELOG.md following our format
4. The PR must pass all CI checks
5. Get approval from at least one maintainer

## Pull Request Template

```markdown
**What does this PR do?**

- [ ] Fix a bug
- [ ] Add a feature
- [ ] Update dependencies
- [ ] Refactor code
- [ ] Tests
- [ ] Other (please specify)

**How should this be tested?**

Please specify how you tested this pull request.

**Screenshots**

Add relevant screenshots if applicable.

**Checklist**

- [ ] I have added an entry to the changelog
- [ ] I have updated the documentation
- [ ] I have tested this PR
- [ ] I have added the correct labels
```

## Setting Up Development Environment

1. Clone the repository:

   ```bash
   git clone https://github.com/qredence/agenticfleet.git
   cd agenticfleet
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   uv pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=agentic_fleet

# Run with verbose output
pytest -v
```

## Documentation

We use Mintify for documentation. After making changes:

1. Build documentation:

   ```bash
   mintify build
   ```

2. Preview locally:
   ```bash
   mintify serve
   ```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a release PR
4. After merge, tag the release:
   ```bash
   git tag -a v0.x.x -m "Version 0.x.x"
   git push origin v0.x.x
   ```

## Getting Help

- Join our [Discord](https://discord.gg/ebgy7gtZHK)
- Create an issue
- Contact maintainers

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.

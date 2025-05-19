# AgenticFleet Cursor Rules

This directory contains rules, guidelines, and best practices for working on the AgenticFleet codebase. These rules help maintain code quality, consistency, and structure across the project.

## Directory Structure

- **linting/**: Configuration files for linting tools
  - `pylint.toml`: Pylint configuration
  
- **formatting/**: Configuration files for code formatting
  - `black.toml`: Black formatter configuration
  
- **style_guide/**: Coding style guidelines
  - `python_style.md`: Python coding style guide
  
- **best_practices/**: Best practices and patterns
  - `agent_patterns.md`: Design patterns for implementing agents

## How to Use These Rules

### Linting

To use the pylint configuration:

```bash
pylint --rcfile=.cursor/rules/linting/pylint.toml src/
```

### Formatting

To use the Black configuration:

```bash
black --config=.cursor/rules/formatting/black.toml src/
```

### VS Code / Cursor Integration

Add the following to your `.vscode/settings.json` to integrate these rules:

```json
{
  "python.linting.pylintEnabled": true,
  "python.linting.enabled": true,
  "python.linting.pylintArgs": [
    "--rcfile=.cursor/rules/linting/pylint.toml"
  ],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": [
    "--config=.cursor/rules/formatting/black.toml"
  ],
  "editor.formatOnSave": true
}
```

## Rule Enforcement

These rules are enforced through:

1. **Pre-commit hooks**: Checking code before commits
2. **CI/CD Pipeline**: Enforcing rules in GitHub workflows
3. **IDE Integration**: Real-time feedback in your editor
4. **Code Review**: Manual review against guidelines

## Contributing to Rules

If you'd like to suggest changes to these rules:

1. Create a branch with your proposed changes
2. Submit a pull request with justification
3. Get approval from at least one maintainer

## Rule Hierarchy

In case of conflicting rules, follow this hierarchy:

1. Language specifications (Python syntax rules)
2. Project-specific standards (this repository)
3. PEP 8 and other Python conventions
4. General programming best practices 
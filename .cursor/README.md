# Cursor Configuration for AgenticFleet

This directory contains configuration files for the Cursor IDE when working with the AgenticFleet project. It provides a comprehensive set of rules, settings, and utilities to enhance code quality and development workflow.

## Directory Structure

- **settings/**: IDE settings and configurations
  - `cursor.json`: General editor and project settings
  - `keybindings.json`: Custom key bindings
  - `project-structure.json`: Project structure overview
  - `code-analysis.json`: Code analysis and linting rules

- **snippets/**: Code snippets for faster development
  - `python.json`: Python-specific code snippets for common patterns

- **extensions/**: Custom extension configurations

- **cache/**: Temporary files and caching data

- **rules/**: Coding standards and best practices
  - `best_practices/`: Best practices for code organization and patterns
  - `formatting/`: Code formatting rules and settings
  - `linting/`: Linting rules and standards
  - `style_guide/`: Code style conventions and guidelines
  - `isolation_rules/`: Memory bank mode rules for systematic development
    - `Level2/`: Level 2 complexity workflows
    - `Level3/`: Level 3 complexity workflows
    - `Level4/`: Level 4 complexity workflows
    - `visual-maps/`: Visual maps for code organization and processes

## Usage

These configurations are automatically loaded by Cursor IDE when you open the project. You can customize these files to match your development preferences.

### Key Settings

- Code formatting: Uses Black for Python files
- Tab size: 4 spaces
- Python path configuration: Includes the `src` directory
- Custom keybindings for AI features
- Memory bank modes for structured development

### Custom Snippets

We've included several useful snippets for AgenticFleet development:

- `agent`: Template for creating a new agent class
- `clstep`: Template for Chainlit steps
- `fapiendpoint`: Template for FastAPI endpoint
- `errorhandler`: Template for standardized error handling

### Memory Bank Modes

The `.cursor/rules/isolation_rules` directory contains memory bank mode configurations that help structure the development process:

- **Planning Mode**: For planning architecture and features
- **Creative Mode**: For brainstorming solutions
- **Implementation Mode**: For systematically implementing planned changes
- **Reflection Mode**: For reviewing and refining code

## Customizing

Feel free to modify these files to match your preferences. Changes will be applied when you restart Cursor or reload the window. 
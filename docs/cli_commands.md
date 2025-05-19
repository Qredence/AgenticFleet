# CLI Commands Reference

This document provides a comprehensive guide to all available CLI commands in AgenticFleet.

## Basic Commands

### Start Command

Start the AgenticFleet application:

```bash
agenticfleet start [OPTIONS]
```

Options:

- `--host TEXT` - Host to bind to (default: localhost)
- `--port INTEGER` - Port to bind to (default: 8000)
- `--debug` - Enable debug mode
- `no-oauth` - Start without OAuth authentication

Examples:

```bash
# Start with default settings
agenticfleet start

# Start on custom port without OAuth
agenticfleet start no-oauth --port 8001

# Start in debug mode
agenticfleet start --debug
```

### Status Command

Check the status of AgenticFleet instances:

```bash
agenticfleet status [OPTIONS]
```

Options:

- `--json` - Output in JSON format

Examples:

```bash
# Check status
agenticfleet status

# Get status in JSON format
agenticfleet status --json
```

### Stop Command

Stop running AgenticFleet instances:

```bash
agenticfleet stop [OPTIONS]
```

Options:

- `--force` - Force stop all instances
- `--port INTEGER` - Stop specific instance on port

Examples:

```bash
# Stop all instances
agenticfleet stop

# Force stop specific instance
agenticfleet stop --port 8000 --force
```

## Configuration Commands

### Config Command

Manage AgenticFleet configuration:

```bash
agenticfleet config [OPTIONS] COMMAND [ARGS]...
```

Subcommands:

- `get` - Get configuration value
- `set` - Set configuration value
- `list` - List all configuration values
- `reset` - Reset configuration to defaults

Examples:

```bash
# List all configuration
agenticfleet config list

# Set a configuration value
agenticfleet config set model.provider azure

# Get a configuration value
agenticfleet config get model.provider
```

### Init Command

Initialize a new AgenticFleet configuration:

```bash
agenticfleet init [OPTIONS]
```

Options:

- `--force` - Overwrite existing configuration
- `--template TEXT` - Use specific template

Examples:

```bash
# Initialize with defaults
agenticfleet init

# Force initialize with specific template
agenticfleet init --force --template production
```

## Development Commands

### Dev Command

Start AgenticFleet in development mode:

```bash
agenticfleet dev [OPTIONS]
```

Options:

- `--reload` - Enable auto-reload on code changes
- `--debug` - Enable debug mode

Examples:

```bash
# Start in development mode with auto-reload
agenticfleet dev --reload

# Start in development mode with debugging
agenticfleet dev --debug
```

### Test Command

Run AgenticFleet tests:

```bash
agenticfleet test [OPTIONS]
```

Options:

- `--coverage` - Generate coverage report
- `--verbose` - Verbose output

Examples:

```bash
# Run all tests
agenticfleet test

# Run tests with coverage
agenticfleet test --coverage
```

## Utility Commands

### Clean Command

Clean AgenticFleet cache and temporary files:

```bash
agenticfleet clean [OPTIONS]
```

Options:

- `--cache` - Clean only cache files
- `--all` - Clean all temporary files
- `--dry-run` - Show what would be cleaned

Examples:

```bash
# Clean cache
agenticfleet clean --cache

# Clean everything
agenticfleet clean --all
```

### Version Command

Display version information:

```bash
agenticfleet version [OPTIONS]
```

Options:

- `--json` - Output in JSON format
- `--check` - Check for updates

Examples:

```bash
# Show version
agenticfleet version

# Check for updates
agenticfleet version --check
```

## Environment Commands

### Env Command

Manage environment variables:

```bash
agenticfleet env [OPTIONS] COMMAND [ARGS]...
```

Subcommands:

- `list` - List environment variables
- `set` - Set environment variable
- `unset` - Unset environment variable

Examples:

```bash
# List all environment variables
agenticfleet env list

# Set environment variable
agenticfleet env set DEBUG true

# Unset environment variable
agenticfleet env unset DEBUG
```

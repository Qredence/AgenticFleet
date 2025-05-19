# Configuration Directory

This directory contains configuration files for the Agentic Fleet application.

## Files

- **model_config.yaml**: Configuration for AI models used in the application
- **user_settings.json**: User-specific settings and preferences

## Usage

These configuration files are loaded by the application at runtime. They can be modified to customize the behavior of the application.

For development, you can create local versions of these files (e.g., `model_config.local.yaml`) which will be loaded instead of the default files if they exist.

## Environment Variables

Many configuration options can also be set using environment variables. See the `.env.example` file in the project root for a list of available environment variables.

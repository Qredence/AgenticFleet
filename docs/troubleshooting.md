# Troubleshooting Guide

This guide helps you resolve common issues with AgenticFleet.

## Port and Process Issues

### Port Already in Use

**Problem**: You see an error like "Address already in use" when starting AgenticFleet.

**Solutions**:

1. **Check Running Instances**:

   ```bash
   agenticfleet status
   ```

2. **Use Different Port**:

   ```bash
   agenticfleet start --port 8001
   ```

3. **Clean Up Processes**:
   ```bash
   agenticfleet stop
   # Or force stop if needed
   agenticfleet stop --force
   ```

### Multiple Instances

**Problem**: Multiple instances running causing conflicts.

**Solutions**:

1. **List Running Instances**:

   ```bash
   ps aux | grep agenticfleet
   ```

2. **Stop All Instances**:

   ```bash
   agenticfleet stop --all
   ```

3. **Use Process Management**:
   ```bash
   # Check PID file
   cat /tmp/agenticfleet.pid
   ```

## Authentication Issues

### OAuth Configuration

**Problem**: OAuth authentication not working.

**Solutions**:

1. **Verify Environment Variables**:

   ```bash
   agenticfleet config list | grep OAUTH
   ```

2. **Check Callback URL**:

   - Ensure it matches GitHub OAuth settings
   - Default: `http://localhost:8000/auth/callback`

3. **Debug OAuth Flow**:
   ```bash
   agenticfleet start --debug
   ```

### Token Issues

**Problem**: Authentication tokens not working or expired.

**Solutions**:

1. **Clear Token Cache**:

   ```bash
   agenticfleet clean --auth-cache
   ```

2. **Regenerate Tokens**:
   - Log out and log back in
   - Check token expiration in settings

## Model Provider Issues

### Azure OpenAI

**Problem**: Can't connect to Azure OpenAI.

**Solutions**:

1. **Verify Credentials**:

   ```bash
   agenticfleet config verify azure
   ```

2. **Check Endpoint**:

   - Ensure endpoint URL is correct
   - Test connection:
     ```bash
     curl -I $AZURE_OPENAI_ENDPOINT
     ```

3. **Debug Mode**:
   ```bash
   agenticfleet start --debug --model-provider azure
   ```

### Rate Limiting

**Problem**: Hitting API rate limits.

**Solutions**:

1. **Check Usage**:

   ```bash
   agenticfleet status --usage
   ```

2. **Adjust Settings**:
   ```bash
   # Increase request delay
   agenticfleet config set model.request_delay 1.0
   ```

## Performance Issues

### High Memory Usage

**Problem**: Application using too much memory.

**Solutions**:

1. **Monitor Usage**:

   ```bash
   agenticfleet status --resources
   ```

2. **Clear Cache**:

   ```bash
   agenticfleet clean --cache
   ```

3. **Adjust Settings**:
   ```bash
   # Reduce cache size
   agenticfleet config set cache.max_size 1000
   ```

### Slow Response Times

**Problem**: Agents responding slowly.

**Solutions**:

1. **Check Performance**:

   ```bash
   agenticfleet status --performance
   ```

2. **Optimize Settings**:
   ```bash
   # Adjust timeouts
   agenticfleet config set agent.timeout 30
   ```

## Installation Issues

### Dependency Conflicts

**Problem**: Package conflicts during installation.

**Solutions**:

1. **Clean Install**:

   ```bash
   uv pip uninstall agentic-fleet
   uv pip install agentic-fleet --no-deps
   uv pip install -r requirements.txt
   ```

2. **Check Dependencies**:
   ```bash
   uv pip check
   ```

### Browser Installation

**Problem**: Playwright browser installation fails.

**Solutions**:

1. **Manual Installation**:

   ```bash
   playwright install chromium --with-deps
   ```

2. **System Dependencies**:

   ```bash
   # Ubuntu/Debian
   sudo apt-get install -y libgbm-dev

   # macOS
   brew install webkit
   ```

## Logging and Debugging

### Enable Debug Logging

```bash
# Set log level
agenticfleet start --log-level DEBUG

# Save logs to file
agenticfleet start --log-file debug.log
```

### View Logs

```bash
# View recent logs
agenticfleet logs

# View specific component logs
agenticfleet logs --component agent
```

## Common Error Messages

### "No module named 'agentic_fleet'"

**Solution**:

```bash
# Reinstall package
uv pip install -e .
```

### "ImportError: cannot import name 'X'"

**Solution**:

```bash
# Update to latest version
uv pip install --upgrade agentic-fleet
```

## Getting Help

If you're still experiencing issues:

1. Check our [GitHub Issues](https://github.com/qredence/agenticfleet/issues)
2. Join our [Discord](https://discord.gg/ebgy7gtZHK)
3. Create a new issue with:
   - Error message
   - System information
   - Steps to reproduce

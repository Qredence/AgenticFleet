# Error Handling Best Practices

This document outlines the standard error handling patterns to use throughout the AgenticFleet codebase for consistency, reliability, and better user experience.

## 1. Exception Hierarchy

Always use the AgenticFleet exception hierarchy for raising and catching exceptions. This helps with consistent error handling and makes error propagation more predictable.

```python
from agentic_fleet.exceptions import (
    AgenticFleetError,
    AgentError,
    ConfigError,
    MessageProcessingError,
    ToolError,
)
```

### 1.1 Exception Class Hierarchy

```
AgenticFleetError (Base exception)
├── ConfigError
│   └── MissingConfigError
├── AgentError
│   ├── AgentInitializationError
│   ├── AgentExecutionError
│   ├── AgentNotFoundError
│   └── AgentTimeoutError
├── MessageProcessingError
│   ├── InvalidMessageError
│   └── MessageRoutingError
├── DatabaseError
│   ├── ConnectionError
│   └── QueryError
├── ToolError
│   ├── ToolExecutionError
│   └── ToolNotFoundError
└── APIError
    ├── AuthenticationError
    ├── AuthorizationError
    └── EndpointError
```

## 2. Exception Handling Patterns

### 2.1 Raising Exceptions

When raising exceptions:

1. Use the most specific exception type from the hierarchy
2. Include descriptive error messages
3. Use the `from` syntax to preserve the exception chain

```python
# Good
try:
    agent = agent_registry.get_agent(agent_id)
except KeyError:
    raise AgentNotFoundError(f"Agent with ID '{agent_id}' not found") from e

# Bad - generic exception
raise Exception("Agent not found")

# Bad - no context
raise AgentNotFoundError()
```

### 2.2 Exception Handling

When catching exceptions:

1. Catch specific exceptions, not `Exception` or bare `except:`
2. Log the exception with context
3. Either handle the exception appropriately or re-raise as a more specific type

```python
# Good
try:
    result = await agent.process_message(message)
except AgentExecutionError as e:
    logger.error(f"Error executing agent {agent.id}: {str(e)}")
    return Response(content="The agent encountered an error", error=True)
except AgentTimeoutError as e:
    logger.warning(f"Agent {agent.id} timed out: {str(e)}")
    return Response(content="The operation timed out", error=True)

# Bad - too broad
try:
    result = await agent.process_message(message)
except Exception as e:
    logger.error(f"Error: {str(e)}")
    return Response(content="An error occurred", error=True)
```

### 2.3 Logging Exceptions

Always include proper logging when handling exceptions:

1. Use the appropriate log level (`error` for serious issues, `warning` for less severe)
2. Include context in the log message
3. Use `exc_info=True` for full tracebacks when needed

```python
# Good
try:
    # Complex operation
except AgentError as e:
    logger.error(f"Agent error in {operation_name}: {str(e)}")
except DatabaseError as e:
    logger.error(f"Database error in {operation_name}: {str(e)}", exc_info=True)

# Bad - insufficient context
try:
    # Complex operation
except Exception as e:
    logger.error(f"Error: {str(e)}")
```

## 3. Error Recovery Patterns

### 3.1 Retry Pattern

Use the retry pattern for transient errors:

```python
async def perform_operation_with_retry(operation_func, max_retries=3, delay=1.0):
    """Perform an operation with retries for transient errors.
    
    Args:
        operation_func: Async function to execute
        max_retries: Maximum number of retry attempts
        delay: Base delay between retries (will be exponentially increased)
        
    Returns:
        The result of the operation
        
    Raises:
        The last exception encountered after all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await operation_func()
        except (ConnectionError, TimeoutError) as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (2 ** attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}. "
                    f"Retrying in {wait_time:.2f}s"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
    
    # If we get here, all retries failed
    raise last_exception
```

### 3.2 Fallback Pattern

Use fallbacks for non-critical operations:

```python
async def get_agent_with_fallback(agent_id, fallback_agent_id=None):
    """Get an agent with fallback if primary agent is unavailable.
    
    Args:
        agent_id: Primary agent ID
        fallback_agent_id: Fallback agent ID (optional)
        
    Returns:
        An agent instance
        
    Raises:
        AgentNotFoundError: If both primary and fallback agents are not found
    """
    try:
        return await agent_registry.get_agent(agent_id)
    except AgentNotFoundError:
        if fallback_agent_id:
            logger.warning(
                f"Primary agent '{agent_id}' not found, using fallback '{fallback_agent_id}'"
            )
            return await agent_registry.get_agent(fallback_agent_id)
        raise
```

## 4. User-Facing Error Messages

When returning errors to users:

1. Provide helpful but not overly technical messages
2. Include an error code or ID for support reference
3. Do not expose sensitive information or full stack traces

```python
# Good user-facing error
async def handle_api_request(request):
    try:
        result = await process_request(request)
        return {"status": "success", "data": result}
    except AgenticFleetError as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Error ID {error_id}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": {
                "message": "Unable to process your request at this time",
                "error_id": error_id
            }
        }
```

## 5. Context Managers

Use context managers for resource management:

```python
class DatabaseSession:
    """Context manager for database sessions."""
    
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.session = None
    
    async def __aenter__(self):
        try:
            self.session = await create_session(self.connection_string)
            return self.session
        except Exception as e:
            raise DatabaseError(f"Failed to create database session: {str(e)}") from e
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

# Usage
async def get_user_data(user_id):
    async with DatabaseSession(config.DATABASE_URL) as session:
        return await session.query(User).filter(User.id == user_id).first()
```

## 6. Error Boundaries

Implement error boundaries at API and UI layers to prevent cascading failures:

```python
async def api_error_boundary(request, call_next):
    """Middleware that catches all exceptions in the API layer."""
    try:
        return await call_next(request)
    except Exception as e:
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Unhandled API exception {error_id}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "message": "An unexpected error occurred",
                    "error_id": error_id
                }
            }
        )
```

## 7. Integration with Monitoring

Connect error handling with monitoring:

```python
def log_and_monitor_exception(e, context=None):
    """Log an exception and send it to monitoring service."""
    error_id = str(uuid.uuid4())[:8]
    
    # Local logging
    logger.error(f"Error {error_id}: {str(e)}", exc_info=True)
    
    # Send to monitoring (example)
    if monitoring_service:
        monitoring_service.track_exception(
            exception=e,
            properties={
                "error_id": error_id,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return error_id
```

## Conclusion

Following these error handling best practices ensures that:

1. Errors are properly categorized and contextualized
2. Debugging is easier with consistent logging
3. Users receive appropriate error messages
4. The system is more resilient through proper recovery patterns
5. Monitoring and tracking of errors is standardized

Always apply these patterns consistently throughout the codebase to improve error handling consistency and overall system reliability. 
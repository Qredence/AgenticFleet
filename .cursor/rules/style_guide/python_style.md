# AgenticFleet Python Style Guide

## Code Formatting

- Follow [PEP 8](https://peps.python.org/pep-0008/) with the following modifications:
  - Line length: 100 characters maximum
  - Use 4 spaces for indentation
  - Use Black for code formatting

## Imports

- Organize imports in the following order:
  1. Standard library imports
  2. Third-party libraries
  3. Local application imports
- Separate each group with a blank line
- Sort imports alphabetically within each group
- Use absolute imports for external packages, relative imports for internal modules

```python
# Standard library
import os
import sys
from typing import Dict, List, Optional, Union

# Third-party libraries
import chainlit as cl
from fastapi import APIRouter, Depends, HTTPException, status

# Local application
from agentic_fleet.core.agents import BaseAgent
from agentic_fleet.models import Response
```

## Naming Conventions

- **Classes**: `CamelCase`
- **Functions/Methods**: `snake_case`
- **Variables**: `snake_case`
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES`
- **Type variables**: `CamelCase` (same as classes)
- **Agents**: Always suffix with `Agent` (e.g., `CodingAgent`, `WebSearchAgent`)

## Type Hints

- Use type hints consistently for all function parameters and return values
- Use `Optional[T]` for parameters that can be `None`
- Use `Union[T1, T2]` for parameters that can be multiple types
- Use `Any` sparingly and only when necessary
- Use `Dict`, `List`, `Set` instead of `dict`, `list`, `set`

```python
def process_message(
    message: str, 
    context: Optional[Dict[str, Any]] = None
) -> Union[Response, List[Response]]:
    ...
```

## Docstrings

- Use Google-style docstrings
- Include descriptions for all parameters and return values
- Document exceptions that the function may raise
- Include usage examples for complex functions

```python
def process_message(message: str, token: Optional[CancellationToken] = None) -> Response:
    """
    Process an incoming message and generate a response.

    Args:
        message: The message content to process
        token: Optional cancellation token to cancel processing

    Returns:
        Response: The agent's response to the message

    Raises:
        ValueError: If the message format is invalid
    
    Example:
        >>> agent = CodingAgent()
        >>> response = await agent.process_message("Generate a hello world function")
        >>> print(response.content)
    """
```

## Error Handling

- Use specific exception types instead of bare `except:` clauses
- Log exceptions with appropriate levels (error, warning, info)
- Include context information in error messages
- Handle errors at the appropriate level of abstraction

```python
try:
    result = await some_function()
except ValueError as e:
    logger.error(f"Invalid input parameter: {str(e)}")
    raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
except SomeExternalException as e:
    logger.warning(f"External service error: {str(e)}")
    raise HTTPException(status_code=502, detail="External service unavailable")
```

## Async Patterns

- Use `async`/`await` consistently throughout the codebase
- Avoid mixing synchronous and asynchronous code
- Use appropriate async patterns for concurrency (asyncio, not threads)
- Properly handle cancellation and timeouts

## Testing

- Write unit tests for all functions and methods
- Use pytest fixtures for test setup
- Use parametrized tests for testing multiple cases
- Mock external dependencies
- Aim for high test coverage

## Agent Implementation

- Follow the agent interface contracts
- Implement required methods with proper error handling
- Document agent capabilities and limitations
- Use dependency injection for services and tools 
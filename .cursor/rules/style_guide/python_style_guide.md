# Python Style Guide for AgenticFleet

This style guide outlines the coding conventions for the AgenticFleet codebase. Following these guidelines ensures consistency across the project and improves code quality and maintainability.

## 1. Formatting

### 1.1 Indentation and Line Length

- Use 4 spaces for indentation (no tabs)
- Limit lines to 100 characters
- Wrap lines that exceed 100 characters

```python
# Good
def very_long_function_name(
    long_argument_name1, 
    long_argument_name2,
    long_argument_name3
):
    return some_value

# Bad - exceeds line limit
def very_long_function_name(long_argument_name1, long_argument_name2, long_argument_name3, long_argument_name4):
    return some_value
```

### 1.2 Blank Lines

- Use 2 blank lines before top-level class and function definitions
- Use 1 blank line before class method definitions
- Use blank lines to separate logical sections within functions

```python
def function1():
    """Function 1 docstring."""
    pass


def function2():
    """Function 2 docstring."""
    pass


class MyClass:
    """Class docstring."""
    
    def method1(self):
        """Method 1 docstring."""
        pass
    
    def method2(self):
        """Method 2 docstring."""
        pass
```

### 1.3 Whitespace

- No trailing whitespace
- Surround operators with a single space on either side
- No space between function name and parenthesis
- One space after commas in lists, dicts, and argument lists

```python
# Good
x = 1 + 2
y = x * 3
result = function(a, b, key="value")

# Bad
x=1+2
y = x*3
result = function ( a,b,key = "value" )
```

## 2. Imports

### 2.1 Import Order

Follow this order for imports:

1. Standard library imports
2. Related third-party imports
3. Local application/library-specific imports

Separate each group with a blank line.

```python
# Standard library
import os
import sys
from typing import Dict, List, Optional

# Third-party
import numpy as np
import chainlit as cl
from fastapi import FastAPI, Depends

# Local
from agentic_fleet.agents import BaseAgent
from agentic_fleet.utils.logging import get_logger
```

### 2.2 Import Style

- Use absolute imports rather than relative imports
- Do not use wildcard imports (`from module import *`)
- Avoid redundant aliases

```python
# Good
from agentic_fleet.core.agents import BaseAgent

# Acceptable when necessary
from agentic_fleet.core.agents import BaseAgent as CoreBaseAgent

# Bad - relative import
from ..core.agents import BaseAgent

# Bad - wildcard import
from agentic_fleet.core.agents import *
```

## 3. Naming Conventions

### 3.1 General Naming

- Use descriptive, meaningful names
- Avoid single-letter variables (except in very short loops)
- Avoid abbreviations unless widely understood

### 3.2 Specific Naming Styles

- `snake_case` for variables, functions, methods, and modules
- `PascalCase` for classes and exceptions
- `UPPER_CASE` for constants

```python
# Variables, functions, methods
agent_name = "assistant"
def process_message(message, context):
    pass

# Classes
class MessageProcessor:
    pass

# Constants
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 60
```

### 3.3 Naming Special Methods

- Prefix private methods and variables with a single underscore: `_private_method`
- Prefix "internal use" attributes with a double underscore: `__internal_attr`
- Avoid trailing underscores unless necessary to avoid conflicts

## 4. Code Structure

### 4.1 Function and Method Structure

- Keep functions focused on a single responsibility
- Aim for functions under 50 lines
- Limit the number of parameters (aim for 5 or fewer)
- Use keyword arguments for greater than 3 parameters

```python
# Good - clear, focused function with named arguments
def process_agent_message(
    message: str,
    agent_id: str,
    timeout: int = 30,
    save_history: bool = True
) -> dict:
    """Process a message with the specified agent."""
    # Implementation
```

### 4.2 Class Structure

Organize classes in this order:

1. Class docstring
2. Class attributes and constants
3. `__init__` method
4. Special methods (`__str__`, `__repr__`, etc.)
5. Properties
6. Class methods
7. Static methods
8. Regular methods
9. Private and internal methods

## 5. Documentation

### 5.1 Docstrings

Use Google-style docstrings for all public modules, functions, classes, and methods:

```python
def function_with_types_in_docstring(param1, param2):
    """Example function with types documented in the docstring.
    
    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.
    
    Returns:
        bool: The return value. True for success, False otherwise.
        
    Raises:
        ValueError: If param1 is not a positive number.
    """
    if param1 <= 0:
        raise ValueError("param1 must be positive")
    return True
```

### 5.2 Comments

- Use comments sparingly - focus on WHY, not WHAT
- Keep comments updated when code changes
- Delete commented-out code

## 6. Type Hints

- Use type hints for function parameters and return values
- Use `typing` module for complex types
- Use `Optional[]` for parameters that could be None

```python
from typing import Dict, List, Optional, Union

def process_data(data: List[Dict[str, any]]) -> Dict[str, Union[str, int]]:
    """Process the input data and return results."""
    result: Dict[str, Union[str, int]] = {}
    # Implementation
    return result

def get_agent(agent_id: str, config: Optional[Dict[str, any]] = None) -> Optional["Agent"]:
    """Get an agent by ID if it exists."""
    # Implementation
```

## 7. Error Handling

- Use specific exception types rather than bare `except:`
- Use context managers for resource cleanup
- Follow the [error handling patterns](/.cursor/rules/best_practices/error_handling.md)

```python
try:
    result = self.process_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise InvalidInputError(f"Invalid input: {e}") from e
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise ServiceUnavailableError("Service unavailable") from e
```

## 8. Async Patterns

- Use `async`/`await` consistently
- Don't mix sync and async code in the same context
- Follow the [async best practices](/.cursor/rules/best_practices/async_patterns.md)

```python
async def process_message(self, message: str) -> Response:
    """Process a message asynchronously."""
    try:
        result = await self.ai_service.generate_response(message)
        return Response(content=result)
    except asyncio.TimeoutError:
        logger.warning("Response generation timed out")
        return Response(content="Processing timed out", error=True)
```

## 9. Testing

- Write unit tests for all public functions and methods
- Use pytest as the testing framework
- Follow the [testing guidelines](/.cursor/rules/best_practices/testing_patterns.md)

## 10. Code Quality Tools

The codebase uses these automated tools for quality control:

- **Black**: Code formatter
- **Flake8**: Linter
- **Pylint**: Static analysis
- **mypy**: Type checking

Configure your editor to run these tools on save or use pre-commit hooks. 
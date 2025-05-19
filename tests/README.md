# Agentic Fleet Testing

This directory contains tests for the Agentic Fleet project. The tests are organized into unit tests and integration tests.

## Test Structure

- `conftest.py`: Contains pytest fixtures shared across multiple test files
- `pytest.ini`: Configuration for pytest
- `test_*.py`: Unit test files for specific modules
- `integration/`: Integration tests
- `unit/`: Directory for additional unit tests

## Running Tests

You can run the tests using the `run_tests.py` script in the project root:

```bash
# Run all tests
./run_tests.py

# Run a specific test file
./run_tests.py tests/test_app.py

# Run tests with specific options
./run_tests.py -v --no-header
```

## Test Fixtures

Common fixtures defined in `conftest.py`:

- `mock_user_session`: Mocks Chainlit's user session with custom get/set behavior
- `mock_chainlit_elements`: Mocks Chainlit UI elements such as Text, Message, and TaskList
- `mock_settings_components`: Mocks Chainlit settings components like ChatSettings, Select, Slider, etc.
- `mock_openai_client`: Mocks the Azure OpenAI client with specific model information
- `mock_env_vars`: Mocks environment variables necessary for testing

## Writing Tests

### Unit Tests

Unit tests should be written for individual components and should mock dependencies. For example:

```python
@pytest.mark.asyncio
async def test_handle_chat_message(mock_user_session, mock_chainlit_elements):
    # Test code here
```

### Integration Tests

Integration tests verify that multiple components work together correctly. These tests use fewer mocks and test broader functionality.

## Testing Chainlit Components

Since Chainlit components use async methods, make sure to use `AsyncMock` when mocking these methods:

```python
mock_message = mock_chainlit_elements["Message"].return_value
await function_that_uses_message(mock_message)
assert mock_message.send.called
```

## Test Coverage

You can run tests with coverage reporting:

```bash
pip install pytest-cov
./run_tests.py --cov=agentic_fleet --cov-report=html
```

This will generate a coverage report in the `htmlcov` directory.

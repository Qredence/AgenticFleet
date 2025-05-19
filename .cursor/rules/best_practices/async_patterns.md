# Asynchronous Programming Best Practices

This document outlines the best practices for asynchronous programming in the AgenticFleet codebase. Following these guidelines will help ensure efficient, reliable, and maintainable async code.

## 1. Core Async Principles

### 1.1 Async/Await Usage

- Use `async`/`await` for I/O-bound operations
- Mark functions that call async functions with `async`
- Always await async functions

```python
# Good
async def get_agent_response(message):
    """Get a response from an agent asynchronously."""
    agent = await agent_registry.get_agent(agent_id)
    return await agent.process_message(message)

# Bad - mixing sync and async
def get_agent_response(message):
    """Incorrect mixing of sync and async code."""
    agent = agent_registry.get_agent(agent_id)  # This should be awaited
    return agent.process_message(message)  # This should be awaited
```

### 1.2 Avoiding Sync Blocking

- Never use blocking I/O in async functions
- For CPU-bound tasks, use `asyncio.to_thread` or ProcessPoolExecutor
- Avoid `time.sleep()` in async code; use `asyncio.sleep()` instead

```python
# Good - using asyncio.sleep
async def delayed_operation(delay_seconds):
    """Perform an operation after a delay."""
    await asyncio.sleep(delay_seconds)
    return await perform_operation()

# Bad - blocking the event loop
async def delayed_operation_bad(delay_seconds):
    """Incorrectly blocks the event loop."""
    time.sleep(delay_seconds)  # Blocks the entire event loop!
    return await perform_operation()
```

### 1.3 Running CPU-Bound Tasks

Use `asyncio.to_thread` for CPU-bound operations:

```python
async def process_large_data(data):
    """Process data in a separate thread to avoid blocking."""
    # This would block if not run in a thread
    result = await asyncio.to_thread(cpu_intensive_calculation, data)
    return result
```

## 2. Task Management

### 2.1 Creating and Awaiting Tasks

Use `asyncio.create_task()` for concurrent operations:

```python
async def process_multiple_agents(message, agent_ids):
    """Process a message with multiple agents concurrently."""
    tasks = [
        asyncio.create_task(process_agent(message, agent_id))
        for agent_id in agent_ids
    ]
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)
    return results
```

### 2.2 Task Cancellation

Always support cancellation in long-running tasks:

```python
async def process_with_timeout(operation, timeout=30):
    """Run an operation with timeout and cancellation support."""
    try:
        return await asyncio.wait_for(operation, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout} seconds")
        raise AgentTimeoutError(f"Operation timed out after {timeout} seconds")
```

### 2.3 Proper Task Cleanup

Ensure tasks are properly cleaned up:

```python
async def run_background_tasks():
    """Run background tasks and ensure they're cleaned up."""
    tasks = []
    try:
        # Create background tasks
        tasks = [
            asyncio.create_task(background_job1()),
            asyncio.create_task(background_job2()),
            asyncio.create_task(background_job3())
        ]
        
        # Do other work while tasks run in background
        await main_job()
        
    finally:
        # Cancel any remaining tasks when we're done
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete or be cancelled
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
```

## 3. Concurrency Control

### 3.1 Limiting Concurrency

Use semaphores to limit concurrency:

```python
class RateLimitedClient:
    """Client with concurrency limiting."""
    
    def __init__(self, max_concurrent=10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def call_api(self, endpoint, data):
        """Call API with concurrency limiting."""
        async with self.semaphore:
            return await self._make_api_call(endpoint, data)
    
    async def _make_api_call(self, endpoint, data):
        """Internal method to make the actual API call."""
        # API call implementation
```

### 3.2 Task Groups

Use task groups for related concurrent operations in Python 3.11+:

```python
async def process_data_streams(streams):
    """Process multiple data streams concurrently."""
    async with asyncio.TaskGroup() as group:
        tasks = [
            group.create_task(process_stream(stream))
            for stream in streams
        ]
    
    # All tasks are complete or cancelled here
    return [task.result() for task in tasks]
```

## 4. Error Handling in Async Code

### 4.1 Exception Propagation

Handle exceptions appropriately in async code:

```python
async def process_with_error_handling():
    """Process with proper async error handling."""
    try:
        # Create concurrent tasks
        results = await asyncio.gather(
            task1(),
            task2(),
            task3(),
            return_exceptions=True  # Prevent exceptions from cancelling other tasks
        )
        
        # Handle any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {str(result)}")
                # Handle the error case
            else:
                # Process successful result
    except Exception as e:
        # Handle any other exceptions
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
```

### 4.2 Task Exception Handling

Check for exceptions in completed tasks:

```python
async def monitor_background_task(task):
    """Monitor a background task for exceptions."""
    try:
        # Wait for the task to complete
        await task
    except asyncio.CancelledError:
        logger.info("Task was cancelled")
    except Exception as e:
        logger.error(f"Task failed with error: {str(e)}", exc_info=True)
        # Handle or propagate the exception
```

## 5. Context Variables and State

### 5.1 Using contextvars

Use `contextvars` for context-local state in async code:

```python
# Define a context variable
current_user = contextvars.ContextVar('current_user', default=None)

async def process_request(user_id, message):
    """Process a request in the context of a user."""
    # Set the user context for this request
    token = current_user.set({'id': user_id})
    try:
        # All functions called from here can access current_user
        return await handle_message(message)
    finally:
        # Reset the context when done
        current_user.reset(token)

async def handle_message(message):
    """Handle a message in the current user context."""
    user = current_user.get()
    logger.info(f"Processing message for user {user['id']}")
    # Implementation
```

## 6. Testing Async Code

### 6.1 Writing Async Tests

Use pytest's async support:

```python
import pytest

@pytest.mark.asyncio
async def test_agent_processing():
    """Test that an agent processes messages correctly."""
    # Setup
    agent = TestAgent()
    
    # Execute
    response = await agent.process_message("test message")
    
    # Assert
    assert response.content == "expected result"
    assert not response.error
```

### 6.2 Mocking Async Functions

Mock async functions in tests:

```python
@pytest.mark.asyncio
async def test_with_async_mock():
    """Test using an async mock."""
    # Create an async mock
    mock_agent = AsyncMock()
    mock_agent.process_message.return_value = Response(content="mocked response")
    
    # Test with the mock
    processor = MessageProcessor(agent=mock_agent)
    result = await processor.process("test message")
    
    # Verify
    mock_agent.process_message.assert_called_once_with("test message")
    assert result.content == "mocked response"
```

## 7. Performance Considerations

### 7.1 Batching

Batch operations for better performance:

```python
async def get_multiple_items(item_ids):
    """Get multiple items efficiently through batching."""
    # Process in reasonably sized batches
    batch_size = 50
    results = []
    
    for i in range(0, len(item_ids), batch_size):
        batch = item_ids[i:i+batch_size]
        # Make a single batched request
        batch_results = await database.fetch_many(
            "SELECT * FROM items WHERE id = ANY($1)",
            [batch]
        )
        results.extend(batch_results)
    
    return results
```

### 7.2 Connection Pooling

Use connection pools for database and HTTP connections:

```python
# Database connection pool
db_pool = None

async def get_db_pool():
    """Get or create the database connection pool."""
    global db_pool
    if db_pool is None:
        db_pool = await create_pool(
            dsn=config.DATABASE_URL,
            min_size=5,
            max_size=20
        )
    return db_pool

async def execute_query(query, params):
    """Execute a query using the connection pool."""
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        return await connection.fetchall(query, *params)
```

## 8. Structuring Async Applications

### 8.1 Service Pattern

Structure async code using the service pattern:

```python
class AgentService:
    """Service for interacting with agents."""
    
    def __init__(self, agent_registry, message_processor):
        self.agent_registry = agent_registry
        self.message_processor = message_processor
    
    async def process_agent_message(self, agent_id, message, timeout=30):
        """Process a message with a specific agent."""
        try:
            agent = await self.agent_registry.get_agent(agent_id)
            
            # Use timeout for the operation
            response = await asyncio.wait_for(
                agent.process_message(message),
                timeout=timeout
            )
            
            return await self.message_processor.format_response(response)
        except asyncio.TimeoutError:
            logger.warning(f"Agent {agent_id} processing timed out")
            raise AgentTimeoutError(f"Processing timed out after {timeout}s")
        except AgentNotFoundError:
            logger.error(f"Agent {agent_id} not found")
            raise
```

### 8.2 Event-Driven Architecture

Implement event-driven patterns for async systems:

```python
class EventBus:
    """Simple async event bus."""
    
    def __init__(self):
        self.subscribers = defaultdict(list)
    
    def subscribe(self, event_type, handler):
        """Subscribe to an event type."""
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event_type, data):
        """Publish an event to all subscribers."""
        subscribers = self.subscribers.get(event_type, [])
        tasks = [asyncio.create_task(handler(data)) for handler in subscribers]
        
        if tasks:
            # Wait for all handlers to process the event
            await asyncio.gather(*tasks, return_exceptions=True)
```

## Conclusion

Following these async programming best practices will result in more efficient, maintainable, and reliable code. Key takeaways:

1. Be consistent with async/await usage
2. Never block the event loop
3. Handle cancellation and cleanup properly
4. Manage concurrency appropriately
5. Handle errors consistently in async contexts
6. Structure applications with async patterns in mind

Always apply these patterns throughout the AgenticFleet codebase to ensure optimal performance and reliability. 
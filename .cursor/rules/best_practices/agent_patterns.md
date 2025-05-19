# Agent Design Patterns for AgenticFleet

This document outlines the recommended design patterns for implementing agents in the AgenticFleet system. Following these patterns will ensure consistency, maintainability, and extensibility of the agent ecosystem.

## Core Agent Architecture

<mermaid>
graph TD
    BaseAgent["BaseAgent<br>Abstract Class"] --> AgentInterface["Agent Interface<br>Definition"]
    AgentInterface --> MessageHandling["Message<br>Processing"]
    AgentInterface --> StateManagement["State<br>Management"]
    AgentInterface --> ToolIntegration["Tool<br>Integration"]
    AgentInterface --> ErrorHandling["Error<br>Handling"]
    
    BaseAgent --> SpecializedAgent1["Specialized Agent<br>Implementation"]
    BaseAgent --> SpecializedAgent2["Specialized Agent<br>Implementation"]
    
    style BaseAgent fill:#4da6ff,stroke:#0066cc,color:white
    style AgentInterface fill:#4dbb5f,stroke:#36873f,color:white
    style MessageHandling fill:#ffa64d,stroke:#cc7a30,color:white
    style StateManagement fill:#ff5555,stroke:#cc0000,color:white
    style ToolIntegration fill:#d971ff,stroke:#a33bc2,color:white
    style ErrorHandling fill:#4dbbbb,stroke:#368787,color:white
</mermaid>

## Agent Interface Definition

All agents should implement a consistent interface:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from agentic_fleet.models import Response
from agentic_fleet.utils.cancellation import CancellationToken

class BaseAgent(ABC):
    """Base class for all agents in the AgenticFleet system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the agent with optional configuration."""
        self.config = config or {}
        self.name = self.__class__.__name__
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize agent resources and state."""
        pass
    
    @abstractmethod
    async def process_message(
        self, message: str, token: Optional[CancellationToken] = None
    ) -> Response:
        """
        Process an incoming message and generate a response.
        
        Args:
            message: The message content to process
            token: Optional cancellation token to cancel processing
            
        Returns:
            Response: The agent's response to the message
        """
        pass
    
    async def on_reset(self) -> None:
        """Reset the agent's state."""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Get the list of capabilities this agent supports."""
        return []
    
    async def shutdown(self) -> None:
        """Clean up resources when shutting down the agent."""
        pass
```

## Agent Implementation Patterns

### Factory Pattern for Agent Creation

Use a factory pattern to create agent instances based on configurations:

```python
class AgentFactory:
    """Factory for creating agent instances."""
    
    _registry: Dict[str, Type[BaseAgent]] = {}
    
    @classmethod
    def register(cls, agent_type: str, agent_class: Type[BaseAgent]) -> None:
        """Register an agent class for a specific type."""
        cls._registry[agent_type] = agent_class
    
    @classmethod
    def create(cls, agent_type: str, config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """Create an agent instance of the specified type."""
        if agent_type not in cls._registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = cls._registry[agent_type]
        return agent_class(config)
```

### Strategy Pattern for Agent Behavior

Implement different agent behaviors using the strategy pattern:

```python
class MessageProcessor:
    """Strategy interface for message processing."""
    
    @abstractmethod
    async def process(self, message: str) -> str:
        """Process a message according to the strategy."""
        pass

class SimpleMessageProcessor(MessageProcessor):
    """Simple message processing strategy."""
    
    async def process(self, message: str) -> str:
        # Simple processing logic
        return f"Processed: {message}"

class LLMMessageProcessor(MessageProcessor):
    """LLM-based message processing strategy."""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
    
    async def process(self, message: str) -> str:
        # Use LLM for processing
        return await self.llm_service.generate_response(message)
```

### State Management Pattern

Use a clean state management pattern for agents that need to maintain state:

```python
class AgentState:
    """Container for agent state."""
    
    def __init__(self):
        self.conversation_history = []
        self.context = {}
        self.memory = {}
        self.last_update = datetime.now()
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_update = datetime.now()
    
    def update_context(self, key: str, value: Any) -> None:
        """Update a context value."""
        self.context[key] = value
        self.last_update = datetime.now()
    
    def reset(self) -> None:
        """Reset the state."""
        self.conversation_history = []
        self.context = {}
        self.last_update = datetime.now()
```

### Middleware Pattern for Message Processing

Use middleware for cross-cutting concerns in message processing:

```python
class Middleware:
    """Base class for agent middleware."""
    
    async def process(self, message: str, next_middleware: Callable) -> str:
        """Process the message and call the next middleware."""
        return await next_middleware(message)

class LoggingMiddleware(Middleware):
    """Middleware that logs messages."""
    
    async def process(self, message: str, next_middleware: Callable) -> str:
        logger.info(f"Processing message: {message[:50]}...")
        result = await next_middleware(message)
        logger.info(f"Processed message. Response: {result[:50]}...")
        return result

class AuthenticationMiddleware(Middleware):
    """Middleware that checks authentication."""
    
    async def process(self, message: str, next_middleware: Callable) -> str:
        # Check authentication logic here
        if not is_authenticated(message):
            return "Authentication required"
        return await next_middleware(message)
```

## Agent Lifecycle Management

### Initialization

Properly initialize agent resources:

```python
class CodeGenerationAgent(BaseAgent):
    """Agent for generating code."""
    
    def initialize(self) -> None:
        """Initialize the code generation agent."""
        # Load necessary models and resources
        self.code_model = self._load_code_model()
        self.language_specs = self._load_language_specs()
        self.templates = self._load_templates()
    
    def _load_code_model(self):
        # Implementation for loading the code model
        pass
    
    def _load_language_specs(self):
        # Implementation for loading language specifications
        pass
    
    def _load_templates(self):
        # Implementation for loading code templates
        pass
```

### Graceful Shutdown

Ensure agents can clean up resources:

```python
class DatabaseAgent(BaseAgent):
    """Agent for database operations."""
    
    def initialize(self) -> None:
        """Initialize database connections."""
        self.connection_pool = create_connection_pool(
            self.config.get("db_url", "sqlite:///default.db"),
            min_connections=2,
            max_connections=10
        )
    
    async def shutdown(self) -> None:
        """Close database connections."""
        if hasattr(self, "connection_pool"):
            await self.connection_pool.close()
            logger.info("Database connection pool closed")
```

## Agent Composition Patterns

### Decorator Pattern for Enhancing Agents

Use decorators to add capabilities to agents:

```python
class AgentDecorator(BaseAgent):
    """Base decorator for enhancing agents."""
    
    def __init__(self, agent: BaseAgent, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.agent = agent
    
    async def process_message(
        self, message: str, token: Optional[CancellationToken] = None
    ) -> Response:
        # Default implementation delegates to the wrapped agent
        return await self.agent.process_message(message, token)
    
    async def on_reset(self) -> None:
        await self.agent.on_reset()
    
    def get_capabilities(self) -> List[str]:
        return self.agent.get_capabilities()
    
    async def shutdown(self) -> None:
        await self.agent.shutdown()

class CachingAgentDecorator(AgentDecorator):
    """Decorator that adds caching to an agent."""
    
    def __init__(self, agent: BaseAgent, config: Optional[Dict[str, Any]] = None):
        super().__init__(agent, config)
        self.cache = {}
        self.ttl = self.config.get("cache_ttl", 300)  # 5 minutes default
    
    async def process_message(
        self, message: str, token: Optional[CancellationToken] = None
    ) -> Response:
        # Check cache first
        cache_key = hash(message)
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() < entry["expires"]:
                return entry["response"]
        
        # Not in cache, delegate to wrapped agent
        response = await self.agent.process_message(message, token)
        
        # Cache the response
        self.cache[cache_key] = {
            "response": response,
            "expires": time.time() + self.ttl
        }
        
        return response
```

### Chain of Responsibility for Agent Pipeline

Use chain of responsibility for creating agent pipelines:

```python
class AgentChain:
    """Chain of agents that process messages in sequence."""
    
    def __init__(self, agents: List[BaseAgent]):
        self.agents = agents
    
    async def process(
        self, message: str, token: Optional[CancellationToken] = None
    ) -> Response:
        """Process a message through the chain of agents."""
        current_message = message
        final_response = None
        
        for agent in self.agents:
            if token and token.cancelled:
                return Response(content="Processing cancelled", cancelled=True)
                
            response = await agent.process_message(current_message, token)
            
            if response.error:
                return response  # Stop chain on error
                
            current_message = response.content
            final_response = response
        
        return final_response
```

## Tool Integration Pattern

Standardize how agents use tools:

```python
class Tool:
    """Base class for tools that agents can use."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with the provided arguments."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the schema for this tool's parameters."""
        return {}

class ToolEnabledAgent(BaseAgent):
    """Base class for agents that can use tools."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool for the agent to use."""
        self.tools[tool.name] = tool
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a registered tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        return await tool.execute(**kwargs)
    
    def get_tool_schemas(self) -> Dict[str, Any]:
        """Get schemas for all registered tools."""
        return {name: tool.get_schema() for name, tool in self.tools.items()}
```

## Error Handling Pattern

Implement consistent error handling in agents:

```python
from agentic_fleet.utils.error_handling import AgentError, safe_execute

class RobustAgent(BaseAgent):
    """Agent with robust error handling."""
    
    async def process_message(
        self, message: str, token: Optional[CancellationToken] = None
    ) -> Response:
        try:
            # Validate input
            if not message or not isinstance(message, str):
                raise ValueError("Invalid message format")
            
            # Check for cancellation
            if token and token.cancelled:
                return Response(content="Processing cancelled", cancelled=True)
            
            # Process message with safe execution
            result = await safe_execute(
                self._process_message_internal,
                message,
                error_prefix="Error in agent processing",
                log_exception=True
            )
            
            return result
            
        except AgentError as e:
            logger.error(f"Agent error: {str(e)}")
            return Response(content=f"Agent error: {str(e)}", error=True)
            
        except Exception as e:
            logger.error(f"Unexpected error in agent: {str(e)}", exc_info=True)
            return Response(
                content="An unexpected error occurred during processing",
                error=True
            )
    
    async def _process_message_internal(self, message: str) -> str:
        """Internal message processing logic."""
        # Implementation of message processing
        pass
```

## Async Pattern for Agents

Ensure proper async implementation:

```python
class AsyncAgent(BaseAgent):
    """Agent with proper async implementation."""
    
    async def process_message(
        self, message: str, token: Optional[CancellationToken] = None
    ) -> Response:
        # Create tasks for concurrent operations
        tasks = [
            asyncio.create_task(self._analyze_message(message)),
            asyncio.create_task(self._retrieve_context(message))
        ]
        
        try:
            # Wait for all tasks with cancellation support
            results = await asyncio.gather(*tasks)
            analysis, context = results
            
            # Use results to generate response
            return await self._generate_response(message, analysis, context)
            
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to finish cancellation
            await asyncio.gather(*tasks, return_exceptions=True)
            return Response(content="Operation cancelled", cancelled=True)
    
    async def _analyze_message(self, message: str) -> Dict[str, Any]:
        """Analyze the incoming message."""
        # Implementation
        pass
    
    async def _retrieve_context(self, message: str) -> Dict[str, Any]:
        """Retrieve relevant context for the message."""
        # Implementation
        pass
    
    async def _generate_response(
        self, message: str, analysis: Dict[str, Any], context: Dict[str, Any]
    ) -> Response:
        """Generate a response using message analysis and context."""
        # Implementation
        pass
```

## Agent Testing Patterns

### Mock-Based Testing

Use mocks to test agents independently:

```python
@pytest.mark.asyncio
async def test_code_generation_agent():
    # Setup mock LLM service
    mock_llm = AsyncMock()
    mock_llm.generate_code.return_value = "def hello_world():\n    print('Hello, World!')"
    
    # Create agent with mock
    agent = CodeGenerationAgent({"llm_service": mock_llm})
    
    # Test message processing
    response = await agent.process_message("Generate a hello world function in Python")
    
    # Assertions
    assert not response.error
    assert "def hello_world" in response.content
    mock_llm.generate_code.assert_called_once()
```

### Component Testing

Test agent components individually:

```python
@pytest.mark.asyncio
async def test_message_processor():
    # Create processor
    processor = SimpleMessageProcessor()
    
    # Test processing
    result = await processor.process("Test message")
    
    # Assertions
    assert result == "Processed: Test message"
```

### Integration Testing

Test agents with their dependencies:

```python
@pytest.mark.asyncio
async def test_agent_with_tools():
    # Setup real tools
    calculator_tool = CalculatorTool("calculator", "Performs calculations")
    
    # Create agent with tool
    agent = ToolEnabledAgent()
    agent.register_tool(calculator_tool)
    
    # Test tool execution through agent
    response = await agent.process_message("Calculate 2+2")
    
    # Assertions
    assert not response.error
    assert "4" in response.content
```

## Best Practices Summary

1. **Follow Interface Contracts**: Always implement the BaseAgent interface consistently
2. **Use Composition Over Inheritance**: Prefer composition for reusing agent functionality
3. **Handle State Carefully**: Explicitly manage agent state for predictability
4. **Use Asynchronous Patterns**: Implement proper async patterns for all agent operations
5. **Implement Robust Error Handling**: Use structured error handling with specific exceptions
6. **Support Cancellation**: Ensure all long-running operations can be cancelled
7. **Design for Testability**: Structure agents to be easily testable
8. **Document Capabilities**: Clearly document what each agent can do
9. **Use Middleware for Cross-Cutting Concerns**: Logging, authentication, etc.
10. **Implement Clean Shutdown**: Ensure agents release resources properly

## Conclusion

Following these agent design patterns will ensure that the AgenticFleet system remains maintainable, extensible, and robust. These patterns provide a foundation for building agents that work consistently within the system while allowing for specialized behaviors and capabilities. 
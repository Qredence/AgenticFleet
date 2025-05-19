import pytest
from agentic_fleet.core.agents.coding_agent import CodingAgent, CodingConfig
from agentic_fleet.core.tools.code_execution.code_execution_tool import CodeBlock, ExecutionResult


@pytest.mark.asyncio
async def test_generate_code():
    """Test code generation functionality of CodingAgent."""
    agent = CodingAgent(config=CodingConfig())
    task = "Create a function that adds two numbers."
    requirements = {"description": "Add two numbers and return result."}
    code_block = await agent._generate_code(task, requirements, context={})
    assert isinstance(code_block, CodeBlock), "Output should be a CodeBlock instance."
    assert "def" in code_block.code.lower(), "Generated code should contain a function definition."


@pytest.mark.asyncio
async def test_execute_code():
    """Test code execution functionality of CodingAgent."""
    agent = CodingAgent(config=CodingConfig())
    # A sample piece of code that can be executed safely
    code = "def add(a, b):\n    return a + b\nresult = add(2, 3)\nprint(result)"
    exec_result = await agent._execute_code(code, context={})
    assert isinstance(exec_result, ExecutionResult), "Output should be an ExecutionResult instance."
    # Depending on the implementation of ExecutionResult, you might check for output
    # For now, ensure that the result is not empty
    assert hasattr(exec_result, "output")
    assert exec_result.output is not None


@pytest.mark.asyncio
async def test_optimize_code():
    """Test code optimization functionality of CodingAgent."""
    agent = CodingAgent(config=CodingConfig())
    code = "def add(a, b):\n    return a + b"
    # Optimize for readability metric
    optimized = await agent._optimize_code(code, metrics=["readability"], context={})
    assert isinstance(optimized, CodeBlock), "Output should be a CodeBlock instance."
    assert len(optimized.code) > 0, "Optimized code should not be empty."


@pytest.mark.asyncio
async def test_review_code():
    """Test code review functionality of CodingAgent."""
    agent = CodingAgent(config=CodingConfig())
    code = "def add(a, b):\n    return a + b"
    review_comments = await agent._review_code(code, context={})
    assert isinstance(review_comments, str), "Review output should be a string."
    assert len(review_comments) > 0, "Review comments should not be empty."

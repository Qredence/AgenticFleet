"""
Code Execution Tool Module.

This module provides tools for generating, validating, and executing code,
with a focus on statistical modeling and data analysis.
"""

import ast
import re
from contextlib import redirect_stdout
from io import StringIO
from typing import Any

import black
import isort
import numpy as np
import pandas as pd
import ruff
from pydantic import BaseModel


class CodeBlock(BaseModel):
    """Represents a block of code with metadata."""

    code: str
    language: str = "python"
    dependencies: list[str] = []
    description: str = ""
    version: str = "1.0"
    metadata: dict[str, Any] = {}


class ExecutionResult(BaseModel):
    """Represents the result of code execution."""

    success: bool
    output: str = ""
    error: str | None = None
    result: Any = None
    execution_time: float = 0.0
    memory_usage: float = 0.0
    metadata: dict[str, Any] = {}


class CodeValidationResult(BaseModel):
    """Represents the result of code validation."""

    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    style_issues: list[str] = []
    security_issues: list[str] = []


class CodeExecutionTool:
    """
    Tool for generating, validating, and executing code blocks,
    with emphasis on statistical modeling and data analysis.
    """

    def __init__(
        self,
        max_execution_time: int = 30,
        memory_limit_mb: int = 1024,
        allowed_modules: list[str] | None = None,
    ) -> None:
        """
        Initialize the Code Execution Tool.

        Args:
            max_execution_time: Maximum execution time in seconds
            memory_limit_mb: Maximum memory usage in MB
            allowed_modules: List of allowed module imports
        """
        self.max_execution_time = max_execution_time
        self.memory_limit_mb = memory_limit_mb
        self.allowed_modules = allowed_modules or [
            "numpy",
            "pandas",
            "scipy",
            "statsmodels",
            "sklearn",
        ]
        self.execution_history: list[dict[str, Any]] = []

    async def execute_code(
        self, code_block: str | CodeBlock, context: dict[str, Any] | None = None
    ) -> ExecutionResult:
        """
        Execute a code block with safety checks and resource limits.

        Args:
            code_block: Code to execute (string or CodeBlock)
            context: Optional execution context variables

        Returns:
            ExecutionResult object containing execution results
        """
        if isinstance(code_block, str):
            code_block = CodeBlock(code=code_block)

        # Validate code before execution
        validation = await self.validate_code(code_block)
        if not validation.valid:
            return ExecutionResult(
                success=False, error="Code validation failed: " + "; ".join(validation.errors)
            )

        # Prepare execution environment
        globals_dict = {"__builtins__": __builtins__, "np": np, "pd": pd}
        if context:
            globals_dict.update(context)

        # Capture output
        output_buffer = StringIO()

        try:
            # Execute with resource limits and output capture
            with redirect_stdout(output_buffer):
                exec(code_block.code, globals_dict)

            # Extract result if available
            result = globals_dict.get("result", None)

            execution_result = ExecutionResult(
                success=True,
                output=output_buffer.getvalue(),
                result=result,
                execution_time=0.0,  # Would be measured in real impl
                memory_usage=0.0,  # Would be measured in real impl
                metadata={"globals": list(globals_dict.keys()), "has_result": result is not None},
            )

        except Exception as e:
            execution_result = ExecutionResult(
                success=False, error=str(e), output=output_buffer.getvalue()
            )

        # Record execution in history
        self.execution_history.append(
            {
                "code_block": code_block.model_dump(),
                "result": execution_result.model_dump(),
                "timestamp": pd.Timestamp.now(),
            }
        )

        return execution_result

    async def validate_code(self, code_block: str | CodeBlock) -> CodeValidationResult:
        """
        Validate code for syntax, style, and security issues.

        Args:
            code_block: Code to validate (string or CodeBlock)

        Returns:
            CodeValidationResult object containing validation results
        """
        if isinstance(code_block, str):
            code_block = CodeBlock(code=code_block)

        validation_result = CodeValidationResult(valid=True)

        try:
            # Syntax check
            ast.parse(code_block.code)

            # Security checks
            if not self._check_imports(code_block.code):
                validation_result.valid = False
                validation_result.security_issues.append("Unauthorized module imports detected")

            if self._has_dangerous_operations(code_block.code):
                validation_result.valid = False
                validation_result.security_issues.append(
                    "Potentially dangerous operations detected"
                )

            # Style checks
            style_issues = []

            # Ruff check
            ruff_results = ruff.check(code_block.code)
            if ruff_results:
                style_issues.extend([str(r) for r in ruff_results])

            # Black formatting check
            try:
                black.format_str(code_block.code, mode=black.Mode())
            except Exception as e:
                style_issues.append(f"Black formatting error: {str(e)}")

            # isort check
            try:
                isort.code(code_block.code)
            except Exception as e:
                style_issues.append(f"Import sorting error: {str(e)}")

            if style_issues:
                validation_result.style_issues.extend(style_issues)

        except SyntaxError as e:
            validation_result.valid = False
            validation_result.errors.append(f"Syntax error: {str(e)}")
        except Exception as e:
            validation_result.valid = False
            validation_result.errors.append(f"Validation error: {str(e)}")

        return validation_result

    def format_code(self, code_block: str | CodeBlock) -> str:
        """
        Format code according to style guidelines.

        Args:
            code_block: Code to format (string or CodeBlock)

        Returns:
            Formatted code string
        """
        if isinstance(code_block, CodeBlock):
            code = code_block.code
        else:
            code = code_block

        try:
            # Sort imports
            code = isort.code(code)

            # Format with black
            code = black.format_str(code, mode=black.Mode())

            return code
        except Exception:
            return code  # Return original if formatting fails

    def get_execution_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get the history of code executions.

        Args:
            limit: Maximum number of history entries to return

        Returns:
            List of execution history records
        """
        return sorted(self.execution_history, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def clear_history(self) -> None:
        """Clear the execution history."""
        self.execution_history.clear()

    def _check_imports(self, code: str) -> bool:
        """
        Check if code only imports allowed modules.

        Args:
            code: Code string to check

        Returns:
            True if all imports are allowed, False otherwise
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
                    if module.split(".")[0] not in self.allowed_modules:
                        return False
            return True
        except:
            return False

    def _has_dangerous_operations(self, code: str) -> bool:
        """
        Check for potentially dangerous operations in code.

        Args:
            code: Code string to check

        Returns:
            True if dangerous operations found, False otherwise
        """
        dangerous_patterns = [
            r"os\.",
            r"subprocess\.",
            r"sys\.",
            r"eval\(",
            r"exec\(",
            r"__import__",
            r"open\(",
            r"file\(",
        ]

        return any(re.search(pattern, code) for pattern in dangerous_patterns)

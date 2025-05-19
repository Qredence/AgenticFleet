"""Message processing module for AgenticFleet.

This module provides functionality for processing and streaming messages in the chat interface.
"""

from typing import Any

from autogen_agentchat.messages import TextMessage

# Task status constants
TASK_STATUS_RUNNING = "running"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"

# Removed stream_text as direct message sending is being refactored out of this module.


async def process_response(
    response: TextMessage | list[Any] | dict[str, Any] | str,
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Process agent responses and return structured data for rendering and any plan update.

    Returns:
        A tuple containing:
        - Optional[Dict[str, Any]]: Structured data for rendering (e.g., {'type': 'text', 'content': '...', 'author': '...'}), or None.
        - Optional[str]: Extracted plan text, or None.
    """
    processed_data: dict[str, Any] | None = None
    plan_update: str | None = None

    try:
        if isinstance(response, TextMessage):
            content = response.content
            author = getattr(response, "source", "Agent")  # Get author if available

            # Basic content type detection (can be expanded)
            # --- Enhanced Content Type Detection ---
            # Check for custom article marker (e.g., "[ARTICLE START]")
            if content.strip().startswith("[ARTICLE START]"):
                article_data = content.strip()[len("[ARTICLE START]") :].strip()
                # Assume the rest of the content is the article data
                processed_data = {
                    "type": "custom",
                    "content": {"type": "article", "data": article_data},
                    "author": author,
                }
            # Check for custom rich code marker (e.g., "[RICH_CODE:python START]")
            elif content.strip().startswith("[RICH_CODE"):
                try:
                    header = content.strip().split("START]")[0]
                    lang = header.split(":")[1].strip() if ":" in header else "text"
                    code_data = content.strip().split("START]")[1].strip()
                    processed_data = {
                        "type": "custom",
                        "content": {"type": "rich_code", "language": lang, "data": code_data},
                        "author": author,
                    }
                except Exception:
                    # Fallback if marker parsing fails
                    processed_data = {"type": "text", "content": content, "author": author}
            # Check for standard code blocks
            elif content.strip().startswith("```") and content.strip().endswith("```"):
                lang_hint = content.strip().split("\n")[0][3:].strip()
                code_content = "\n".join(content.strip().split("\n")[1:-1])
                processed_data = {
                    "type": "code",
                    "content": code_content,
                    "language": lang_hint or None,
                    "author": author,
                }
            # Check for plan update
            elif "Here is the plan to follow as best as possible:" in content:
                plan_parts = content.split("Here is the plan to follow as best as possible:")
                # Send the introductory text part
                intro_text = plan_parts[0].strip()
                if intro_text:
                    processed_data = {"type": "text", "content": intro_text, "author": author}
                # Extract the plan part
                if len(plan_parts) > 1:
                    plan_update = plan_parts[1].strip()
                    # Optionally, could also return the plan text itself as a message part:
                    # processed_data = {'type': 'text', 'content': f"Plan:\n{plan_update}", 'author': author}
            # Default to text
            else:
                processed_data = {"type": "text", "content": content, "author": author}

        elif isinstance(response, dict):
            # Handle potential dict structures (e.g., from tool calls or specific formats)
            if "content" in response:
                content = response["content"]
                author = response.get("author", "Agent")
                # Add more sophisticated type detection based on dict structure if needed
                processed_data = {
                    "type": "text",
                    "content": str(content),
                    "author": author,
                }  # Default to text
            # Add checks for other dict structures representing images, etc.
            elif response.get("type") == "image":
                # Basic image handling assuming URL is provided
                processed_data = {
                    "type": "image",
                    "content": response.get("url"),
                    "author": response.get("author", "Agent"),
                }
            # Add more checks here if agents can return other structured dicts
            else:
                # Fallback for unknown dict structure
                processed_data = {"type": "text", "content": str(response), "author": "System"}

        elif isinstance(response, (list, tuple)):
            # Process first item in list/tuple for simplicity in streaming context
            # A more robust solution might aggregate or handle sequences differently
            if response:
                processed_data, plan_update = await process_response(response[0])

        elif isinstance(response, str):
            # Handle raw strings
            processed_data = {"type": "text", "content": response, "author": "Agent"}

        # else: # Handle other potential types if necessary
        #     processed_data = {'type': 'text', 'content': str(response), 'author': 'System'}

    except Exception as e:
        # Return error as structured data
        processed_data = {
            "type": "error",
            "content": f"⚠️ Error processing response chunk: {str(e)}",
            "author": "System",
        }

    return processed_data, plan_update

"""Message handler module for AgenticFleet Chainlit UI.

This module contains functions for handling chat messages and rendering content.
"""

# Standard library imports
import logging
import traceback
import uuid

# Third-party imports
import chainlit as cl

from agentic_fleet.core.agents.team_manager import TeamManager  # Assuming this is safe

# Local imports
from agentic_fleet.message_processing import process_response
from agentic_fleet.services.chat_service import ChatService
from agentic_fleet.ui.components.canvas_panel import (
    add_edge_to_canvas,
    add_node_to_canvas,
    initialize_canvas,
)
from agentic_fleet.ui.task_manager import extract_and_add_plan_tasks

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize chat service
chat_service = ChatService()


async def handle_chat_message(
    message: cl.Message, agent_team_manager: TeamManager | None = None
) -> None:
    """Process an incoming chat message and generate a response.

    Args:
        message: The incoming chat message
        agent_team_manager: Optional. If provided, uses the AgenticFleet TeamManager.
    """
    # Get render mode from session (set in chainlit_app.py based on profile)
    render_mode = cl.user_session.get("ui_render_mode", "tasklist")  # Default to tasklist mode
    is_tasklist_mode = render_mode == "tasklist"
    is_custom_mode = render_mode == "custom"
    is_canvas_mode = render_mode == "canvas"

    # Get session ID for chat history
    session_id = cl.user_session.get("session_id")
    if not session_id:
        # Fallback: generate a random session ID if not present (Chainlit user_session has no 'id' attribute)
        session_id = str(uuid.uuid4())
        cl.user_session.set("session_id", session_id)

    # Store user message in chat history
    try:
        from agentic_fleet.schemas.message import MessageCreate, MessageType

        user_message = MessageCreate(
            content=message.content,
            sender="User",
            receiver="Agent",
            message_type=MessageType.TEXT,
            session_id=session_id,
            metadata={},
        )
        await chat_service.process_message(user_message)
    except Exception as e:
        logger.warning(f"Error storing user message in chat history: {e}")

    # Create TaskList if in tasklist mode
    task_list = None
    if is_tasklist_mode:
        task_list = cl.TaskList()
        task_list.status = "Analyzing your query..."  # Set status after creation
        await task_list.send()

        # Store the task list in user session for later updates
        cl.user_session.set("current_task_list", task_list)

        # Initialize plan steps tracking
        cl.user_session.set("plan_steps", {})
        cl.user_session.set("plan_tasks", {})

    # Initialize canvas if in canvas mode
    if is_canvas_mode:
        # Initialize the canvas interface
        await initialize_canvas()

        # Send a welcome message
        await cl.Message(
            content="🖌️ Canvas mode activated. Your responses will be visualized in a canvas interface.",
            author="System",
        ).send()

    try:
        # Check for reset command without showing a message
        # Handle both string and list content types
        if isinstance(message.content, str) and message.content.strip().lower() == "/reset":
            await on_reset(cl.Action(name="reset_agents", payload={"action": "reset"}))
            if task_list:
                task_list.status = "✅ Agents reset successfully"
                await task_list.send()
            return

        if agent_team_manager:  # New path for AgenticFleet TeamManager
            logger.info(f"Using AgenticFleet TeamManager: {agent_team_manager.config.name}")
            await cl.Message(
                content=f"Processing with team: {agent_team_manager.config.name}..."
            ).send()
            try:
                # This is a non-streaming call
                result_content = await agent_team_manager.execute_task(message.content)

                # Ensure result_content is a string before sending
                if not isinstance(result_content, str):
                    result_content = str(result_content)  # Convert if it's a dict or other type

                await cl.Message(
                    content=result_content, author=agent_team_manager.config.name
                ).send()
                # Store agent response in chat history
                try:
                    from agentic_fleet.schemas.message import MessageCreate, MessageType

                    agent_response_message = MessageCreate(
                        content=result_content,
                        sender=agent_team_manager.config.name,
                        receiver="User",
                        message_type=MessageType.TEXT,
                        session_id=session_id,
                        metadata={},
                    )
                    await chat_service.process_message(agent_response_message)
                except Exception as e:
                    logger.warning(f"Error storing agent response in chat history: {e}")

            except Exception as e:
                error_msg = (
                    f"⚠️ Error during task execution with {agent_team_manager.config.name}: {str(e)}"
                )
                logger.error(f"Task execution error: {traceback.format_exc()}")
                await cl.ErrorMessage(content=error_msg).send()
            return  # End of new path

        # Fallback to legacy team (MagenticOne) if agent_team_manager not provided
        legacy_team = cl.user_session.get("agent_team")
        if not legacy_team:
            await cl.ErrorMessage(content="No active agent team found in session.").send()
            return

        # Update task list with processing task (only in tasklist mode)
        process_task = None
        if is_tasklist_mode and task_list:
            process_task = cl.Task(
                title="🧠 Processing with Agent Team", status=cl.TaskStatus.RUNNING
            )
            await task_list.add_task(process_task)

        # We'll process responses as they come in

        # Create a main message container for elements
        main_msg = cl.Message(content="", author="Agent")  # Use a generic author initially
        await main_msg.send()
        message_id = main_msg.id  # Get the ID of the container message

        # Initialize status tracking differently based on render mode
        task_status = {}
        if is_tasklist_mode:
            # Create status elements for tasklist mode
            task_status = {
                "overview": cl.Text(
                    name="task_overview", content="📊 **Task Overview:**\n", display="side"
                ),
                "planning": cl.Text(name="planning", content="🧩 **Planning:**\n", display="side"),
                "execution": cl.Text(
                    name="execution", content="⚙️ **Execution:**\n", display="side"
                ),
                "results": cl.Text(name="results", content="🎯 **Results:**\n", display="side"),
            }

            # Send status elements associated with the main message
            for element in task_status.values():
                await element.send(for_id=message_id)
        elif is_custom_mode:
            # For MCP profile, use a custom welcome element
            await cl.Custom(
                content={"type": "mcp_console", "data": "Initializing MCP environment..."}
            ).send()

        # Process input with agent team - Stream elements directly
        current_step = None  # Track the current step for streaming text

        # Run streaming with proper error handling
        try:
            # Directly use the async generator without awaiting it first
            async for chunk in legacy_team.run_stream(task=message.content):
                try:
                    # Process the response chunk to get structured data
                    processed_data, plan_update = await process_response(chunk)

                    # Skip if no data to process
                    if not processed_data:
                        continue

                    content_type = processed_data.get("type", "text")
                    content = processed_data.get("content", "")
                    author = _rename_author(
                        processed_data.get("author", "Agent")
                    )  # Use rename function
                    language = processed_data.get("language")  # For code

                    # Handle content based on render mode
                    if is_tasklist_mode:
                        # TaskList Mode (MagenticFleet profile)
                        if content_type == "text":
                            # Create new step if needed
                            if not isinstance(current_step, cl.Step):
                                current_step = cl.Step(
                                    name=f"Response from {author}", type="llm", show_input=False
                                )
                                await current_step.send()

                            # Stream text to current step
                            if isinstance(current_step, cl.Step):
                                try:
                                    await current_step.stream_token(content)
                                except Exception as e:
                                    logger.warning(f"Error streaming token: {e}")

                        else:
                            # Finalize any text step before sending other content
                            if isinstance(current_step, cl.Step):
                                await current_step.update()
                                current_step = None  # Reset step tracker

                            # Create appropriate element based on content type
                            try:
                                if content_type == "code":
                                    await cl.Message(
                                        content="",
                                        elements=[cl.Code(content=content, language=language)],
                                    ).send()
                                elif content_type == "image":
                                    await cl.Message(
                                        content="", elements=[cl.Image(url=content, name="image")]
                                    ).send()
                                elif content_type == "custom":
                                    await cl.Message(
                                        content="", elements=[cl.Custom(content=content)]
                                    ).send()
                                elif content_type == "error":
                                    await cl.ErrorMessage(content=content).send()
                            except Exception as e:
                                logger.warning(f"Error sending {content_type} element: {e}")

                    elif is_custom_mode:
                        # Custom Mode (MCP Focus profile)
                        if content_type == "text":
                            # Handle text accumulation for article-style rendering
                            if not isinstance(current_step, dict):
                                current_step = {"type": "article", "chunks": []}

                            # Add content to accumulated chunks
                            chunk_dict = current_step
                            if isinstance(chunk_dict.get("chunks"), list):
                                chunk_dict["chunks"].append(content)

                                # Check if we should send the accumulated text
                                chunks = chunk_dict["chunks"]
                                combined_text = "".join(chunks)
                                if len(combined_text) > 500 or "." in content:
                                    try:
                                        await cl.Custom(
                                            content={
                                                "type": "article",
                                                "data": combined_text,
                                                "author": author,
                                            }
                                        ).send()
                                    except Exception as e:
                                        logger.warning(f"Error sending article: {e}")

                                    # Reset accumulator
                                    current_step = {"type": "article", "chunks": []}

                        elif content_type in ["code", "image", "custom", "error"]:
                            # Reset text accumulator
                            current_step = None

                            # Send appropriate element based on content type
                            try:
                                if content_type == "code":
                                    await cl.Message(
                                        content="",
                                        elements=[
                                            cl.Custom(
                                                content={
                                                    "type": "rich_code",
                                                    "language": language or "text",
                                                    "data": content,
                                                    "author": author,
                                                }
                                            )
                                        ],
                                    ).send()
                                elif content_type == "image":
                                    await cl.Message(
                                        content="", elements=[cl.Image(url=content, name="image")]
                                    ).send()
                                elif content_type == "custom":
                                    await cl.Message(
                                        content="", elements=[cl.Custom(content=content)]
                                    ).send()
                                elif content_type == "error":
                                    await cl.ErrorMessage(content=content).send()
                            except Exception as e:
                                logger.warning(f"Error sending {content_type} element: {e}")

                    elif is_canvas_mode:
                        # Canvas Mode
                        try:
                            # Generate a unique ID for the node
                            node_id = f"node_{len(cl.user_session.get('canvas_data', {}).get('nodes', []))}"

                            if content_type == "text":
                                # Add text content as a node to the canvas
                                await add_node_to_canvas(
                                    node_id=node_id,
                                    node_type="text",
                                    content=content,
                                    metadata={"author": author},
                                )
                            elif content_type == "code":
                                # Add code content as a node to the canvas
                                await add_node_to_canvas(
                                    node_id=node_id,
                                    node_type="code",
                                    content=content,
                                    metadata={"language": language or "text", "author": author},
                                )
                            elif content_type == "image":
                                # Add image content as a node to the canvas
                                await add_node_to_canvas(
                                    node_id=node_id,
                                    node_type="image",
                                    content=content,
                                    metadata={"author": author},
                                )
                            elif content_type == "custom":
                                # Add custom content as a node to the canvas
                                await add_node_to_canvas(
                                    node_id=node_id,
                                    node_type="custom",
                                    content=str(content),
                                    metadata={"author": author},
                                )
                            elif content_type == "error":
                                # Add error content as a node to the canvas
                                await add_node_to_canvas(
                                    node_id=node_id,
                                    node_type="error",
                                    content=content,
                                    metadata={"author": author},
                                )

                            # If there's a previous node, add an edge between them
                            previous_node_id = cl.user_session.get("previous_node_id")
                            if previous_node_id:
                                edge_id = f"edge_{len(cl.user_session.get('canvas_data', {}).get('edges', []))}"
                                await add_edge_to_canvas(
                                    edge_id=edge_id,
                                    source_id=previous_node_id,
                                    target_id=node_id,
                                    edge_type="default",
                                )

                            # Store the current node ID for the next iteration
                            cl.user_session.set("previous_node_id", node_id)

                        except Exception as e:
                            logger.warning(f"Error adding content to canvas: {e}")

                    # Handle plan updates if detected
                    if plan_update:
                        # Finalize any text step first
                        if isinstance(current_step, cl.Step):
                            await current_step.update()
                            current_step = None

                        # Process plan in tasklist mode
                        if is_tasklist_mode and task_list and task_status:
                            plan_steps = cl.user_session.get("plan_steps") or {}
                            try:
                                await extract_and_add_plan_tasks(
                                    plan_update,
                                    task_list,
                                    task_status,
                                    message_id,
                                    is_update=len(plan_steps) > 0,
                                )
                            except Exception as e:
                                logger.warning(f"Error processing plan update: {e}")

                except Exception as e:
                    # Log and handle chunk processing errors
                    logger.error(f"Error processing chunk: {e}")
                    await cl.ErrorMessage(
                        content=f"Error processing response chunk: {str(e)}"
                    ).send()

        except Exception as e:
            # Log and handle stream-level errors
            logger.error(f"Streaming error: {e}")
            await cl.ErrorMessage(content=f"Streaming error: {str(e)}").send()

        # Finalize any remaining step
        if current_step is not None:
            try:
                if isinstance(current_step, cl.Step):
                    await current_step.update()
                elif isinstance(current_step, dict) and isinstance(
                    current_step.get("chunks"), list
                ):
                    chunks = current_step["chunks"]
                    combined_text = "".join(chunks)
                    if combined_text.strip():
                        # Provide a default author
                        final_author = "Agent"
                        if "author" in locals():
                            final_author = author

                        await cl.Custom(
                            content={
                                "type": "article",
                                "data": combined_text,
                                "author": final_author,
                            }
                        ).send()
            except Exception as e:
                logger.warning(f"Error finalizing step: {e}")

        # Complete task processing
        if is_tasklist_mode and task_list is not None:
            try:
                if process_task is not None:
                    process_task.status = cl.TaskStatus.DONE
                    process_task.title = "✅ Processing complete"
                await task_list.send()
            except Exception as e:
                logger.warning(f"Error completing task: {e}")

        # Update main message
        try:
            main_msg.content = "Processing complete."
            await main_msg.update()

            # Store agent response in chat history
            try:
                from agentic_fleet.schemas.message import MessageCreate, MessageType

                agent_message = MessageCreate(
                    content=main_msg.content,
                    sender="Agent",
                    receiver="User",
                    message_type=MessageType.TEXT,
                    session_id=session_id,
                    metadata={},
                )
                await chat_service.process_message(agent_message)
            except Exception as e:
                logger.warning(f"Error storing agent message in chat history: {e}")
        except Exception as e:
            logger.warning(f"Error updating main message: {e}")

        # Send final actions
        try:
            await cl.Message(
                content="Actions:",
                actions=[
                    cl.Action(
                        name="refine_response",
                        label="🔄 Refine Response",
                        tooltip="Ask the agent to refine this response",
                        payload={"action": "refine"},
                    ),
                    cl.Action(
                        name="save_response",
                        label="💾 Save Response",
                        tooltip="Save this response for later",
                        payload={"action": "save"},
                    ),
                ],
            ).send()
        except Exception as e:
            logger.warning(f"Error sending action message: {e}")

    except Exception as e:
        # Log the overall error
        logger.error(f"Error processing message: {str(e)}")
        logger.error(traceback.format_exc())

        # Update task list to show failure
        if task_list:
            try:
                task_list.status = f"⚠️ Error: {str(e)}"
                await task_list.send()
            except Exception:
                pass  # Ignore errors when trying to report errors

        # Send error message to user
        try:
            await cl.Message(
                content=f"An error occurred while processing your request: {str(e)}",
            ).send()
        except Exception:
            pass  # Ignore errors when trying to report errors


async def on_reset(_: cl.Action) -> None:
    """Reset the agent team.

    Args:
        action: The action triggering the reset
    """
    try:
        # Reinitialize the application
        await cl.Message(content="🔄 Resetting agent team...").send()

        # Trigger chat restart
        await cl.ChatRestartEvent().send()
    except Exception as e:
        logger.error(f"Error during reset: {e}")
        await cl.Message(content=f"Error during reset: {str(e)}").send()


def _rename_author(orig_author: str) -> str:
    """Friendly agent names with emoji indicators.

    Args:
        orig_author: The original author name

    Returns:
        A formatted author name with emoji
    """
    rename_map = {
        "MagenticOne": "🤖 Magentic Assistant",
        "Orchestrator": "🎼 Orchestrator",
        "WebSurfer": "🌐 Web Navigator",
        "FileSurfer": "📁 File Explorer",
        "Coder": "👨‍💻 Code Architect",
        "Executor": "⚡ Action Runner",
        "System": "🛠️ System",
        "Tool Manager": "🔧 Tool Manager",
        "Assistant": "🤖 Assistant",
        "user": "👤 User",
        "Chatbot": "💬 Assistant",
    }
    # If the author is already prefixed with an emoji, return as is
    if orig_author and any(ord(c) > 0x1F00 for c in orig_author):
        return orig_author
    return rename_map.get(orig_author, f"🔹 {orig_author}")

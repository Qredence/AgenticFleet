"""MCP panel UI components.

This module provides UI components for displaying MCP information.
"""

import json
import logging
from typing import Any

import chainlit as cl

from agentic_fleet.pool.mcp.mcp_factory import get_available_mcp_configs

logger = logging.getLogger(__name__)


async def list_available_mcps() -> list[dict[str, Any]]:
    """List available MCP connections and their tools.

    Returns:
        List of MCP server configurations
    """
    try:
        # Get connected MCP servers from user session
        mcp_servers = cl.user_session.get("mcp_servers", [])

        if not mcp_servers or len(mcp_servers) == 0:
            await cl.Message(
                content="No MCP servers currently connected. Use the MCP panel to connect to an MCP server.",
                author="MCP Manager",
            ).send()
            return []

        # Build a markdown list of all tools
        mcp_tools_list = "# Available MCP Tools\n\n"

        # Process each server
        for server in mcp_servers:
            server_name = server.get("name", "Unknown")
            server_type = server.get("connection_type", "Unknown")
            server_tools = server.get("tools", [])

            mcp_tools_list += f"## {server_name} ({server_type})\n"

            if not server_tools:
                mcp_tools_list += "No tools available from this server.\n\n"
                continue

            for tool in server_tools:
                tool_name = tool.get("name", "Unnamed Tool")
                tool_desc = tool.get("description", "No description available")
                mcp_tools_list += f"- **{tool_name}**: {tool_desc}\n"

            mcp_tools_list += "\n"

        # Send the tools list
        await cl.Message(
            content=mcp_tools_list,
            author="MCP Manager",
        ).send()

        # Return the list of servers
        return mcp_servers

    except Exception as e:
        logger.error(f"Error retrieving MCP tools: {e}")
        await cl.Message(
            content=f"Error retrieving MCP tools: {str(e)}",
            author="MCP Manager",
        ).send()
        return []


async def send_mcp_panel(mcp_id: str) -> None:
    """Send the MCP panel for the specified MCP.

    Args:
        mcp_id: The ID of the MCP to display
    """
    try:
        # Get available MCP configurations
        mcp_configs = get_available_mcp_configs()

        if mcp_id not in mcp_configs:
            await cl.Message(
                content=f"Error: MCP configuration '{mcp_id}' not found.", author="MCP Manager"
            ).send()
            return

        # Get the MCP configuration
        mcp_config = mcp_configs[mcp_id]

        # Build the panel content
        panel_content = f"# MCP: {mcp_config.get('name', mcp_id)}\n\n"
        panel_content += f"**Type**: {mcp_config.get('type', 'base_mcp')}\n"
        panel_content += (
            f"**Description**: {mcp_config.get('description', 'No description available')}\n\n"
        )

        # Add configuration details
        panel_content += "## Configuration\n\n"
        panel_content += "```json\n"
        panel_content += json.dumps(mcp_config, indent=2)
        panel_content += "\n```\n\n"

        # Add actions
        actions = [
            cl.Action(
                name="connect_mcp",
                label="🔌 Connect",
                tooltip="Connect to this MCP",
                payload={"mcp_id": mcp_id},
            ),
            cl.Action(
                name="disconnect_mcp",
                label="❌ Disconnect",
                tooltip="Disconnect from this MCP",
                payload={"mcp_id": mcp_id},
            ),
        ]

        # Send the panel
        await cl.Message(content=panel_content, author="MCP Manager", actions=actions).send()

    except Exception as e:
        logger.error(f"Error sending MCP panel: {e}")
        await cl.Message(content=f"Error sending MCP panel: {str(e)}", author="MCP Manager").send()


async def call_mcp_tool(server_name: str, tool_name: str, tool_args: dict[str, Any]) -> Any:
    """Call an MCP tool.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool to call
        tool_args: Arguments for the tool

    Returns:
        The result from the tool execution
    """
    try:
        # Get MCP servers from user session
        mcp_servers = cl.user_session.get("mcp_servers", [])

        # Find the server with the specified name
        server = None
        for s in mcp_servers:
            if s.get("name") == server_name:
                server = s
                break

        if not server:
            error_msg = f"MCP server '{server_name}' not connected"
            await cl.Message(content=f"⚠️ {error_msg}", author="MCP Manager").send()
            raise ValueError(error_msg)

        # Get the MCP instance
        mcp_instance = server.get("instance")
        if not mcp_instance:
            error_msg = f"MCP instance for server '{server_name}' not found"
            await cl.Message(content=f"⚠️ {error_msg}", author="MCP Manager").send()
            raise ValueError(error_msg)

        # Send a message showing what we're calling
        await cl.Message(
            content=f"Calling MCP tool: `{tool_name}` on server `{server_name}`\nArguments: ```json\n{str(tool_args)}\n```",
            author="MCP Manager",
        ).send()

        # Call the tool and get the result
        # Note: This assumes the MCP instance has a call_tool method
        # If it doesn't, this will need to be updated based on the actual API
        if hasattr(mcp_instance, "call_tool"):
            result = await mcp_instance.call_tool(tool_name, tool_args)
        else:
            # Fallback to using the register_tool/process_message pattern
            # This is a simplified implementation and may need to be adjusted
            await mcp_instance.register_tool(tool_name, tool_args)
            result = await mcp_instance.process_message(
                sender_id="user",
                message=f"Call tool {tool_name}",
                metadata={"tool_args": tool_args},
            )

        # Send back the result
        result_str = str(result) if result is not None else "No result returned"
        await cl.Message(
            content=f"MCP tool result:\n```json\n{result_str}\n```", author="MCP Manager"
        ).send()

        return result

    except Exception as e:
        error_msg = f"Error calling MCP tool '{tool_name}': {str(e)}"
        logger.error(error_msg)

        # Show error in the UI
        await cl.Message(content=f"⚠️ {error_msg}", author="MCP Manager").send()
        raise

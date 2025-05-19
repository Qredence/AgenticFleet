"""MCP connection handlers for AgenticFleet.

This module contains handlers for Model Context Protocol (MCP) connections.
"""

import logging
from typing import Any

import chainlit as cl

# Initialize logger
logger = logging.getLogger(__name__)

# Store MCP server connections
MCP_SERVERS = {}


@cl.on_mcp_connect
async def on_mcp_connect(connection, session):
    """Handler for when an MCP connection is established.

    This function is called when a new MCP connection is established.
    It registers the connection in the MCP_SERVERS dictionary.

    Args:
        connection: The MCP connection object
        session: The MCP client session
    """
    logger.info(f"MCP connection established: {connection.name}")

    # Store the connection
    MCP_SERVERS[connection.name] = {
        "connection": connection,
        "session": session,
        "capabilities": connection.capabilities,
    }

    # Log capabilities
    logger.debug(f"MCP capabilities: {connection.capabilities}")

    # Update UI with connection status
    await cl.Message(
        content=f"Connected to MCP server: {connection.name}",
        author="System",
    ).send()


@cl.on_mcp_disconnect
async def on_mcp_disconnect(name, session):
    """Handler for when an MCP connection is terminated.

    Args:
        name: The name of the MCP connection
        session: The MCP client session
    """
    logger.info(f"MCP connection terminated: {name}")

    # Remove the connection from the registry
    if name in MCP_SERVERS:
        del MCP_SERVERS[name]

    # Update UI with connection status
    await cl.Message(
        content=f"Disconnected from MCP server: {name}",
        author="System",
    ).send()


async def call_mcp_tool(server_name: str, tool_name: str, tool_args: dict[str, Any]):
    """Call an MCP tool with the given arguments.

    This function can be used as part of a step to call MCP tools.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool to call
        tool_args: Arguments for the tool

    Returns:
        The result from the tool execution
    """
    logger.info(f"Calling MCP tool: {tool_name} on server {server_name}")

    # Check if the server exists
    if server_name not in MCP_SERVERS:
        error_msg = (
            f"MCP server '{server_name}' not found. Available servers: {list(MCP_SERVERS.keys())}"
        )
        logger.error(error_msg)
        return {"error": error_msg}

    # Get the connection
    connection = MCP_SERVERS[server_name]["connection"]

    try:
        # Call the tool
        result = await connection.call_tool(tool_name, tool_args)
        logger.debug(f"MCP tool result: {result}")
        return result
    except Exception as e:
        error_msg = f"Error calling MCP tool {tool_name}: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

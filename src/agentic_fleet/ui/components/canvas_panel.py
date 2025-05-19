"""Canvas panel UI components.

This module provides UI components for displaying a Canvas-like interface.
"""

import logging
from typing import Any

import chainlit as cl

logger = logging.getLogger(__name__)


async def initialize_canvas() -> None:
    """Initialize the canvas interface.

    This function creates and sends the initial canvas component.
    """
    try:
        # Create a canvas container with initial empty state
        canvas_data = {
            "type": "canvas",
            "nodes": [],
            "edges": [],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }

        # Send the canvas component
        await cl.Custom(content=canvas_data).send()

        # Store canvas data in user session for later updates
        cl.user_session.set("canvas_data", canvas_data)

        logger.info("Canvas interface initialized")
    except Exception as e:
        logger.error(f"Error initializing canvas: {e}")
        await cl.Message(
            content=f"Error initializing canvas interface: {str(e)}", author="System"
        ).send()


async def add_node_to_canvas(
    node_id: str,
    node_type: str,
    content: str,
    position: dict[str, int] = None,
    metadata: dict[str, Any] = None,
) -> None:
    """Add a node to the canvas.

    Args:
        node_id: Unique identifier for the node
        node_type: Type of node (e.g., "text", "code", "image")
        content: Content of the node
        position: Optional position {x, y} for the node
        metadata: Optional additional metadata for the node
    """
    try:
        # Get current canvas data from session
        canvas_data = cl.user_session.get("canvas_data")
        if not canvas_data:
            logger.warning("Canvas data not found in session")
            await initialize_canvas()
            canvas_data = cl.user_session.get("canvas_data")

        # Set default position if not provided
        if not position:
            # Calculate position based on existing nodes
            nodes = canvas_data.get("nodes", [])
            x_offset = len(nodes) * 50 % 300  # Wrap after 300px
            y_offset = (len(nodes) // 6) * 100  # New row every 6 nodes
            position = {"x": 100 + x_offset, "y": 100 + y_offset}

        # Create new node
        new_node = {
            "id": node_id,
            "type": node_type,
            "content": content,
            "position": position,
            "metadata": metadata or {},
        }

        # Add node to canvas data
        canvas_data["nodes"].append(new_node)

        # Update canvas data in session
        cl.user_session.set("canvas_data", canvas_data)

        # Send updated canvas
        await cl.Custom(content=canvas_data).send()

        logger.info(f"Added node {node_id} to canvas")
    except Exception as e:
        logger.error(f"Error adding node to canvas: {e}")
        await cl.Message(content=f"Error adding node to canvas: {str(e)}", author="System").send()


async def add_edge_to_canvas(
    edge_id: str,
    source_id: str,
    target_id: str,
    label: str = None,
    edge_type: str = "default",
    metadata: dict[str, Any] = None,
) -> None:
    """Add an edge between nodes on the canvas.

    Args:
        edge_id: Unique identifier for the edge
        source_id: ID of the source node
        target_id: ID of the target node
        label: Optional label for the edge
        edge_type: Type of edge (e.g., "default", "dashed")
        metadata: Optional additional metadata for the edge
    """
    try:
        # Get current canvas data from session
        canvas_data = cl.user_session.get("canvas_data")
        if not canvas_data:
            logger.warning("Canvas data not found in session")
            return

        # Create new edge
        new_edge = {
            "id": edge_id,
            "source": source_id,
            "target": target_id,
            "label": label,
            "type": edge_type,
            "metadata": metadata or {},
        }

        # Add edge to canvas data
        canvas_data["edges"].append(new_edge)

        # Update canvas data in session
        cl.user_session.set("canvas_data", canvas_data)

        # Send updated canvas
        await cl.Custom(content=canvas_data).send()

        logger.info(f"Added edge {edge_id} to canvas")
    except Exception as e:
        logger.error(f"Error adding edge to canvas: {e}")
        await cl.Message(content=f"Error adding edge to canvas: {str(e)}", author="System").send()


async def update_canvas_viewport(x: int, y: int, zoom: float) -> None:
    """Update the canvas viewport.

    Args:
        x: X coordinate of the viewport
        y: Y coordinate of the viewport
        zoom: Zoom level of the viewport
    """
    try:
        # Get current canvas data from session
        canvas_data = cl.user_session.get("canvas_data")
        if not canvas_data:
            logger.warning("Canvas data not found in session")
            return

        # Update viewport
        canvas_data["viewport"] = {"x": x, "y": y, "zoom": zoom}

        # Update canvas data in session
        cl.user_session.set("canvas_data", canvas_data)

        # Send updated canvas
        await cl.Custom(content=canvas_data).send()

        logger.info(f"Updated canvas viewport to x={x}, y={y}, zoom={zoom}")
    except Exception as e:
        logger.error(f"Error updating canvas viewport: {e}")

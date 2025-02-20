"""
This module provides wrappers for agents from the autogen-ext package.

It imports the following agents:
    - FileSurferAgent
    - MagenticOneAgent
    - OpenAIAgent
    - VideoSurferAgent
    - WebSurferAgent

Developers can use or re-export these agents as needed in the project.
"""

from autogen_ext.agents.file_surfer import FileSurferAgent
from autogen_ext.agents.magentic_one import MagenticOneAgent
from autogen_ext.agents.openai import OpenAIAgent
from autogen_ext.agents.video_surfer import VideoSurferAgent
from autogen_ext.agents.web_surfer import WebSurferAgent

__all__ = [
    "FileSurferAgent",
    "MagenticOneAgent",
    "OpenAIAgent",
    "VideoSurferAgent",
    "WebSurferAgent",
]

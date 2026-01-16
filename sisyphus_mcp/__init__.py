"""
Oh-My-Antigravity-Sisyphus MCP Server

Multi-agent orchestration system for Antigravity IDE.
Provides MCP tools for task management, workflow automation, and completion verification.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from sisyphus_mcp.server import create_server, run_server

__all__ = ["create_server", "run_server", "__version__"]

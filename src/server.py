#!/usr/bin/env python3
import os
import sys
import json
import logging
import asyncio
from typing import Any, Dict, List, Sequence

import mcp.server.stdio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Resource, TextContent, ImageContent, EmbeddedResource

from dotenv import load_dotenv

from .tools import get_quip_tools, handle_quip_read_spreadsheet

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("quip-mcp-server")

def main():
    """
    Entry point for the Quip MCP server when used as a console script
    """
    # Check for required environment variables before running async_main
    quip_token = os.environ.get("QUIP_TOKEN")
    if not quip_token:
        logger.error("QUIP_TOKEN environment variable is not set")
        logger.error("Please set the QUIP_TOKEN environment variable to your Quip API token")
        sys.exit(1)
        
    asyncio.run(async_main())

async def async_main():
    """
    Main entry point for the Quip MCP server
    """
    logger.info("Starting Quip MCP Server")
    
    # Check for required environment variables
    quip_token = os.environ.get("QUIP_TOKEN")
    if not quip_token:
        logger.error("QUIP_TOKEN environment variable is not set")
        logger.error("Please set the QUIP_TOKEN environment variable to your Quip API token")
        sys.exit(1)
    
    # Create the MCP server
    server = Server("quip-mcp-server")
    
    # Register handlers
    @server.list_tools()
    async def list_tools() -> List[Resource]:
        """List available Quip tools"""
        logger.debug("Handling list_tools request")
        return get_quip_tools()
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls"""
        logger.info(f"Handling tool call: {name}")
        logger.debug(f"Tool arguments: {arguments}")
        
        if not isinstance(arguments, dict):
            logger.error("Invalid arguments: not a dictionary")
            raise ValueError("Invalid arguments")
        
        try:
            if name == "quip_read_spreadsheet":
                return await handle_quip_read_spreadsheet(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Tool call failed: {str(e)}")
            raise RuntimeError(f"Tool call failed: {str(e)}")
    
    # Start the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="quip-mcp-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    main()

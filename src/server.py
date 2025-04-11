#!/usr/bin/env python3
import os
import sys
import logging
import asyncio
import argparse
from typing import Any, List, Sequence, Optional
from urllib.parse import urlparse, parse_qs

import mcp.server.stdio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Resource, TextContent, ImageContent, EmbeddedResource, ResourceTemplate

from dotenv import load_dotenv

from .version import __version__
from .tools import get_quip_tools, handle_quip_read_spreadsheet
from .storage import create_storage, StorageInterface

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
def configure_logging(args=None):
    """
    Configure logging based on environment variables and command line arguments
    
    Args:
        args: Command line arguments (optional)
    """
    # Default level is WARN
    log_level = logging.WARN
    
    # Check environment variable for debug mode
    if os.environ.get("QUIP_DEBUG") == "1":
        log_level = logging.DEBUG
    
    # Command line argument overrides environment variable
    if args and getattr(args, "debug", False):
        log_level = logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger("quip-mcp-server")

# Initialize logger with default configuration for imports and tests
logger = logging.getLogger("quip-mcp-server")
# Configure the logger with default settings (will be reconfigured in main() with args)
logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Global storage instance
storage_instance: Optional[StorageInterface] = None

# Global server instance for testing
server_instance: Optional[Server] = None

def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Quip MCP Server")
    parser.add_argument(
        "--storage-path",
        help="Path to store CSV files (default: from QUIP_STORAGE_PATH env var or ~/.quip-mcp-server/storage)"
    )
    parser.add_argument(
        "--file-protocol",
        action="store_true",
        help="Use file protocol for resource URIs"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    return parser.parse_args()

def get_storage_path(args):
    """
    Get storage path from command line arguments or environment variables
    
    Args:
        args: Command line arguments
        
    Returns:
        str: Storage path
    """
    # First try command line argument
    if args.storage_path:
        return args.storage_path
    
    # Then try environment variable
    storage_path = os.environ.get("QUIP_STORAGE_PATH")
    if storage_path:
        return storage_path
    
    # Default to ~/.quip-mcp-server/storage
    default_path = os.path.join(os.path.expanduser("~"), ".quip-mcp-server", "storage")
    logger.info(f"Using default storage path: {default_path}")
    return default_path

def main():
    """
    Entry point for the Quip MCP server when used as a console script
    """
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Reconfigure logging with command line arguments
        configure_logging(args)
        
        # Check for required environment variables before running async_main
        quip_token = os.environ.get("QUIP_TOKEN")
        if not quip_token:
            logger.error("QUIP_TOKEN environment variable is not set")
            logger.error("Please set the QUIP_TOKEN environment variable to your Quip API token")
            sys.exit(1)
        
        # Get storage path
        storage_path = get_storage_path(args)
        
        # Initialize storage
        global storage_instance
        storage_instance = create_storage(storage_type="local", storage_path=storage_path, is_file_protocol=args.file_protocol)
        
        asyncio.run(async_main(args))
    except SystemExit as e:
        # Re-raise the SystemExit exception to preserve the exit code
        raise e
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        sys.exit(2)

async def async_main(args):
    """
    Main entry point for the Quip MCP server
    
    Args:
        args: Command line arguments
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
    
    # Register resource templates
    @server.list_resource_templates()
    async def list_resource_templates():
        return [
            ResourceTemplate(
                uri_template="file://{storage_path}/{thread_id}-{sheet_name}.csv",
                description="Quip spreadsheet resource in local file system"
            ) if args.file_protocol else
                ResourceTemplate(
                    uri_template="quip://{thread_id}",
                    description="Quip spreadsheet resource"
                )
        ]
    
    # Register handlers
    @server.list_tools()
    async def list_tools() -> List[Resource]:
        """List available Quip tools"""
        logger.debug("Handling list_tools request")
        return get_quip_tools()
        
    @server.list_resources()
    async def list_resources() -> List[Resource]:
        """List available Quip resources"""
        logger.debug("Handling list_resources request")
        return await discover_resources(args.file_protocol)
    # Register resource handler
    @server.read_resource()
    async def handle_resource_access(uri: str) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Resource access handler wrapper"""
        return await access_resource(uri)
    
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
                global storage_instance
                return await handle_quip_read_spreadsheet(arguments, storage_instance)
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
                server_version=__version__,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

async def discover_resources(isFileProtocol: bool) -> List[Resource]:
    """
    Discover available resources by scanning the storage directory
    
    Returns:
        List[Resource]: List of available resources
    """
    logger.info("Discovering resources")
    
    global storage_instance
    if not storage_instance:
        logger.error("Storage not initialized")
        return []
    
    # Check if storage is LocalStorage
    if not hasattr(storage_instance, "storage_path"):
        logger.warning("Storage is not LocalStorage, cannot discover resources")
        return []
    
    resources = []
    storage_path = storage_instance.storage_path
    
    try:
        # Scan storage directory for CSV files
        for filename in os.listdir(storage_path):
            if filename.endswith(".csv") and not filename.endswith(".meta"):
                # Parse filename to get thread_id and sheet_name
                file_path = os.path.join(storage_path, filename)
                
                # Extract thread_id and sheet_name from filename
                if "-" in filename:
                    # Format: {thread_id}-{sheet_name}.csv
                    thread_id = filename.split("-")[0]
                    sheet_name = "-".join(filename.split("-")[1:]).replace(".csv", "")
                else:
                    # Format: {thread_id}.csv
                    thread_id = filename.replace(".csv", "")
                    sheet_name = None
                
                # Get metadata
                metadata = storage_instance.get_metadata(thread_id, sheet_name)
                
                # Create resource URI
                if isFileProtocol:
                    resource_uri = f"file://{file_path}"
                else:
                    # Use resource template to create resource URI
                    resource_uri = storage_instance.get_resource_uri(thread_id, sheet_name)
                
                # Create resource name
                resource_name = f"Quip Thread(Spreadsheet): {thread_id}"
                if sheet_name:
                    resource_name += f" (Sheet: {sheet_name})"
                if isFileProtocol:
                    resource_name += f" You can access the file at: {file_path}"
                
                # Create resource description
                description = f"CSV data from Quip spreadsheet. {metadata.get('total_rows', 0)} rows, {metadata.get('total_size', 0)} bytes."
                
                # Create resource
                resource = Resource(
                    uri=resource_uri,
                    name=resource_name,
                    description=description,
                    mime_type="text/csv"
                )
                
                resources.append(resource)
                logger.info(f"Discovered resource: {resource_uri}")
    
    except Exception as e:
        logger.error(f"Error discovering resources: {str(e)}")
    
    logger.info(f"Discovered {len(resources)} resources")
    return resources

async def access_resource(uri: str) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """
    Handle resource access requests
    
    Args:
        uri: Resource URI
        
    Returns:
        Sequence of content objects
    """
    logger.info(f"Handling resource access: {uri}")
    
    # Parse the URI
    parsed_uri = urlparse(uri)
    
    if parsed_uri.scheme not in ("quip", "file"):
        raise ValueError(f"Unsupported URI scheme: {parsed_uri.scheme}")
    
    # Extract thread_id and sheet_name
    if parsed_uri.scheme == "file":
        filename = parsed_uri.path.split("/")[-1].replace(".csv", "").split("-")
        thread_id = filename[0]
        sheet_name = "-".join(filename[1:]) if len(filename) > 1 else None
    else:
        thread_id = parsed_uri.netloc
        query_params = parse_qs(parsed_uri.query)
        sheet_name = query_params.get("sheet", [None])[0]
    
    logger.info(f"Accessing resource for thread_id: {thread_id}, sheet_name: {sheet_name}")
    
    # Get the CSV content from storage
    global storage_instance
    if not storage_instance:
        raise RuntimeError("Storage not initialized")
    
    csv_content = storage_instance.get_csv(thread_id, sheet_name)
    if not csv_content:
        raise ValueError(f"Resource not found: {uri}")
    
    # Return the full CSV content
    return [TextContent(type="text", text=csv_content)]


if __name__ == "__main__":
    main()

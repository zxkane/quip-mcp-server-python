import os
import json
import tempfile
import logging
from typing import Dict, Any, List, Optional

from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

from .quip_client import QuipClient, convert_xlsx_to_csv

# Initialize logger
logger = logging.getLogger("quip-mcp-server")

def get_quip_tools() -> List[Tool]:
    """
    Get the list of Quip tools available in this MCP server

    Returns:
        List of Tool objects
    """
    return [
        Tool(
            name="quip_read_spreadsheet",
            description="Read the content of a Quip document by its thread ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "threadId": {
                        "type": "string",
                        "description": "The Quip document thread ID"
                    },
                    "sheetName": {
                        "type": "string",
                        "description": "Optional sheet or tab name to read from"
                    }
                },
                "required": ["threadId"]
            }
        )
    ]

async def handle_quip_read_spreadsheet(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Handle the quip_read_spreadsheet tool
    
    Args:
        arguments: Dictionary containing the tool arguments
        
    Returns:
        List of TextContent objects
        
    Raises:
        ValueError: If the thread is not a spreadsheet or the sheet is not found
    """
    thread_id = arguments.get("threadId")
    sheet_name = arguments.get("sheetName")
    
    if not thread_id:
        raise ValueError("threadId is required")
    
    logger.info(f"Reading spreadsheet from thread {thread_id}, sheet: {sheet_name or 'default'}")
    
    # Get Quip token from environment
    quip_token = os.environ.get("QUIP_TOKEN")
    quip_base_url = os.environ.get("QUIP_BASE_URL", "https://platform.quip.com")
    
    if not quip_token:
        raise ValueError("QUIP_TOKEN environment variable is not set")
    
    # Initialize Quip client
    client = QuipClient(access_token=quip_token, base_url=quip_base_url)
    
    # Check if the thread is a spreadsheet
    if not client.is_spreadsheet(thread_id):
        raise ValueError(f"Thread {thread_id} is not a spreadsheet or does not exist")
    
    # Try primary export method first
    csv_data = None
    used_fallback = False
    error_message = None
    
    try:
        # Export thread to XLSX first
        logger.info(f"Attempting primary export method: XLSX for thread {thread_id}")
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
            xlsx_path = temp_file.name
        
        client.export_thread_to_xlsx(thread_id, xlsx_path)
        
        # Convert XLSX to CSV
        logger.info(f"Converting sheet '{sheet_name or 'default'}' from XLSX to CSV")
        csv_data = convert_xlsx_to_csv(xlsx_path, sheet_name)
        
    except Exception as e:
        error_message = str(e)
        logger.warning(f"Primary export method failed: {error_message}")
        logger.info("Attempting fallback export method")
        
        try:
            # Try fallback method
            csv_data = client.export_thread_to_csv_fallback(thread_id, sheet_name)
            used_fallback = True
            logger.info("Successfully exported using fallback method")
        except Exception as fallback_error:
            logger.error(f"Fallback export method also failed: {str(fallback_error)}")
            raise ValueError(f"Failed to export spreadsheet. Primary error: {error_message}, Fallback error: {str(fallback_error)}")
    finally:
        # Clean up temporary XLSX file if it exists
        if 'xlsx_path' in locals() and os.path.exists(xlsx_path):
            try:
                os.remove(xlsx_path)
                logger.info(f"Cleaned up temporary XLSX file: {xlsx_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary XLSX file: {str(e)}")
    
    if not csv_data:
        raise ValueError("Failed to export data: no CSV content generated")
    
    # Return the CSV data
    return [TextContent(type="text", text=csv_data)]

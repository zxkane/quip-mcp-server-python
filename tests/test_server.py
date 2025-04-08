#!/usr/bin/env python3
"""
Tests for the Quip MCP server.
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.server import main, async_main
from src.quip_client import QuipClient
from src.tools import get_quip_tools, handle_quip_read_spreadsheet


def test_get_quip_tools():
    """Test that get_quip_tools returns a list of tools"""
    tools = get_quip_tools()
    assert len(tools) > 0
    assert any(tool.name == "quip_read_spreadsheet" for tool in tools)


@patch('src.tools.QuipClient')
@pytest.mark.asyncio
async def test_handle_quip_read_spreadsheet_missing_thread_id(mock_quip_client):
    """Test that handle_quip_read_spreadsheet raises an error when threadId is missing"""
    with pytest.raises(ValueError, match="threadId is required"):
        await handle_quip_read_spreadsheet({})


@patch('src.tools.QuipClient')
@patch('os.environ.get')
@pytest.mark.asyncio
async def test_handle_quip_read_spreadsheet_not_spreadsheet(mock_environ_get, mock_quip_client):
    """Test that handle_quip_read_spreadsheet raises an error when thread is not a spreadsheet"""
    # Setup mocks
    mock_environ_get.return_value = "fake_token"  # Mock QUIP_TOKEN
    
    mock_instance = MagicMock()
    mock_quip_client.return_value = mock_instance
    mock_instance.is_spreadsheet.return_value = False
    
    # Test
    with pytest.raises(ValueError, match="Thread .* is not a spreadsheet"):
        await handle_quip_read_spreadsheet({"threadId": "test_thread_id"})


@patch('os.environ.get')
@patch('asyncio.run')
def test_main_missing_token(mock_asyncio_run, mock_environ_get):
    """Test that main raises an error when QUIP_TOKEN is missing"""
    # Configure the mock to return None for QUIP_TOKEN and something else for other calls
    def mock_get(key, default=None):
        if key == "QUIP_TOKEN":
            return None
        return default
    
    mock_environ_get.side_effect = mock_get
    
    # Mock asyncio.run to avoid actually running the async code
    mock_asyncio_run.return_value = None
    
    # Redirect stderr to capture the error message
    with patch('sys.exit') as mock_exit:
        with patch('src.server.logger.error') as mock_logger_error:
            main()
            mock_exit.assert_called_once_with(1)
            # Check that the error message was logged
            mock_logger_error.assert_any_call("QUIP_TOKEN environment variable is not set")

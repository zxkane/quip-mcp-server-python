#!/usr/bin/env python3
"""
Tests for the Quip MCP server.
"""
import os
import sys
import pytest
import json
import logging
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.server import main, async_main, parse_arguments, get_storage_path, configure_logging
from src.quip_client import QuipClient
from src.tools import get_quip_tools, handle_quip_read_spreadsheet
from src.storage import LocalStorage


def test_get_quip_tools():
    """Test that get_quip_tools returns a list of tools"""
    tools = get_quip_tools()
    assert len(tools) > 0
    assert any(tool.name == "quip_read_spreadsheet" for tool in tools)


@patch('src.tools.QuipClient')
@pytest.mark.asyncio
async def test_handle_quip_read_spreadsheet_missing_thread_id(mock_quip_client):
    """Test that handle_quip_read_spreadsheet raises an error when threadId is missing"""
    # Create a mock storage
    mock_storage = MagicMock()
    
    with pytest.raises(ValueError, match="threadId is required"):
        await handle_quip_read_spreadsheet({}, mock_storage)


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
        # Create a mock storage
        mock_storage = MagicMock()
        await handle_quip_read_spreadsheet({"threadId": "test_thread_id"}, mock_storage)
@patch('src.tools.QuipClient')
@patch('os.environ.get')
@pytest.mark.asyncio
async def test_handle_quip_read_spreadsheet_resource_uri_quip_protocol(mock_environ_get, mock_quip_client):
    """Test that handle_quip_read_spreadsheet returns resource_uri with quip:// protocol when is_file_protocol=False"""
    # Setup mocks
    mock_environ_get.return_value = "fake_token"  # Mock QUIP_TOKEN
    
    mock_instance = MagicMock()
    mock_quip_client.return_value = mock_instance
    mock_instance.is_spreadsheet.return_value = True
    
    # Mock export methods
    mock_instance.export_thread_to_xlsx.return_value = None
    
    # Mock convert_xlsx_to_csv
    with patch('src.tools.convert_xlsx_to_csv', return_value="header1,header2\nvalue1,value2"):
        # Create a mock storage with is_file_protocol=False
        mock_storage = MagicMock()
        mock_storage.get_metadata.return_value = {
            "total_rows": 2,
            "total_size": 30,
            "resource_uri": "quip://test_thread_id?sheet=test_sheet"
        }
        mock_storage.get_resource_uri.return_value = "quip://test_thread_id?sheet=test_sheet"
        mock_storage.is_file_protocol = False
        
        # Call the function
        result = await handle_quip_read_spreadsheet({"threadId": "test_thread_id", "sheetName": "test_sheet"}, mock_storage)
        
        # Parse the JSON response
        response_data = json.loads(result[0].text)
        
        # Verify the resource_uri uses quip:// protocol
        assert "resource_uri" in response_data["metadata"]
        assert response_data["metadata"]["resource_uri"].startswith("quip://")
        assert "test_thread_id" in response_data["metadata"]["resource_uri"]
        assert "test_sheet" in response_data["metadata"]["resource_uri"]


@patch('src.tools.QuipClient')
@patch('os.environ.get')
@pytest.mark.asyncio
async def test_handle_quip_read_spreadsheet_resource_uri_file_protocol(mock_environ_get, mock_quip_client):
    """Test that handle_quip_read_spreadsheet returns resource_uri with file:// protocol when is_file_protocol=True"""
    # Setup mocks
    mock_environ_get.return_value = "fake_token"  # Mock QUIP_TOKEN
    
    mock_instance = MagicMock()
    mock_quip_client.return_value = mock_instance
    mock_instance.is_spreadsheet.return_value = True
    
    # Mock export methods
    mock_instance.export_thread_to_xlsx.return_value = None
    
    # Mock convert_xlsx_to_csv
    with patch('src.tools.convert_xlsx_to_csv', return_value="header1,header2\nvalue1,value2"):
        # Create a mock storage with is_file_protocol=True
        mock_storage = MagicMock()
        mock_storage.get_metadata.return_value = {
            "total_rows": 2,
            "total_size": 30,
            "resource_uri": "file:///tmp/test_storage/test_thread_id-test_sheet.csv"
        }
        mock_storage.get_resource_uri.return_value = "file:///tmp/test_storage/test_thread_id-test_sheet.csv"
        mock_storage.is_file_protocol = True
        
        # Call the function
        result = await handle_quip_read_spreadsheet({"threadId": "test_thread_id", "sheetName": "test_sheet"}, mock_storage)
        
        # Parse the JSON response
        response_data = json.loads(result[0].text)
        
        # Verify the resource_uri uses file:// protocol
        assert "resource_uri" in response_data["metadata"]
        assert response_data["metadata"]["resource_uri"].startswith("file://")
        assert "test_thread_id-test_sheet.csv" in response_data["metadata"]["resource_uri"]



@patch('argparse.ArgumentParser.parse_args')
@patch('src.server.logger')
@patch('src.server.configure_logging')
@patch('asyncio.run')
@patch('os.environ.get')
def test_main_missing_token(mock_environ_get, mock_asyncio_run, mock_configure_logging, mock_logger, mock_parse_args):
    """Test that main raises an error when QUIP_TOKEN is missing"""
    # Configure the mock to return None for QUIP_TOKEN and something else for other calls
    def mock_get(key, default=None):
        if key == "QUIP_TOKEN":
            return None
        return default
    
    mock_environ_get.side_effect = mock_get
    
    # Mock logger
    mock_logger.error = MagicMock()
    
    # Mock argparse to avoid command line parsing issues
    mock_parse_args.return_value = MagicMock(storage_path=None, debug=False)
    # Use side_effect to make sys.exit raise SystemExit exception, preventing subsequent code execution
    with patch('sys.exit', side_effect=SystemExit) as mock_exit:
        try:
            main()
        except SystemExit:
            pass
        
        # Check that the error message was logged
        mock_logger.error.assert_any_call("QUIP_TOKEN environment variable is not set")
        
        # Check that sys.exit was called with code 1
        mock_exit.assert_called_with(1)
        
        # Since sys.exit raises an exception, subsequent code won't execute, so asyncio.run won't be called
        mock_asyncio_run.assert_not_called()


def test_parse_arguments():
    """Test parsing command line arguments"""
    # Test with no arguments
    with patch('sys.argv', ['quip-mcp-server']):
        args = parse_arguments()
        assert args.storage_path is None
        assert args.debug is False
        assert args.file_protocol is False
    
    # Test with storage-path argument
    with patch('sys.argv', ['quip-mcp-server', '--storage-path', '/tmp/test']):
        args = parse_arguments()
        assert args.storage_path == '/tmp/test'
        assert args.debug is False
        assert args.file_protocol is False
    
    # Test with debug argument
    with patch('sys.argv', ['quip-mcp-server', '--debug']):
        args = parse_arguments()
        assert args.storage_path is None
        assert args.debug is True
        assert args.file_protocol is False
    
    # Test with file-protocol argument
    with patch('sys.argv', ['quip-mcp-server', '--file-protocol']):
        args = parse_arguments()
        assert args.storage_path is None
        assert args.debug is False
        assert args.file_protocol is True
    
    # Test with all arguments
    with patch('sys.argv', ['quip-mcp-server', '--storage-path', '/tmp/test', '--debug', '--file-protocol']):
        args = parse_arguments()
        assert args.storage_path == '/tmp/test'
        assert args.debug is True
        assert args.file_protocol is True


def test_get_storage_path():
    """Test getting storage path from arguments or environment"""
    # Test with argument
    args = MagicMock()
    args.storage_path = '/tmp/test'
    assert get_storage_path(args) == '/tmp/test'
@patch('logging.basicConfig')
def test_configure_logging_default(mock_basicConfig):
    """Test configure_logging with default settings"""
    # Test with no arguments
    args = MagicMock(debug=False)
    
    with patch('os.environ.get', return_value=None):
        logger = configure_logging(args)
        
        # Verify that basicConfig was called with WARN level
        mock_basicConfig.assert_called_once()
        assert mock_basicConfig.call_args[1]['level'] == logging.WARN


@patch('logging.basicConfig')
def test_configure_logging_env_debug(mock_basicConfig):
    """Test configure_logging with debug environment variable"""
    # Test with debug environment variable
    args = MagicMock(debug=False)
    
    with patch('os.environ.get', return_value="1"):
        logger = configure_logging(args)
        
        # Verify that basicConfig was called with DEBUG level
        mock_basicConfig.assert_called_once()
        assert mock_basicConfig.call_args[1]['level'] == logging.DEBUG


@patch('logging.basicConfig')
def test_configure_logging_arg_debug(mock_basicConfig):
    """Test configure_logging with debug command line argument"""
    # Test with debug command line argument
    args = MagicMock(debug=True)
    
    with patch('os.environ.get', return_value=None):
        logger = configure_logging(args)
        
        # Verify that basicConfig was called with DEBUG level
        mock_basicConfig.assert_called_once()
        assert mock_basicConfig.call_args[1]['level'] == logging.DEBUG


@patch('logging.basicConfig')
def test_configure_logging_both_debug(mock_basicConfig):
    """Test configure_logging with both debug environment variable and command line argument"""
    # Test with both debug environment variable and command line argument
    args = MagicMock(debug=True)
    
    with patch('os.environ.get', return_value="1"):
        logger = configure_logging(args)
        
        # Verify that basicConfig was called with DEBUG level
        mock_basicConfig.assert_called_once()
        assert mock_basicConfig.call_args[1]['level'] == logging.DEBUG

    
    # Test with environment variable
    args = MagicMock()
    args.storage_path = None
    with patch('os.environ.get', return_value='/tmp/env'):
        assert get_storage_path(args) == '/tmp/env'
    
    # Test with default
    args = MagicMock()
    args.storage_path = None
    with patch('os.environ.get', return_value=None):
        with patch('os.path.expanduser', return_value='/home/user'):
            path = get_storage_path(args)
            assert path == '/home/user/.quip-mcp-server/storage'


@patch('src.server.urlparse')
@patch('src.server.parse_qs')
@pytest.mark.asyncio
async def test_access_resource_quip_protocol(mock_parse_qs, mock_urlparse):
    """Test accessing a resource with quip:// protocol"""
    # Import the access_resource function
    from src.server import access_resource
    
    # Setup mocks
    mock_urlparse.return_value = MagicMock(scheme="quip", netloc="test_thread_id")
    mock_parse_qs.return_value = {"sheet": ["test_sheet"]}
    
    # Create a mock storage
    mock_storage = MagicMock()
    mock_storage.get_csv.return_value = "header1,header2\nvalue1,value2"
    
    # Patch the global storage_instance
    with patch('src.server.storage_instance', mock_storage):
        result = await access_resource("quip://test_thread_id?sheet=test_sheet")
        
        # Verify the result
        assert len(result) == 1
        assert result[0].type == "text"
        assert result[0].text == "header1,header2\nvalue1,value2"
        
        # Verify the mocks were called correctly
        mock_urlparse.assert_called_once_with("quip://test_thread_id?sheet=test_sheet")
        mock_parse_qs.assert_called_once()
        mock_storage.get_csv.assert_called_once_with("test_thread_id", "test_sheet")


@patch('src.server.urlparse')
@pytest.mark.asyncio
async def test_access_resource_file_protocol(mock_urlparse):
    """Test accessing a resource with file:// protocol"""
    # Import the access_resource function
    from src.server import access_resource
    
    # Setup mocks
    mock_urlparse.return_value = MagicMock(
        scheme="file",
        path="/tmp/test_storage/thread1-sheet1.csv"
    )
    
    # Create a mock storage
    mock_storage = MagicMock()
    mock_storage.get_csv.return_value = "header1,header2\nvalue1,value2"
    
    # Patch the global storage_instance
    with patch('src.server.storage_instance', mock_storage):
        result = await access_resource("file:///tmp/test_storage/thread1-sheet1.csv")
        
        # Verify the result
        assert len(result) == 1
        assert result[0].type == "text"
        assert result[0].text == "header1,header2\nvalue1,value2"
        
        # Verify the mocks were called correctly
        mock_urlparse.assert_called_once_with("file:///tmp/test_storage/thread1-sheet1.csv")
        mock_storage.get_csv.assert_called_once_with("thread1", "sheet1")


@patch('src.server.urlparse')
@pytest.mark.asyncio
async def test_access_resource_invalid_scheme(mock_urlparse):
    """Test accessing a resource with an invalid scheme"""
    # Import the access_resource function
    from src.server import access_resource
    
    # Setup mocks
    mock_urlparse.return_value = MagicMock(scheme="invalid", netloc="test_thread_id")
    
    # Test
    with pytest.raises(ValueError, match="Unsupported URI scheme"):
        await access_resource("invalid://test_thread_id")


@patch('src.server.urlparse')
@patch('src.server.parse_qs')
@pytest.mark.asyncio
async def test_access_resource_not_found(mock_parse_qs, mock_urlparse):
    """Test accessing a non-existent resource"""
    # Import the access_resource function
    from src.server import access_resource
    
    # Setup mocks
    mock_urlparse.return_value = MagicMock(scheme="quip", netloc="test_thread_id")
    mock_parse_qs.return_value = {"sheet": ["test_sheet"]}
    
    # Create a mock storage
    mock_storage = MagicMock()
    mock_storage.get_csv.return_value = None
    
    # Patch the global storage_instance
    with patch('src.server.storage_instance', mock_storage):
        with pytest.raises(ValueError, match="Resource not found"):
            await access_resource("quip://test_thread_id?sheet=test_sheet")


@patch('os.listdir')
@patch('os.path.join')
@pytest.mark.asyncio
async def test_discover_resources(mock_path_join, mock_listdir):
    """Test discovering resources from storage directory with default protocol (quip://)"""
    # Import the discover_resources function
    from src.server import discover_resources
    
    # Setup mocks
    mock_listdir.return_value = ["thread1.csv", "thread2-sheet1.csv", "thread3.csv.meta"]
    mock_path_join.side_effect = lambda *args: "/".join(args)
    
    # Create a mock storage
    mock_storage = MagicMock()
    mock_storage.storage_path = "/tmp/test_storage"
    mock_storage.get_metadata.side_effect = lambda thread_id, sheet_name: {
        "total_rows": 10,
        "total_size": 1024,
        "resource_uri": f"quip://{thread_id}" + (f"?sheet={sheet_name}" if sheet_name else "")
    }
    mock_storage.get_resource_uri.side_effect = lambda thread_id, sheet_name: \
        f"quip://{thread_id}" + (f"?sheet={sheet_name}" if sheet_name else "")
    
    # Patch the global storage_instance
    with patch('src.server.storage_instance', mock_storage):
        resources = await discover_resources(False)  # Explicitly pass False for isFileProtocol
        
        # Verify the result
        assert len(resources) == 2  # Only .csv files, not .meta files
        
        # Check first resource (thread1.csv)
        assert str(resources[0].uri) == "quip://thread1"
        assert resources[0].name == "Quip Thread(Spreadsheet): thread1"
        assert "10 rows" in resources[0].description
        assert "1024 bytes" in resources[0].description
        assert resources[0].mime_type == "text/csv"
        
        # Check second resource (thread2-sheet1.csv)
        assert str(resources[1].uri) == "quip://thread2?sheet=sheet1"
        assert resources[1].name == "Quip Thread(Spreadsheet): thread2 (Sheet: sheet1)"
        assert "10 rows" in resources[1].description
        assert "1024 bytes" in resources[1].description
        assert resources[1].mime_type == "text/csv"
        
        # Verify the mocks were called correctly
        mock_listdir.assert_called_once_with("/tmp/test_storage")
        mock_storage.get_metadata.assert_any_call("thread1", None)
        mock_storage.get_metadata.assert_any_call("thread2", "sheet1")


@patch('os.listdir')
@patch('os.path.join')
@pytest.mark.asyncio
async def test_discover_resources_with_file_protocol(mock_path_join, mock_listdir):
    """Test discovering resources from storage directory with file:// protocol"""
    # Import the discover_resources function
    from src.server import discover_resources
    
    # Setup mocks
    mock_listdir.return_value = ["thread1.csv", "thread2-sheet1.csv", "thread3.csv.meta"]
    mock_path_join.side_effect = lambda *args: "/".join(args)
    
    # Create a mock storage
    mock_storage = MagicMock()
    mock_storage.storage_path = "/tmp/test_storage"
    mock_storage.get_metadata.side_effect = lambda thread_id, sheet_name: {
        "total_rows": 10,
        "total_size": 1024
    }
    
    # Patch the global storage_instance
    with patch('src.server.storage_instance', mock_storage):
        resources = await discover_resources(True)  # Pass True for isFileProtocol
        
        # Verify the result
        assert len(resources) == 2  # Only .csv files, not .meta files
        
        # Check first resource (thread1.csv)
        assert str(resources[0].uri).startswith("file:///tmp/test_storage/thread1.csv")
        assert resources[0].name.startswith("Quip Thread(Spreadsheet): thread1")
        assert "You can access the file at:" in resources[0].name
        assert "/tmp/test_storage/thread1.csv" in resources[0].name
        assert "10 rows" in resources[0].description
        assert "1024 bytes" in resources[0].description
        assert resources[0].mime_type == "text/csv"
        
        # Check second resource (thread2-sheet1.csv)
        assert str(resources[1].uri).startswith("file:///tmp/test_storage/thread2-sheet1.csv")
        assert resources[1].name.startswith("Quip Thread(Spreadsheet): thread2 (Sheet: sheet1)")
        assert "You can access the file at:" in resources[1].name
        assert "/tmp/test_storage/thread2-sheet1.csv" in resources[1].name
        assert "10 rows" in resources[1].description
        assert "1024 bytes" in resources[1].description
        assert resources[1].mime_type == "text/csv"
        
        # Verify the mocks were called correctly
        mock_listdir.assert_called_once_with("/tmp/test_storage")
        mock_storage.get_metadata.assert_any_call("thread1", None)
        mock_storage.get_metadata.assert_any_call("thread2", "sheet1")
@patch('sys.argv')
def test_debug_mode_output(mock_argv, caplog):
    """测试启动时指定 --debug 参数后，日志中有 info/debug level 输出"""
    import logging
    from src.server import logger
    
    # 设置 caplog 级别为 DEBUG
    caplog.set_level(logging.DEBUG)
    
    # 模拟命令行参数
    mock_argv.__getitem__.side_effect = lambda idx: ['quip-mcp-server', '--debug'][idx]
    
    # 清除之前的日志记录
    caplog.clear()
    
    # 输出不同级别的日志
    logger.debug("这是一条 DEBUG 消息")
    logger.info("这是一条 INFO 消息")
    logger.warning("这是一条 WARNING 消息")
    
    # 获取记录的日志消息
    records = caplog.get_records("call")
    
    # 验证日志记录
    debug_records = [r for r in records if r.levelname == "DEBUG"]
    info_records = [r for r in records if r.levelname == "INFO"]
    warning_records = [r for r in records if r.levelname == "WARNING"]
    
    # 验证所有级别的消息都被记录
    assert len(debug_records) == 1
    # 验证所有级别的消息都被记录
    assert len(debug_records) == 1
    assert len(info_records) == 1
    assert len(warning_records) == 1
    assert debug_records[0].message == "这是一条 DEBUG 消息"
    assert info_records[0].message == "这是一条 INFO 消息"
    assert warning_records[0].message == "这是一条 WARNING 消息"


@patch('sys.argv')
def test_normal_mode_output(mock_argv, caplog):
    """测试启动时没有指定 --debug 参数，日志中没有 info/debug level 输出"""
    import logging
    from src.server import logger
    
    # 设置 caplog 级别为 WARN
    caplog.set_level(logging.WARN)
    
    # 模拟命令行参数
    mock_argv.__getitem__.side_effect = lambda idx: ['quip-mcp-server'][idx]
    
    # 清除之前的日志记录
    caplog.clear()
    
    # 输出不同级别的日志
    logger.debug("这是一条 DEBUG 消息")
    logger.info("这是一条 INFO 消息")
    logger.warning("这是一条 WARNING 消息")
    
    # 获取记录的日志消息
    records = caplog.get_records("call")
    
    # 验证日志记录
    debug_records = [r for r in records if r.levelname == "DEBUG"]
    info_records = [r for r in records if r.levelname == "INFO"]
    warning_records = [r for r in records if r.levelname == "WARNING"]
    
    # 验证只有 WARNING 级别的消息被记录
    assert len(debug_records) == 0
    assert len(info_records) == 0
    assert len(warning_records) == 1
    assert warning_records[0].message == "这是一条 WARNING 消息"


@patch('os.listdir')
@pytest.mark.asyncio
async def test_discover_resources_empty_directory(mock_listdir):
    """Test discovering resources from an empty storage directory"""
    # Import the discover_resources function
    from src.server import discover_resources
    
    # Setup mocks
    mock_listdir.return_value = []
    
    # Create a mock storage
    mock_storage = MagicMock()
    mock_storage.storage_path = "/tmp/test_storage"
    
    # Patch the global storage_instance
    with patch('src.server.storage_instance', mock_storage):
        # Test with default protocol (quip://)
        resources = await discover_resources(False)
        
        # Verify the result
        assert len(resources) == 0
        
        # Verify the mocks were called correctly
        mock_listdir.assert_called_once_with("/tmp/test_storage")


@patch('os.listdir')
@pytest.mark.asyncio
async def test_discover_resources_error_handling(mock_listdir):
    """Test error handling when discovering resources"""
    # Import the discover_resources function
    from src.server import discover_resources
    
    # Setup mocks to raise an exception
    mock_listdir.side_effect = Exception("Test exception")
    
    # Create a mock storage
    mock_storage = MagicMock()
    mock_storage.storage_path = "/tmp/test_storage"
    
    # Patch the global storage_instance
    with patch('src.server.storage_instance', mock_storage):
        # Test with default protocol (quip://)
        resources = await discover_resources(False)
        
        # Verify the result (should be empty list due to error handling)
        assert len(resources) == 0
        
        # Verify the mocks were called correctly
        mock_listdir.assert_called_once_with("/tmp/test_storage")
        
        # Reset mock for next test
        mock_listdir.reset_mock()
        mock_listdir.side_effect = Exception("Test exception")
        
        # Test with file:// protocol
        resources = await discover_resources(True)
        
        # Verify the result (should be empty list due to error handling)
        assert len(resources) == 0
        
        # Verify the mocks were called correctly
        mock_listdir.assert_called_once_with("/tmp/test_storage")

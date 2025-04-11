#!/usr/bin/env python3
"""
Tests for the storage module.
"""
import os
import sys
import tempfile
import pytest
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.storage import StorageInterface, LocalStorage, create_storage, truncate_csv_content


def test_create_storage_local():
    """Test creating a local storage instance"""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = create_storage(storage_type="local", storage_path=temp_dir)
        assert isinstance(storage, LocalStorage)
        assert storage.storage_path == temp_dir


def test_create_storage_invalid_type():
    """Test creating a storage instance with an invalid type"""
    with pytest.raises(ValueError, match="Unsupported storage type"):
        create_storage(storage_type="invalid")


def test_create_storage_missing_path():
    """Test creating a local storage instance without a path"""
    with pytest.raises(ValueError, match="storage_path is required"):
        create_storage(storage_type="local")


def test_local_storage_save_and_get_csv():
    """Test saving and retrieving CSV content with local storage"""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalStorage(temp_dir, is_file_protocol=False)
        
        # Test data
        thread_id = "test_thread_id"
        sheet_name = "test_sheet"
        csv_content = "header1,header2\nvalue1,value2\nvalue3,value4"
        
        # Save CSV content
        file_path = storage.save_csv(thread_id, sheet_name, csv_content)
        assert os.path.exists(file_path)
        
        # Get CSV content
        retrieved_content = storage.get_csv(thread_id, sheet_name)
        assert retrieved_content == csv_content
        
        # Check metadata file
        metadata_path = file_path + ".meta"
        assert os.path.exists(metadata_path)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata["total_rows"] == 3  # Header + 2 data rows
        assert metadata["total_size"] == len(csv_content)
        assert metadata["resource_uri"] == f"quip://{thread_id}?sheet={sheet_name}"


def test_local_storage_get_nonexistent_csv():
    """Test retrieving non-existent CSV content"""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalStorage(temp_dir, is_file_protocol=False)
        
        # Test data
        thread_id = "nonexistent_thread_id"
        sheet_name = "nonexistent_sheet"
        
        # Get non-existent CSV content
        retrieved_content = storage.get_csv(thread_id, sheet_name)
        assert retrieved_content is None


def test_local_storage_get_resource_uri():
    """Test getting resource URI"""
    storage = LocalStorage("/tmp", is_file_protocol=False)
    
    # Test with sheet name
    thread_id = "test_thread_id"
    sheet_name = "test sheet with spaces"
    uri = storage.get_resource_uri(thread_id, sheet_name)
    assert uri == f"quip://{thread_id}?sheet=test%20sheet%20with%20spaces"
    
    # Test without sheet name
    uri = storage.get_resource_uri(thread_id)
    assert uri == f"quip://{thread_id}"


def test_local_storage_get_metadata():
    """Test getting metadata"""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalStorage(temp_dir, is_file_protocol=False)
        
        # Test data
        thread_id = "test_thread_id"
        sheet_name = "test_sheet"
        csv_content = "header1,header2\nvalue1,value2\nvalue3,value4"
        
        # Save CSV content
        storage.save_csv(thread_id, sheet_name, csv_content)
        
        # Get metadata
        metadata = storage.get_metadata(thread_id, sheet_name)
        assert metadata["total_rows"] == 3  # Header + 2 data rows
        assert metadata["total_size"] == len(csv_content)
        assert metadata["resource_uri"] == f"quip://{thread_id}?sheet={sheet_name}"


def test_local_storage_get_nonexistent_metadata():
    """Test getting metadata for non-existent CSV"""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalStorage(temp_dir, is_file_protocol=False)
        
        # Test data
        thread_id = "nonexistent_thread_id"
        sheet_name = "nonexistent_sheet"
        
        # Get metadata for non-existent CSV
        metadata = storage.get_metadata(thread_id, sheet_name)
        assert metadata["total_rows"] == 0
        assert metadata["total_size"] == 0
        assert metadata["resource_uri"] == f"quip://{thread_id}?sheet={sheet_name}"


def test_truncate_csv_content_small():
    """Test truncating small CSV content (no truncation needed)"""
    csv_content = "header1,header2\nvalue1,value2\nvalue3,value4"
    max_size = 1024  # 1KB
    
    truncated, is_truncated = truncate_csv_content(csv_content, max_size)
    assert truncated == csv_content
    assert is_truncated is False


def test_truncate_csv_content_large():
    """Test truncating large CSV content"""
    # Create a large CSV content
    header = "col1,col2,col3,col4,col5"
    data_row = "data1,data2,data3,data4,data5"
    
    # Create 1000 rows (should be well over 10KB)
    rows = [header] + [data_row] * 1000
    csv_content = "\n".join(rows)
    
    max_size = 1024  # 1KB
    
    truncated, is_truncated = truncate_csv_content(csv_content, max_size)
    assert len(truncated) <= max_size
    assert is_truncated is True
    assert truncated.startswith(header)  # Header should be preserved
    assert truncated.count("\n") < 1000  # Should have fewer rows than original
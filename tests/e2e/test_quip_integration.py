import os
import tempfile
import pytest
import csv
import io
import json
from src.quip_client import convert_xlsx_to_csv
from src.storage import LocalStorage, truncate_csv_content

@pytest.mark.e2e
def test_connection(quip_client, test_thread_id):
    """Test connection to Quip API"""
    thread = quip_client.get_thread(test_thread_id)
    assert thread is not None
    assert "thread" in thread
    print(thread["thread"])
    assert thread["thread"]["id"] == test_thread_id or \
      ("secret_path" in thread["thread"] and thread["thread"]["secret_path"] == test_thread_id) or \
      test_thread_id in thread["thread"]["link"]

@pytest.mark.e2e
def test_is_spreadsheet(quip_client, test_thread_id):
    """Test if the thread is correctly identified as a spreadsheet"""
    is_spreadsheet = quip_client.is_spreadsheet(test_thread_id)
    assert is_spreadsheet is True

@pytest.mark.e2e
def test_export_to_xlsx(quip_client, test_thread_id):
    """Test exporting to XLSX format"""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        xlsx_path = temp_file.name
    
    try:
        # Export to XLSX
        quip_client.export_thread_to_xlsx(test_thread_id, xlsx_path)
        assert os.path.exists(xlsx_path)
        assert os.path.getsize(xlsx_path) > 0
    finally:
        # Clean up temporary file
        if os.path.exists(xlsx_path):
            os.remove(xlsx_path)

@pytest.mark.e2e
def test_convert_xlsx_to_csv(quip_client, test_thread_id, test_sheet_name):
    """Test converting XLSX to CSV and validate content"""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        xlsx_path = temp_file.name
    
    try:
        # Export to XLSX
        quip_client.export_thread_to_xlsx(test_thread_id, xlsx_path)
        
        # Convert to CSV
        csv_data = convert_xlsx_to_csv(xlsx_path, test_sheet_name)
        
        # Validate CSV data
        assert csv_data is not None
        assert len(csv_data) > 0
        
        # Parse CSV data for more detailed validation
        csv_reader = csv.reader(io.StringIO(csv_data))
        rows = list(csv_reader)
        assert len(rows) > 0  # At least one row of data
        
        # You can add more specific validations for your data
    finally:
        # Clean up temporary file
        if os.path.exists(xlsx_path):
            os.remove(xlsx_path)

@pytest.mark.e2e
def test_export_to_csv_fallback(quip_client, test_thread_id, test_sheet_name):
    """Test exporting to CSV format using fallback method"""
    csv_data = quip_client.export_thread_to_csv_fallback(test_thread_id, test_sheet_name)
    assert csv_data is not None
    assert len(csv_data) > 0
    
    # Parse CSV data for more detailed validation
    csv_reader = csv.reader(io.StringIO(csv_data))
    rows = list(csv_reader)
    assert len(rows) > 0  # At least one row of data

@pytest.mark.e2e
def test_error_handling_invalid_thread(quip_client):
    """Test handling of invalid threadId"""
    invalid_thread_id = "invalid_thread_id_123456"
    
    # Test is_spreadsheet method
    is_spreadsheet = quip_client.is_spreadsheet(invalid_thread_id)
    assert is_spreadsheet is False
    
    # Test export_thread_to_xlsx method
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as temp_file:
        with pytest.raises(Exception):
            quip_client.export_thread_to_xlsx(invalid_thread_id, temp_file.name)
    
    # Test export_thread_to_csv_fallback method
    with pytest.raises(Exception):
        quip_client.export_thread_to_csv_fallback(invalid_thread_id)


@pytest.mark.e2e
def test_storage_integration(quip_client, test_thread_id, test_sheet_name, storage):
    """Test integration with storage"""
    # Export to XLSX and convert to CSV
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        xlsx_path = temp_file.name
    
    try:
        # Export to XLSX
        quip_client.export_thread_to_xlsx(test_thread_id, xlsx_path)
        
        # Convert to CSV
        csv_data = convert_xlsx_to_csv(xlsx_path, test_sheet_name)
        
        # Save to storage
        storage.save_csv(test_thread_id, test_sheet_name, csv_data)
        
        # Retrieve from storage
        retrieved_csv = storage.get_csv(test_thread_id, test_sheet_name)
        
        # Normalize line endings for comparison
        normalized_csv_data = csv_data.replace('\r\n', '\n')
        normalized_retrieved_csv = retrieved_csv.replace('\r\n', '\n')
        
        assert normalized_retrieved_csv == normalized_csv_data
        
        # Get metadata
        metadata = storage.get_metadata(test_thread_id, test_sheet_name)
        assert metadata["total_rows"] > 0
        assert metadata["total_size"] > 0
        assert metadata["resource_uri"] == f"quip://{test_thread_id}?sheet={test_sheet_name}"
    finally:
        # Clean up temporary file
        if os.path.exists(xlsx_path):
            os.remove(xlsx_path)



@pytest.mark.e2e
def test_large_spreadsheet_truncation(quip_client, test_thread_id, test_large_sheet_name, storage):
    """Test handling of large spreadsheets with truncation"""
    # This test assumes that the test spreadsheet is large enough to trigger truncation
    # If not, it will still test the functionality but won't actually truncate
    
    # Export to XLSX and convert to CSV
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        xlsx_path = temp_file.name
    try:
        # Export to XLSX
        quip_client.export_thread_to_xlsx(test_thread_id, xlsx_path)
        
        # Convert to CSV
        csv_data = convert_xlsx_to_csv(xlsx_path, test_large_sheet_name)
        
        # Save to storage
        storage.save_csv(test_thread_id, test_large_sheet_name, csv_data)
        
        # Truncate CSV content
        MAX_SIZE = 10 * 1024  # 10KB
        truncated_csv, is_truncated = truncate_csv_content(csv_data, MAX_SIZE)
        
        # Create response with CSV content and metadata
        metadata = storage.get_metadata(test_thread_id, test_large_sheet_name)
        metadata["is_truncated"] = is_truncated
        
        response_data = {
            "csv_content": truncated_csv,
            "metadata": metadata
        }
        
        # Verify response structure
        assert "csv_content" in response_data
        assert "metadata" in response_data
        assert "total_rows" in response_data["metadata"]
        assert "total_size" in response_data["metadata"]
        assert "is_truncated" in response_data["metadata"]
        assert "resource_uri" in response_data["metadata"]
        
        # Verify content
        if is_truncated:
            assert len(response_data["csv_content"]) <= MAX_SIZE
            assert response_data["metadata"]["is_truncated"] is True
        else:
            assert response_data["csv_content"] == csv_data
            assert response_data["metadata"]["is_truncated"] is False
    finally:
        # Clean up temporary file
        if os.path.exists(xlsx_path):
            os.remove(xlsx_path)


@pytest.mark.e2e
def test_resource_discovery(quip_client, test_thread_id, test_sheet_name, storage):
    """Test resource discovery functionality"""
    # First, export a spreadsheet and save it to storage
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        xlsx_path = temp_file.name
    
    try:
        # Export to XLSX
        quip_client.export_thread_to_xlsx(test_thread_id, xlsx_path)
        
        # Convert to CSV
        csv_data = convert_xlsx_to_csv(xlsx_path, test_sheet_name)
        
        # Save to storage
        storage.save_csv(test_thread_id, test_sheet_name, csv_data)
        
        # Import the discover_resources function
        from src.server import discover_resources
        import asyncio
        
        # Patch the global storage_instance
        import src.server
        original_storage = src.server.storage_instance
        src.server.storage_instance = storage
        
        try:
            # Call discover_resources
            resources = asyncio.run(discover_resources(isFileProtocol=False))
            
            # Verify resources were discovered
            assert len(resources) > 0
            
            # Find our test resource
            test_resource = None
            for resource in resources:
                if str(resource.uri) == f"quip://{test_thread_id}?sheet={test_sheet_name}":
                    test_resource = resource
                    break
            
            # Verify the test resource was found
            assert test_resource is not None
            assert test_resource.name == f"Quip Thread(Spreadsheet): {test_thread_id} (Sheet: {test_sheet_name})"
            assert "rows" in test_resource.description
            assert "bytes" in test_resource.description
            assert test_resource.mime_type == "text/csv"
            
        finally:
            # Restore the original storage_instance
            src.server.storage_instance = original_storage
    finally:
        # Clean up temporary file
        if os.path.exists(xlsx_path):
            os.remove(xlsx_path)
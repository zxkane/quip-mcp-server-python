import os
import tempfile
import pytest
import csv
import io
from src.quip_client import convert_xlsx_to_csv

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
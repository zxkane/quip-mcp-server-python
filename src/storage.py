import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from urllib.parse import quote

# Initialize logger
logger = logging.getLogger("quip-mcp-server")

class StorageInterface(ABC):
    """
    Abstract base class for storage interface, defining standard methods for storage operations
    """
    @abstractmethod
    def save_csv(self, thread_id: str, sheet_name: Optional[str], csv_content: str) -> str:
        """
        Save CSV content
        
        Args:
            thread_id: Quip document thread ID
            sheet_name: Sheet name (optional)
            csv_content: CSV content
            
        Returns:
            str: Resource identifier (such as file path or object URL)
        """
        pass
    
    @abstractmethod
    def get_csv(self, thread_id: str, sheet_name: Optional[str] = None) -> Optional[str]:
        """
        Get CSV content
        
        Args:
            thread_id: Quip document thread ID
            sheet_name: Sheet name (optional)
            
        Returns:
            Optional[str]: CSV content, or None if it doesn't exist
        """
        pass
    
    @abstractmethod
    def get_resource_uri(self, thread_id: str, sheet_name: Optional[str] = None) -> str:
        """
        Get resource URI
        
        Args:
            thread_id: Quip document thread ID
            sheet_name: Sheet name (optional)
            
        Returns:
            str: Resource URI
        """
        pass
    
    @abstractmethod
    def get_metadata(self, thread_id: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata for the stored CSV
        
        Args:
            thread_id: Quip document thread ID
            sheet_name: Sheet name (optional)
            
        Returns:
            Dict[str, Any]: Metadata including total_rows, total_size, etc.
        """
        pass


class LocalStorage(StorageInterface):
    """
    Local file system storage implementation
    """
    def __init__(self, storage_path: str, is_file_protocol: bool):
        """
        Initialize local storage
        
        Args:
            storage_path: Storage path
        """
        self.storage_path = storage_path
        self.is_file_protocol = is_file_protocol
        os.makedirs(storage_path, exist_ok=True)
        logger.info(f"LocalStorage initialized with path: {storage_path}, is_file_protocol: {is_file_protocol}")
    
    def get_file_path(self, thread_id: str, sheet_name: Optional[str] = None) -> str:
        """
        Get file path
        
        Args:
            thread_id: Quip document thread ID
            sheet_name: Sheet name (optional)
            
        Returns:
            str: File path
        """
        file_name = f"{thread_id}"
        if sheet_name:
            # Replace invalid filename characters
            safe_sheet_name = sheet_name.replace('/', '_').replace('\\', '_')
            file_name += f"-{safe_sheet_name}"
        file_name += ".csv"
        return os.path.join(self.storage_path, file_name)
    
    def save_csv(self, thread_id: str, sheet_name: Optional[str], csv_content: str) -> str:
        """
        Save CSV content to local file
        
        Args:
            thread_id: Quip document thread ID
            sheet_name: Sheet name (optional)
            csv_content: CSV content
            
        Returns:
            str: File path
        """
        file_path = self.get_file_path(thread_id, sheet_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Calculate and save metadata
        metadata = {
            "total_rows": len(csv_content.splitlines()),
            "total_size": len(csv_content),
            "resource_uri": self.get_resource_uri(thread_id, sheet_name)
        }
        
        # Save metadata to a separate file
        metadata_path = file_path + ".meta"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f)
        
        logger.info(f"Saved CSV to {file_path} ({metadata['total_size']} bytes, {metadata['total_rows']} rows)")
        return file_path
    
    def get_csv(self, thread_id: str, sheet_name: Optional[str] = None) -> Optional[str]:
        """
        Get CSV content from local file
        
        Args:
            thread_id: Quip document thread ID
            sheet_name: Sheet name (optional)
            
        Returns:
            Optional[str]: CSV content, or None if file doesn't exist
        """
        file_path = self.get_file_path(thread_id, sheet_name)
        if not os.path.exists(file_path):
            logger.warning(f"CSV file not found: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Retrieved CSV from {file_path} ({len(content)} bytes)")
        return content
    
    def get_resource_uri(self, thread_id: str, sheet_name: Optional[str] = None) -> str:
        """
        Get resource URI
        
        Args:
            thread_id: Quip document thread ID
            sheet_name: Sheet name (optional)
            
        Returns:
            str: Resource URI
        """
        if self.is_file_protocol:
            return f"file://{self.get_file_path(thread_id, sheet_name)}"
        if sheet_name:
            return f"quip://{thread_id}?sheet={quote(sheet_name)}"
        return f"quip://{thread_id}"
    
    def get_metadata(self, thread_id: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metadata for the stored CSV
        
        Args:
            thread_id: Quip document thread ID
            sheet_name: Sheet name (optional)
            
        Returns:
            Dict[str, Any]: Metadata including total_rows, total_size, etc.
        """
        file_path = self.get_file_path(thread_id, sheet_name)
        metadata_path = file_path + ".meta"
        
        if not os.path.exists(metadata_path):
            logger.warning(f"Metadata file not found: {metadata_path}")
            # If metadata file doesn't exist but CSV file does, generate metadata
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metadata = {
                    "total_rows": len(content.splitlines()),
                    "total_size": len(content),
                    "resource_uri": self.get_resource_uri(thread_id, sheet_name)
                }
                
                # Save the generated metadata
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f)
                
                return metadata
            
            # If neither file exists, return empty metadata
            return {
                "total_rows": 0,
                "total_size": 0,
                "resource_uri": self.get_resource_uri(thread_id, sheet_name)
            }
        
        # Read metadata from file
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return metadata


def create_storage(storage_type: str = "local", **kwargs) -> StorageInterface:
    """
    Factory function to create storage instance
    
    Args:
        storage_type: Storage type, currently supports "local"
        **kwargs: Parameters passed to storage constructor
        
    Returns:
        StorageInterface: Storage instance
        
    Raises:
        ValueError: If storage type is not supported
    """
    if storage_type == "local":
        storage_path = kwargs.get("storage_path")
        if not storage_path:
            raise ValueError("storage_path is required for local storage")
        return LocalStorage(storage_path, kwargs.get("is_file_protocol", False))
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


def truncate_csv_content(csv_content: str, max_size: int = 10 * 1024) -> tuple[str, bool]:
    """
    Truncate CSV content to be under the specified maximum size
    
    Args:
        csv_content: Original CSV content
        max_size: Maximum size in bytes (default: 10KB)
        
    Returns:
        tuple[str, bool]: Truncated CSV content and a boolean indicating if truncation occurred
    """
    if len(csv_content) <= max_size:
        return csv_content, False
    
    lines = csv_content.splitlines()
    header = lines[0] if lines else ""
    
    # Always include the header
    result = [header]
    current_size = len(header) + 1  # +1 for newline
    
    # Add as many data rows as possible without exceeding max_size
    for i in range(1, len(lines)):
        line_size = len(lines[i]) + 1  # +1 for newline
        if current_size + line_size > max_size:
            break
        
        result.append(lines[i])
        current_size += line_size
    
    truncated_content = "\n".join(result)
    logger.info(f"Truncated CSV from {len(csv_content)} bytes to {len(truncated_content)} bytes")
    return truncated_content, True
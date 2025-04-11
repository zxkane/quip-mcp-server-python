import os
import pytest
import tempfile
from dotenv import load_dotenv
from src.quip_client import QuipClient
from src.storage import LocalStorage
@pytest.fixture(scope="session", autouse=True)
def load_env():
    """
    Load test environment variables
    
    Priority:
    1. System environment variables
    2. Variables from .env.local file (if exists)
    
    This supports both local development and CI/CD environments
    """
    # Try to load .env.local file if it exists
    local_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.local')
    if os.path.exists(local_env):
        load_dotenv(local_env)
        print(f"Loaded environment variables from {local_env}")
    
    # Check required environment variables (either from .env.local or system)
    if not os.environ.get("QUIP_TOKEN"):
        pytest.skip("QUIP_TOKEN environment variable is not set, skipping e2e tests")
    if not os.environ.get("TEST_THREAD_ID"):
        pytest.skip("TEST_THREAD_ID environment variable is not set, skipping e2e tests")
        pytest.skip("TEST_THREAD_ID环境变量未设置，跳过e2e测试")

@pytest.fixture
def quip_client():
    """Create a QuipClient instance"""
    token = os.environ.get("QUIP_TOKEN")
    base_url = os.environ.get("QUIP_BASE_URL", "https://platform.quip.com")
    return QuipClient(access_token=token, base_url=base_url)

@pytest.fixture
def test_thread_id():
    """Get the test thread ID"""
    return os.environ.get("TEST_THREAD_ID")

@pytest.fixture
def test_sheet_name():
    """Get the test sheet name"""
    return os.environ.get("TEST_SHEET_NAME")

@pytest.fixture
def test_large_sheet_name():
    """Get the test large sheet name"""
    return os.environ.get("TEST_LARGE_SHEET_NAME")

@pytest.fixture
def temp_storage_path():
    """
    Create a temporary directory for storage during tests
    
    Returns:
        str: Path to the temporary directory
    """
    with tempfile.TemporaryDirectory(prefix="quip_mcp_test_") as temp_dir:
        yield temp_dir
        # Directory will be automatically cleaned up after the test

@pytest.fixture
def storage(temp_storage_path):
    """
    Create a LocalStorage instance with a temporary directory
    
    Args:
        temp_storage_path: Temporary directory path from fixture
        
    Returns:
        LocalStorage: Storage instance for testing
    """
    return LocalStorage(temp_storage_path, is_file_protocol=False)
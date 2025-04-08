import os
import pytest
from dotenv import load_dotenv
from src.quip_client import QuipClient
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
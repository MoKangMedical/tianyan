import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    with TestClient(app) as test_client:
        yield test_client

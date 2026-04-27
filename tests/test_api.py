import pytest
from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """测试健康检查接口"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_root_endpoint(client: TestClient):
    """测试根路径接口"""
    response = client.get("/")
    assert response.status_code == 200

from conftest import SyncASGIClient

def test_health_check(client: SyncASGIClient):
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_root_endpoint(client: SyncASGIClient):
    """测试根路径接口"""
    response = client.get("/")
    assert response.status_code == 200

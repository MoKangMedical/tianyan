"""天眼Demo Server API测试。"""

import pytest
from fastapi.testclient import TestClient
from demo_server import app

client = TestClient(app)


class TestHealthAndInfo:
    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "healthy"
        assert d["version"] == "1.0.0"

    def test_dashboard(self):
        r = client.get("/api/v1/dashboard")
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["platform"] == "天眼 Tianyan"
        assert d["total_endpoints"] >= 14

    def test_templates(self):
        r = client.get("/api/v1/templates")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] >= 5
        names = [t["name"] for t in d["templates"]]
        assert any("GLP" in n for n in names)

    def test_landing_page(self):
        r = client.get("/")
        assert r.status_code == 200
        assert "天眼" in r.text


class TestPopulation:
    def test_create_population(self):
        r = client.post("/api/population", json={
            "size": 50,
            "region": "一线城市",
            "age_min": 25,
            "age_max": 35,
            "gender": "female",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["summary"]["size"] == 50


class TestSimulation:
    def test_simulate(self):
        r = client.post("/api/simulate", json={
            "scenario_description": "一款新手机上市",
            "population_size": 30,
            "rounds": 1,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert 0 <= d["purchase_intent"] <= 1


class TestKOL:
    def test_kol_prediction(self):
        r = client.post("/api/kol", json={
            "product_name": "测试产品",
            "product_price": 199,
            "kol_type": "头部美妆博主",
            "population_size": 50,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["predicted_reach"] > 0
        assert d["best_platform"] in ["抖音", "小红书", "B站", "微信视频号"]


class TestLivestream:
    def test_livestream(self):
        r = client.post("/api/livestream", json={
            "product_name": "测试产品",
            "product_price": 199,
            "platform": "抖音",
            "discount_rate": 0.2,
            "population_size": 50,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["predicted_gmv"] > 0


class TestChannel:
    def test_channel_optimization(self):
        r = client.post("/api/channel", json={
            "product_name": "测试产品",
            "product_price": 199,
            "product_category": "美妆",
            "population_size": 50,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "best_platform" in d


class TestSeeding:
    def test_seeding(self):
        r = client.post("/api/seeding", json={
            "product_name": "测试产品",
            "product_price": 199,
            "content_style": "种草笔记",
            "num_notes": 50,
            "population_size": 50,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["predicted_impressions"] > 0


class TestFullPrediction:
    def test_full_prediction(self):
        r = client.post("/api/v1/predict/full", json={
            "product_name": "GLP-1减重针",
            "product_price": 399,
            "category": "消费医疗",
            "population_size": 50,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "product_launch" in d
        assert "pricing" in d
        assert "kol" in d
        assert "livestream" in d
        assert "seeding" in d
        assert "channels" in d

    def test_full_prediction_minimal(self):
        r = client.post("/api/v1/predict/full", json={
            "product_name": "简单测试",
            "product_price": 99,
            "population_size": 30,
            "include_kol": False,
            "include_livestream": False,
            "include_seeding": False,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "kol" not in d


class TestReport:
    def test_generate_report(self):
        r = client.post("/api/v1/report/generate", json={
            "product_name": "测试报告产品",
            "product_price": 199,
            "population_size": 30,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "title" in d
        assert "sections" in d
        assert "markdown" in d
        assert len(d["markdown"]) > 100


class TestTemplateRun:
    def test_run_glp1_template(self):
        r = client.post("/api/v1/template/run", json={
            "template_key": "glp1_weight_loss",
            "product_name": "SlimGuard",
            "product_price": 399,
            "population_size": 50,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["industry"] == "消费医疗"
        assert "reference_data" in d

    def test_run_invalid_template(self):
        r = client.post("/api/v1/template/run", json={
            "template_key": "nonexistent_xyz",
            "product_name": "测试",
            "product_price": 99,
        })
        assert r.status_code == 404


class TestCompare:
    def test_compare_products(self):
        r = client.post("/api/v1/compare", json={
            "product_a": "产品A",
            "product_b": "产品B",
            "price_a": 299,
            "price_b": 399,
            "population_size": 50,
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "product_a" in d
        assert "product_b" in d
        assert "winner" in d
        assert d["winner"] in ["产品A", "产品B"]


class TestCompliance:
    def test_forbidden_scenario_handled(self):
        """即使输入敏感内容，API也不崩溃（返回200或400均可）。"""
        r = client.post("/api/simulate", json={
            "scenario_description": "选举投票模拟",
            "population_size": 10,
        })
        assert r.status_code in [200, 400]


class TestCheckpoints:
    def test_audit_log(self):
        """审计日志端点返回正确结构。"""
        r = client.get("/api/v1/checkpoints/audit")
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "stats" in d

    def test_preview_population(self):
        """dry-run预览人口生成操作。"""
        r = client.post("/api/v1/checkpoints/preview", json={
            "operation": "population", "population_size": 5000,
        })
        assert r.status_code == 200
        assert r.json()["mode"] == "dry_run"

    def test_compare_dry_run(self):
        """产品对比支持dry-run模式。"""
        r = client.post("/api/v1/compare", json={
            "product_a": "A", "product_b": "B",
            "price_a": 299, "price_b": 399,
            "population_size": 50, "dry_run": True,
        })
        assert r.status_code == 200
        assert r.json()["mode"] == "dry_run"

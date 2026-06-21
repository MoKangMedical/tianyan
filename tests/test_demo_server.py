"""天眼Demo Server API测试。"""

import pytest
from conftest import create_test_client

client = create_test_client()


class TestHealthAndInfo:
    def test_health(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "healthy"
        assert d["version"] == "1.0.0"
        assert d["llm"]["provider"] == "deepseek"
        assert d["llm"]["model"] == "deepseek-v4-pro"
        assert "audio" in d["media"]
        assert "video" in d["media"]

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

    def test_campaign_assets(self):
        r = client.get("/api/v1/campaigns/assets")
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "xiaohongshu" in d["channels"]
        assert "douyin" in d["channels"]
        assert "digitalHuman" in d["channels"]
        assert "assets" in d
        assert d["assets"]["xiaohongshu"]["calendar"]

    def test_offers_catalog(self):
        r = client.get("/api/v1/offers/catalog")
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert len(d["offers"]) >= 4

    def test_lead_intake(self):
        r = client.post("/api/v1/leads/intake", json={
            "company_name": "示例公司",
            "contact_name": "张三",
            "contact_channel": "wechat:demo",
            "project_type": "减重",
            "budget_range": "¥3-10万",
            "goals": "想验证商业模式并启动宣传",
            "preferred_offer": "诊断式 POC",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["lead_id"].startswith("lead-")
        assert "notifications" in d

    def test_list_leads(self):
        r = client.get("/api/v1/leads")
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "leads" in d
        assert d["count"] >= 1

    def test_lead_pipeline_summary(self):
        r = client.get("/api/v1/leads/pipeline/summary")
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "summary" in d

    def test_lead_detail_and_status_update(self):
        create = client.post("/api/v1/leads/intake", json={
            "company_name": "跟进公司",
            "contact_name": "赵六",
            "contact_channel": "wechat:zhaoliu",
            "project_type": "护肤",
            "budget_range": "¥3-10万",
            "goals": "想做内容和代运营",
            "preferred_offer": "增长与数字人代运营",
        }).json()
        lead_id = create["lead_id"]

        detail = client.get(f"/api/v1/leads/{lead_id}")
        assert detail.status_code == 200
        assert detail.json()["lead"]["lead_id"] == lead_id

        update = client.post(f"/api/v1/leads/{lead_id}/status", json={
            "status": "proposal",
            "owner": "Alice",
            "note": "已发送方案",
        })
        assert update.status_code == 200
        assert update.json()["update"]["status"] == "proposal"

        history = client.get(f"/api/v1/leads/{lead_id}/history")
        assert history.status_code == 200
        assert len(history.json()["history"]) >= 1

    def test_leads_filtered_and_export_csv(self):
        filtered = client.get("/api/v1/leads", params={"status": "proposal"})
        assert filtered.status_code == 200
        assert "leads" in filtered.json()

        exported = client.get("/api/v1/leads/export.csv")
        assert exported.status_code == 200
        assert "lead_id" in exported.text

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
        assert d["provider"] == "deepseek"
        assert d["model"] == "deepseek-v4-pro"
        assert "title" in d
        assert "summary" in d
        assert "sections" in d
        assert "markdown" in d
        assert len(d["markdown"]) > 100


class TestMedia:
    def test_generate_audio(self):
        r = client.post("/api/v1/media/audio", json={
            "text": "测试旁白",
            "voice": "default_zh",
            "audio_format": "mp3",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["provider"] == "mimo"
        assert d["audio_url"].endswith("/mock/audio/demo.mp3")
        assert d["audio_base64"]

    def test_generate_video(self):
        r = client.post("/api/v1/media/video", json={
            "prompt": "生成一个 20 秒案例视频",
            "voice": "default_zh",
            "audio_format": "mp3",
            "video_provider": "comfyui",
            "video_mode": "narrated-brief",
        })
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["provider"] == "deepseek"
        assert d["audio_provider"] == "mimo"
        assert d["video_provider"] == "comfyui"
        assert d["audio_url"].endswith("/mock/audio/demo.mp3")
        assert d["video_url"].endswith("/mock/video/demo.mp4")
        assert d["poster_url"].endswith("/mock/video/demo.jpg")


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

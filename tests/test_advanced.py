"""天眼平台高级模块测试。

覆盖：
- report_generator（麦肯锡报告生成器）
- persistence（数据持久化层）
- realtime_feeds（实时数据源）
- industry_templates（行业模板）
- mimo_adapter（MIMO API适配器）
"""

import json
import os
import tempfile
import pytest

from tianyan import (
    SyntheticPopulation,
    ConsumerEye,
    ScenarioEngine,
    Scenario,
    McKinseyReportGenerator,
    McKinseyReport,
    ReportSection,
    PersistenceLayer,
    SimulationRun,
    RealtimeFeedManager,
    StockFeedAdapter,
    NewsFeedAdapter,
    PolicyFeedAdapter,
    get_template,
    list_templates,
    get_all_template_keys,
    IndustryTemplate,
    GLP1_WEIGHT_LOSS,
    HEALTH_SUPPLEMENT,
    SKINCARE_LAUNCH,
    TELEHEALTH_PLATFORM,
    MALE_HEALTH,
    MIMOAdapter,
    MockMIMOAdapter,
    MIMOConfig,
)


# ============================================================
# 报告生成器测试
# ============================================================

class TestReportGenerator:
    """麦肯锡报告生成器测试。"""

    def _make_sim_result(self, size=50):
        """用ScenarioEngine生成SimulationResult（report_generator需要的类型）。"""
        pop = SyntheticPopulation(size=size, seed=42)
        engine = ScenarioEngine(pop)
        scenario = Scenario(
            name="GLP-1减重针上市",
            description="一款定价399元的GLP-1减重产品上市，一周一次，科学减重",
            category="general",
        )
        return engine.run(scenario)

    def test_generate_product_launch_report(self):
        gen = McKinseyReportGenerator()
        sim_result = self._make_sim_result()
        report = gen.generate_product_launch_report(
            product_name="GLP-1减重针",
            simulation_result=sim_result,
        )
        assert isinstance(report, McKinseyReport)
        assert report.title != ""

    def test_report_has_sections(self):
        gen = McKinseyReportGenerator()
        sim_result = self._make_sim_result()
        report = gen.generate_product_launch_report(
            product_name="测试产品",
            simulation_result=sim_result,
        )
        assert len(report.sections) > 0
        for section in report.sections:
            assert isinstance(section, ReportSection)
            assert section.title != ""

    def test_report_to_markdown(self):
        gen = McKinseyReportGenerator()
        sim_result = self._make_sim_result()
        report = gen.generate_product_launch_report(
            product_name="测试产品",
            simulation_result=sim_result,
        )
        md = report.to_markdown()
        assert isinstance(md, str)
        assert len(md) > 100

    def test_report_to_json(self):
        gen = McKinseyReportGenerator()
        sim_result = self._make_sim_result()
        report = gen.generate_product_launch_report(
            product_name="测试产品",
            simulation_result=sim_result,
        )
        j = report.to_json()
        data = json.loads(j)
        assert "title" in data

    def test_report_section_confidence(self):
        gen = McKinseyReportGenerator()
        sim_result = self._make_sim_result()
        report = gen.generate_product_launch_report(
            product_name="测试产品",
            simulation_result=sim_result,
        )
        for section in report.sections:
            assert 0 <= section.confidence <= 1

    def test_report_with_different_sizes(self):
        gen = McKinseyReportGenerator()
        for size in [10, 100, 500]:
            sim_result = self._make_sim_result(size=size)
            report = gen.generate_product_launch_report(
                product_name="测试产品",
                simulation_result=sim_result,
            )
            assert len(report.sections) > 0


# ============================================================
# 持久化层测试
# ============================================================

class TestPersistence:
    """数据持久化层测试。"""

    def test_save_and_list_simulations(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            layer = PersistenceLayer(db_path=db_path)
            sim_id = layer.save_simulation(
                scenario_name="测试场景",
                scenario_type="product_launch",
                population_size=100,
                population_params={"region": "一线城市"},
                parameters={"price": 199},
                result_summary={"purchase_intent": 0.65},
                confidence=0.8,
                execution_time_ms=1200,
            )
            assert sim_id > 0

            sims = layer.list_simulations(limit=10)
            assert len(sims) >= 1
            assert sims[0].scenario_name == "测试场景"
        finally:
            os.unlink(db_path)

    def test_get_simulation(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            layer = PersistenceLayer(db_path=db_path)
            sim_id = layer.save_simulation(
                scenario_name="获取测试",
                scenario_type="test",
                population_size=50,
                population_params={},
                parameters={},
                result_summary={"score": 0.5},
                confidence=0.7,
                execution_time_ms=500,
            )
            sim = layer.get_simulation(sim_id)
            assert sim is not None
            assert sim.scenario_name == "获取测试"
        finally:
            os.unlink(db_path)

    def test_save_prediction(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            layer = PersistenceLayer(db_path=db_path)
            layer.save_prediction(
                simulation_id=0,
                product="测试产品",
                scenario_name="产品上市",
                key_metrics={"intent": 0.7, "price_acceptance": 0.5},
                segments={},
                recommendations=["建议A"],
                confidence=0.8,
            )
            preds = layer.list_predictions(product="测试产品")
            assert len(preds) >= 1
        finally:
            os.unlink(db_path)

    def test_save_audit(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            layer = PersistenceLayer(db_path=db_path)
            layer.save_audit(
                action="scenario_check",
                category="product_launch",
                passed=True,
                details={"product": "洗发水"},
            )
            # 至少不应该报错
            assert True
        finally:
            os.unlink(db_path)

    def test_get_stats(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            layer = PersistenceLayer(db_path=db_path)
            stats = layer.get_stats()
            assert isinstance(stats, dict)
            assert "total_simulations" in stats
        finally:
            os.unlink(db_path)

    def test_multiple_simulations(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            layer = PersistenceLayer(db_path=db_path)
            for i in range(5):
                layer.save_simulation(
                    scenario_name=f"场景{i}",
                    scenario_type="test",
                    population_size=50,
                    population_params={},
                    parameters={},
                    result_summary={"score": i * 0.1},
                    confidence=0.7,
                    execution_time_ms=100,
                )
            sims = layer.list_simulations(limit=10)
            assert len(sims) == 5
        finally:
            os.unlink(db_path)


# ============================================================
# 实时数据源测试
# ============================================================

class TestRealtimeFeeds:
    """实时数据源测试。"""

    def test_feed_manager_creation(self):
        manager = RealtimeFeedManager()
        assert manager is not None

    def test_stock_adapter_creation(self):
        adapter = StockFeedAdapter()
        assert adapter is not None

    def test_news_adapter_creation(self):
        adapter = NewsFeedAdapter()
        assert adapter is not None

    def test_policy_adapter_creation(self):
        adapter = PolicyFeedAdapter()
        assert adapter is not None

    def test_manager_has_adapters(self):
        manager = RealtimeFeedManager()
        # 应该能获取已注册的适配器列表
        if hasattr(manager, 'get_adapters'):
            adapters = manager.get_adapters()
            assert isinstance(adapters, (list, dict))
        elif hasattr(manager, 'adapters'):
            assert isinstance(manager.adapters, (list, dict))


# ============================================================
# 行业模板测试
# ============================================================

class TestIndustryTemplates:
    """行业模板测试。"""

    def test_list_templates(self):
        templates = list_templates()
        assert isinstance(templates, list)
        assert len(templates) >= 5

    def test_get_all_keys(self):
        keys = get_all_template_keys()
        assert isinstance(keys, list)
        assert "glp1_weight_loss" in keys
        assert "health_supplement" in keys

    def test_get_glp1_template(self):
        tpl = get_template("glp1_weight_loss")
        assert tpl.name == GLP1_WEIGHT_LOSS.name
        assert tpl.industry == "消费医疗"
        assert "price_range" in tpl.default_params

    def test_get_health_supplement(self):
        tpl = get_template("health_supplement")
        assert tpl.industry in ("消费医疗", "保健品", "健康", "健康消费品")

    def test_get_skincare(self):
        tpl = get_template("skincare_launch")
        assert tpl is not None
        assert len(tpl.key_metrics) > 0

    def test_get_telehealth(self):
        tpl = get_template("telehealth_platform")
        assert tpl is not None

    def test_get_male_health(self):
        tpl = get_template("male_health")
        assert tpl is not None

    def test_invalid_template_returns_none(self):
        tpl = get_template("nonexistent_template_xyz")
        assert tpl is None

    def test_template_has_recommended_population(self):
        tpl = get_template("glp1_weight_loss")
        assert isinstance(tpl.recommended_population, dict)
        assert len(tpl.recommended_population) > 0

    def test_template_has_reference_data(self):
        tpl = get_template("glp1_weight_loss")
        assert isinstance(tpl.reference_data, dict)

    def test_all_templates_have_metrics(self):
        for key in get_all_template_keys():
            tpl = get_template(key)
            assert len(tpl.key_metrics) > 0, f"{key} should have key_metrics"


# ============================================================
# MIMO适配器测试
# ============================================================

class TestMIMOAdapter:
    """MIMO API适配器测试。"""

    def test_mock_adapter_decision(self):
        adapter = MockMIMOAdapter()
        result = adapter.generate_sync("这个人会购买吗？")
        assert "decision" in result or "response" in result

    def test_mock_adapter_various_prompts(self):
        adapter = MockMIMOAdapter()
        prompts = [
            "这个人会购买产品吗？",
            "决策是什么？",
            "普通问题",
        ]
        for prompt in prompts:
            result = adapter.generate_sync(prompt)
            assert isinstance(result, dict)

    def test_config_defaults(self):
        config = MIMOConfig()
        assert config.model == "mimo-v2-pro"
        assert config.max_tokens == 1024
        assert config.temperature == 0.7

    def test_config_custom(self):
        config = MIMOConfig(
            api_key="test_key",
            base_url="https://test.api.com/v1",
            model="custom-model",
            max_tokens=512,
            temperature=0.5,
        )
        assert config.api_key == "test_key"
        assert config.model == "custom-model"
        assert config.max_tokens == 512

    def test_mimo_adapter_creation(self):
        config = MIMOConfig(api_key="fake_key")
        adapter = MIMOAdapter(config=config)
        assert adapter.config.api_key == "fake_key"

    def test_mock_system_prompt(self):
        adapter = MockMIMOAdapter()
        result = adapter.generate_sync(
            "这个人会购买吗？",
            system="你是一个消费者行为分析专家",
        )
        assert isinstance(result, dict)


# ============================================================
# 集成测试
# ============================================================

class TestIntegration:
    """跨模块集成测试。"""

    def test_population_to_eye_to_report(self):
        """完整流程：人群生成 → 场景模拟 → 报告生成。"""
        pop = SyntheticPopulation(size=30, seed=42)
        engine = ScenarioEngine(pop)
        scenario = Scenario(
            name="集成测试",
            description="一款定价199元的快消品上市",
            category="general",
        )
        sim_result = engine.run(scenario)
        gen = McKinseyReportGenerator()
        report = gen.generate_product_launch_report(
            product_name="集成测试产品",
            simulation_result=sim_result,
        )
        assert len(report.sections) > 0
        md = report.to_markdown()
        assert len(md) > 50

    def test_scenario_engine_report(self):
        """场景引擎 → 场景运行。"""
        pop = SyntheticPopulation(size=20, seed=42)
        engine = ScenarioEngine(pop)
        scenario = Scenario(
            name="集成场景",
            description="一款新手机上市",
            category="general",
        )
        result = engine.run(scenario)
        assert result.population_size == 20

    def test_template_with_population(self):
        """行业模板 → 人群推荐参数 → 生成人群。"""
        tpl = get_template("glp1_weight_loss")
        rec = tpl.recommended_population
        pop = SyntheticPopulation(
            size=50,
            seed=42,
            age_range=rec.get("age_range", (25, 45)),
            gender=rec.get("gender", "all"),
        )
        assert len(pop.profiles) == 50

    def test_persistence_with_simulation(self):
        """持久化 → 保存模拟 → 查询。"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            pop = SyntheticPopulation(size=20, seed=42)
            eye = ConsumerEye()
            result = eye.predict_product_launch(
                product_name="持久化测试",
                price=99,
                category="快消品",
                selling_point="便宜好用",
                channels=["淘宝"],
                target_population=pop,
            )
            layer = PersistenceLayer(db_path=db_path)
            sim_id = layer.save_simulation(
                scenario_name="持久化测试",
                scenario_type="product_launch",
                population_size=20,
                population_params={"seed": 42},
                parameters={"price": 99},
                result_summary=result.key_metrics,
                confidence=result.key_metrics.get("avg_confidence", 0.5),
                execution_time_ms=100,
            )
            assert sim_id > 0
            stats = layer.get_stats()
            assert stats["total_simulations"] >= 1
        finally:
            os.unlink(db_path)

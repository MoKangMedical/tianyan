"""天眼平台测试。"""

import pytest
from tianyan import (
    SyntheticPopulation,
    ConsumerEye,
    PolicyEye,
    MarketEye,
    ComplianceChecker,
    ComplianceError,
)


class TestSyntheticPopulation:
    """合成人群测试。"""

    def test_basic_generation(self):
        pop = SyntheticPopulation(size=100, seed=42)
        assert len(pop.profiles) == 100

    def test_age_filter(self):
        pop = SyntheticPopulation(age_range=(25, 35), size=100, seed=42)
        for p in pop.profiles:
            assert 25 <= p.age <= 35

    def test_gender_filter(self):
        pop = SyntheticPopulation(gender="female", size=100, seed=42)
        for p in pop.profiles:
            assert p.gender == "女"

    def test_city_tier_filter(self):
        pop = SyntheticPopulation(region="一线城市", size=100, seed=42)
        for p in pop.profiles:
            assert p.city_tier == "一线城市"

    def test_summary(self):
        pop = SyntheticPopulation(size=100, seed=42)
        summary = pop.summary()
        assert summary["size"] == 100
        assert "avg_age" in summary
        assert "avg_income" in summary


class TestConsumerEye:
    """消费眼测试。"""

    def test_product_launch_prediction(self):
        pop = SyntheticPopulation(size=50, seed=42)
        eye = ConsumerEye()
        result = eye.predict_product_launch(
            product_name="测试产品",
            price=199,
            category="快消品",
            selling_point="测试卖点",
            channels=["淘宝"],
            target_population=pop,
        )
        assert result.scenario_name != ""
        assert 0 <= result.key_metrics["purchase_intent"] <= 1

    def test_ad_creative_test(self):
        pop = SyntheticPopulation(size=50, seed=42)
        eye = ConsumerEye()
        result = eye.test_ad_creative(
            ad_theme="夏日护肤",
            channel="抖音",
            style="种草风",
            target_population=pop,
        )
        assert result.scenario_name != ""


class TestPolicyEye:
    """政策眼测试。"""

    def test_policy_impact(self):
        pop = SyntheticPopulation(size=50, seed=42)
        eye = PolicyEye()
        result = eye.assess_policy_impact(
            policy_name="医保个人账户改革",
            scope="全国",
            changes="门诊报销比例提高",
            target_population=pop,
            policy_category="healthcare",
        )
        assert result.key_metrics["approval_rate"] >= 0

    def test_forbidden_policy_category(self):
        pop = SyntheticPopulation(size=10, seed=42)
        eye = PolicyEye()
        with pytest.raises(ComplianceError):
            eye.assess_policy_impact(
                policy_name="测试",
                scope="",
                changes="",
                target_population=pop,
                policy_category="political",
            )


class TestComplianceChecker:
    """合规检查测试。"""

    def test_clean_scenario(self):
        checker = ComplianceChecker()
        assert checker.check_scenario("product_launch", {"product": "洗发水"})

    def test_political_scenario_blocked(self):
        checker = ComplianceChecker()
        with pytest.raises(ComplianceError):
            checker.check_scenario("election", {"country": "中国"})

    def test_sensitive_word_blocked(self):
        checker = ComplianceChecker()
        with pytest.raises(ComplianceError):
            checker.check_scenario("product_launch", {"name": "选举投票器"})

    def test_data_pii_blocked(self):
        checker = ComplianceChecker()
        with pytest.raises(ComplianceError):
            checker.check_data_usage("user_upload", contains_pii=True)

    def test_output_sanitization(self):
        checker = ComplianceChecker()
        output = {"phone": "13812345678", "name": "张三"}
        sanitized = checker.sanitize_output(output)
        assert "13812345678" not in sanitized["phone"]

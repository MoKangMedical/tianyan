"""决策检查点模块测试。"""

import pytest
from tianyan.checkpoints import (
    CheckpointResult,
    validate_population_params,
    validate_prediction_params,
    validate_batch_operation,
    dry_run_population,
    dry_run_prediction,
    OperationAudit,
    AuditLog,
)


class TestPopulationValidation:
    """人群参数校验测试。"""

    def test_valid_params(self):
        cp = validate_population_params(size=1000, region="一线城市")
        assert cp.approved is True
        assert len(cp.errors) == 0
        assert cp.preview["population_size"] == 1000

    def test_large_population_warning(self):
        cp = validate_population_params(size=15000)
        assert cp.approved is True
        assert any("较大" in w for w in cp.warnings)

    def test_too_large_population_error(self):
        cp = validate_population_params(size=60000)
        assert cp.approved is False
        assert any("超出上限" in e for e in cp.errors)

    def test_invalid_age_range(self):
        cp = validate_population_params(size=100, age_range=(50, 30))
        assert cp.approved is False

    def test_estimated_cost(self):
        cp = validate_population_params(size=5000)
        assert cp.estimated_cost["memory_mb"] > 0
        assert cp.estimated_cost["time_seconds"] > 0


class TestPredictionValidation:
    """预测参数校验测试。"""

    def test_valid_params(self):
        cp = validate_prediction_params(
            product_name="测试产品", price=99.9, population_size=1000,
        )
        assert cp.approved is True

    def test_empty_product_name(self):
        cp = validate_prediction_params(product_name="", price=100, population_size=100)
        assert cp.approved is False

    def test_zero_price(self):
        cp = validate_prediction_params(product_name="X", price=0, population_size=100)
        assert cp.approved is False

    def test_high_price_warning(self):
        cp = validate_prediction_params(product_name="X", price=5000000, population_size=100)
        assert cp.approved is True
        assert any("偏高" in w for w in cp.warnings)

    def test_sub_operations_count(self):
        cp = validate_prediction_params(
            product_name="X", price=100, population_size=1000,
            sub_operations=["KOL", "直播", "种草"],
        )
        assert cp.preview["total_sub_operations"] == 3


class TestBatchValidation:
    """批量操作校验测试。"""

    def test_empty_batch(self):
        cp = validate_batch_operation([])
        assert cp.approved is False

    def test_valid_batch(self):
        ops = [
            {"type": "kol", "product_name": "A", "population_size": 1000},
            {"type": "livestream", "product_name": "A", "population_size": 1000},
        ]
        cp = validate_batch_operation(ops)
        assert cp.approved is True
        assert cp.preview["operation_count"] == 2


class TestDryRun:
    """Dry-run 模式测试。"""

    def test_population_dry_run(self):
        result = dry_run_population(size=5000, region="一线城市")
        assert result["mode"] == "dry_run"
        assert result["operation"] == "create_population"
        assert result["will_execute"] is True

    def test_prediction_dry_run(self):
        result = dry_run_prediction(
            product_name="GLP-1减重药", price=1980,
            population_size=2000,
            include_kol=True, include_livestream=True,
        )
        assert result["mode"] == "dry_run"
        assert result["will_execute"] is True
        assert "checkpoint" in result

    def test_prediction_dry_run_invalid(self):
        result = dry_run_prediction(product_name="", price=-1, population_size=100)
        assert result["will_execute"] is False


class TestAuditLog:
    """审计日志测试。"""

    def test_record_and_recent(self):
        log = AuditLog(max_entries=100)
        log.record(OperationAudit(operation="test", parameters={"x": 1}))
        assert log.count() == 1
        recent = log.recent(5)
        assert len(recent) == 1
        assert recent[0]["operation"] == "test"

    def test_max_entries(self):
        log = AuditLog(max_entries=5)
        for i in range(10):
            log.record(OperationAudit(operation=f"op_{i}", parameters={}))
        assert log.count() == 5
        assert log.recent(1)[0]["operation"] == "op_9"

    def test_stats(self):
        log = AuditLog()
        log.record(OperationAudit(operation="a", parameters={}, dry_run=True))
        log.record(OperationAudit(operation="a", parameters={}, approved=False))
        log.record(OperationAudit(operation="b", parameters={}))
        stats = log.stats()
        assert stats["total"] == 3
        assert stats["dry_runs"] == 1
        assert stats["rejections"] == 1
        assert stats["by_operation"]["a"] == 2

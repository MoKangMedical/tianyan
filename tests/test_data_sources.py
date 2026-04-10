"""天眼数据源适配器测试。"""

import pytest
from tianyan.data_sources import (
    DataSourceType,
    DataQuality,
    DataPoint,
    ChinaStatisticsSource,
    GLP1MarketSource,
    QwenDeepResearchAdapter,
    PolicyDataSource,
    StockFinancialSource,
    DataSourceRegistry,
    create_registry,
)


class TestDataSourceRegistry:
    def test_create_registry(self):
        reg = create_registry()
        assert reg is not None

    def test_register(self):
        reg = create_registry()
        src = ChinaStatisticsSource()
        reg.register(src)
        assert reg.get("china_statistics") is not None

    def test_get_china_stats(self):
        reg = create_registry()
        reg.register(ChinaStatisticsSource())
        source = reg.get("china_statistics")
        assert source is not None

    def test_get_nonexistent(self):
        reg = create_registry()
        source = reg.get("nonexistent_xyz")
        assert source is None


class TestChinaStatisticsSource:
    def test_creation(self):
        src = ChinaStatisticsSource()
        assert src is not None

    def test_name(self):
        src = ChinaStatisticsSource()
        assert src.name == "china_statistics"

    @pytest.mark.asyncio
    async def test_fetch_obesity(self):
        src = ChinaStatisticsSource()
        data = await src.fetch("obesity")
        assert data is not None
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_fetch_returns_datapoints(self):
        src = ChinaStatisticsSource()
        data = await src.fetch("obesity")
        assert isinstance(data, list)
        assert all(isinstance(dp, DataPoint) for dp in data)

    @pytest.mark.asyncio
    async def test_fetch_returns_valid_structure(self):
        src = ChinaStatisticsSource()
        data = await src.fetch("obesity")
        assert len(data) > 0
        dp = data[0]
        assert dp.value is not None
        assert dp.confidence > 0

    @pytest.mark.asyncio
    async def test_fetch_empty(self):
        src = ChinaStatisticsSource()
        data = await src.fetch("nonexistent_xyz_query_12345")
        assert data == []


class TestGLP1MarketSource:
    def test_creation(self):
        src = GLP1MarketSource()
        assert src is not None

    def test_name(self):
        src = GLP1MarketSource()
        assert src.name == "glp1_market"


class TestPolicyDataSource:
    def test_creation(self):
        src = PolicyDataSource()
        assert src is not None

    def test_name(self):
        src = PolicyDataSource()
        assert src.name == "policy_data"


class TestStockFinancialSource:
    def test_creation(self):
        src = StockFinancialSource()
        assert src is not None

    def test_name(self):
        src = StockFinancialSource()
        assert src.name == "stock_financial"


class TestDataPoint:
    def test_creation(self):
        dp = DataPoint(
            value=1.0,
            source="test",
            source_type=DataSourceType.STATISTICS,
            quality=DataQuality.OFFICIAL,
            timestamp="2024-01-01",
            unit="%",
        )
        assert dp.source == "test"
        assert dp.confidence == 0.8

    def test_custom_confidence(self):
        dp = DataPoint(
            value=2.0,
            source="test",
            source_type=DataSourceType.STATISTICS,
            quality=DataQuality.OFFICIAL,
            timestamp="2024-01-01",
            unit="%",
            confidence=0.95,
        )
        assert dp.confidence == 0.95

    def test_metadata_default(self):
        dp = DataPoint(
            value=3.0,
            source="test",
            source_type=DataSourceType.SOCIAL,
            quality=DataQuality.VERIFIED,
            timestamp="2024-01-01",
            unit="亿元",
        )
        assert dp.metadata == {}

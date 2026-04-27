"""
天眼数据集成层 — 统一多源数据查询

整合:
- 静态数据源 (国家统计局/GLP-1市场/政策数据)
- 实时数据源 (A股/新闻/政策更新)
- LLM增强分析 (DeepSeek/MIMO)

用法:
    from tianyan.data_integration import DataIntegration
    di = DataIntegration()
    result = di.query("减肥药市场规模")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from .data_sources import DataSourceRegistry, create_registry, DataPoint
from .realtime_feeds import StockFeedAdapter, NewsFeedAdapter, PolicyFeedAdapter, FeedItem
from .llm_adapter import get_llm, UnifiedLLMAdapter


@dataclass
class IntegratedResult:
    """集成查询结果。"""
    query: str
    static_data: list[DataPoint] = field(default_factory=list)
    realtime_data: list[FeedItem] = field(default_factory=list)
    llm_analysis: str = ""
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "static_data": [dp.to_dict() for dp in self.static_data],
            "realtime_data": [fi.to_dict() for fi in self.realtime_data],
            "llm_analysis": self.llm_analysis,
            "sources": self.sources,
            "confidence": self.confidence,
        }


class DataIntegration:
    """
    统一数据集成层。

    整合静态数据、实时数据和LLM分析。
    """

    def __init__(self, llm: Optional[UnifiedLLMAdapter] = None):
        self.registry = create_registry()
        self.llm = llm or get_llm()
        self._stock_adapter = StockFeedAdapter()
        self._news_adapter = NewsFeedAdapter()
        self._policy_adapter = PolicyFeedAdapter()

    def query(self, query: str, use_llm: bool = True) -> IntegratedResult:
        """
        统一查询接口。

        Args:
            query: 查询关键词
            use_llm: 是否使用LLM增强分析

        Returns:
            IntegratedResult
        """
        result = IntegratedResult(query=query)

        # 1. 查询静态数据源
        for source_name in ["china_statistics", "glp1_market", "policy_data", "stock_financial"]:
            source = self.registry.get(source_name)
            if source:
                try:
                    import asyncio
                    data = asyncio.run(source.fetch(query))
                    if data:
                        result.static_data.extend(data)
                        result.sources.append(source_name)
                except Exception:
                    pass

        # 2. 查询实时数据 (新闻)
        try:
            news_items = self._news_adapter.fetch_latest()
            # Filter by query keywords
            keywords = query.lower().split()
            for item in news_items:
                if any(kw in item.title.lower() or kw in item.content.lower() for kw in keywords):
                    result.realtime_data.append(item)
                    if "news_feed" not in result.sources:
                        result.sources.append("news_feed")
        except Exception:
            pass

        # 3. LLM增强分析
        if use_llm and self.llm.is_llm_available:
            context = self._build_context(result)
            analysis_prompt = f"""基于以下数据，分析"{query}"的市场前景：

{context}

请提供：
1. 市场规模估算
2. 增长趋势
3. 关键驱动因素
4. 风险提示
5. 投资建议

请用JSON格式返回。"""

            system = "你是一位专业的市场分析师，基于数据提供客观、专业的分析。"
            try:
                llm_result = self.llm.generate_json(analysis_prompt, system)
                result.llm_analysis = json.dumps(llm_result, ensure_ascii=False, indent=2)
                result.sources.append("llm_analysis")
            except Exception:
                pass

        # 4. 计算综合置信度
        result.confidence = self._calculate_confidence(result)

        return result

    def _build_context(self, result: IntegratedResult) -> str:
        """构建LLM分析的上下文。"""
        parts = []

        if result.static_data:
            parts.append("=== 静态数据 ===")
            for dp in result.static_data[:5]:  # 限制数量
                parts.append(f"- {dp.source}: {json.dumps(dp.value, ensure_ascii=False)[:200]}")

        if result.realtime_data:
            parts.append("\n=== 实时数据 ===")
            for item in result.realtime_data[:3]:
                parts.append(f"- {item.title}: {item.content[:100]}")

        return "\n".join(parts) if parts else "暂无相关数据"

    def _calculate_confidence(self, result: IntegratedResult) -> float:
        """计算综合置信度。"""
        score = 0.0
        count = 0

        # 静态数据置信度
        if result.static_data:
            avg_conf = sum(dp.confidence for dp in result.static_data) / len(result.static_data)
            score += avg_conf * 0.4
            count += 1

        # 实时数据加分
        if result.realtime_data:
            score += 0.3
            count += 1

        # LLM分析加分
        if result.llm_analysis:
            score += 0.3
            count += 1

        return min(0.95, score) if count > 0 else 0.0

    def get_market_overview(self, industry: str) -> dict[str, Any]:
        """获取行业概览。"""
        result = self.query(f"{industry}市场规模 趋势 政策")
        return {
            "industry": industry,
            "data_points": len(result.static_data),
            "news_count": len(result.realtime_data),
            "analysis": result.llm_analysis,
            "confidence": result.confidence,
            "sources": result.sources,
        }

    def get_competitor_analysis(self, product: str, competitors: list[str]) -> dict[str, Any]:
        """获取竞品分析。"""
        query = f"{product} 竞品 {' '.join(competitors)}"
        result = self.query(query)
        return {
            "product": product,
            "competitors": competitors,
            "analysis": result.llm_analysis,
            "confidence": result.confidence,
        }

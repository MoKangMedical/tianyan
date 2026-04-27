"""
OPC Platform 集成模块

让 OPC Platform 可以调用天眼预测引擎。
"""

from __future__ import annotations

import json
from typing import Any, Optional

from .products import ConsumerEye, PolicyEye, MarketEye, PredictionResult
from .population import SyntheticPopulation
from .conversation import ConversationEngine


class OPCIntegration:
    """
    OPC Platform 集成接口。

    提供简化的API供OPC Platform调用。
    """

    def __init__(self):
        self._consumer_eye = ConsumerEye()
        self._policy_eye = PolicyEye()
        self._market_eye = MarketEye()
        self._conversation_engine = ConversationEngine()

    def predict_product(
        self,
        product_name: str,
        price: float,
        category: str,
        selling_point: str = "",
        channels: list[str] = None,
        population_size: int = 1000,
    ) -> dict[str, Any]:
        """
        产品上市预测。

        Args:
            product_name: 产品名称
            price: 价格
            category: 品类
            selling_point: 卖点
            channels: 渠道列表
            population_size: 人群规模

        Returns:
            预测结果字典
        """
        channels = channels or ["线上"]

        pop = SyntheticPopulation(size=population_size, region="全国")
        result = self._consumer_eye.predict_product_launch(
            product_name=product_name,
            price=price,
            category=category,
            selling_point=selling_point,
            channels=channels,
            target_population=pop,
        )

        return {
            "product": product_name,
            "confidence": result.confidence,
            "metrics": result.key_metrics,
            "segments": result.segments,
            "recommendations": result.recommendations,
        }

    def predict_market_trend(
        self,
        industry: str,
        trend_description: str,
        population_size: int = 1000,
    ) -> dict[str, Any]:
        """
        市场趋势预测。

        Args:
            industry: 行业
            trend_description: 趋势描述
            population_size: 人群规模

        Returns:
            预测结果字典
        """
        pop = SyntheticPopulation(size=population_size, region="全国")
        result = self._market_eye.predict_trend(
            industry=industry,
            trend_description=trend_description,
            target_population=pop,
        )

        return {
            "industry": industry,
            "confidence": result.confidence,
            "metrics": result.key_metrics,
            "recommendations": result.recommendations,
        }

    def start_conversation(self, user_input: str) -> dict[str, Any]:
        """
        开始对话式预测。

        Args:
            user_input: 用户输入

        Returns:
            对话响应
        """
        response = self._conversation_engine.start(user_input)
        return response.to_dict()

    def continue_conversation(self, user_input: str) -> dict[str, Any]:
        """
        继续对话。

        Args:
            user_input: 用户输入

        Returns:
            对话响应
        """
        response = self._conversation_engine.continue_(user_input)
        return response.to_dict()

    def get_health(self) -> dict[str, Any]:
        """健康检查。"""
        return {
            "status": "healthy",
            "service": "tianyan-opc-integration",
            "version": "1.0.0",
            "capabilities": [
                "product_prediction",
                "market_trend",
                "conversation",
            ],
        }

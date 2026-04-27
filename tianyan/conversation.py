"""
天眼对话式预测引擎 — 多轮交互式市场预测

支持用户通过自然语言进行多轮对话：
- 第1轮：产品基本信息
- 第2轮：目标市场确认
- 第3轮：渠道策略讨论
- 第4轮：定价优化
- 第5轮：风险评估

用法:
    from tianyan.conversation import ConversationEngine
    engine = ConversationEngine()
    r1 = engine.start("我想推出一款减重产品")
    r2 = engine.continue_("定价299元/月，目标25-45岁女性")
    r3 = engine.continue_("小红书和抖音哪个渠道更好？")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .llm_adapter import get_llm, UnifiedLLMAdapter
from .population import SyntheticPopulation
from .products import ConsumerEye, PredictionResult


class ConversationStage(Enum):
    """对话阶段。"""
    INITIAL = "initial"           # 初始阶段
    PRODUCT = "product"           # 产品定义
    MARKET = "market"             # 市场确认
    CHANNEL = "channel"           # 渠道讨论
    PRICING = "pricing"           # 定价优化
    RISK = "risk"                 # 风险评估
    COMPLETE = "complete"         # 完成


@dataclass
class ConversationState:
    """对话状态。"""
    stage: ConversationStage = ConversationStage.INITIAL
    history: list[dict[str, str]] = field(default_factory=list)
    product_info: dict[str, Any] = field(default_factory=dict)
    market_info: dict[str, Any] = field(default_factory=dict)
    channel_info: dict[str, Any] = field(default_factory=dict)
    pricing_info: dict[str, Any] = field(default_factory=dict)
    prediction_result: Optional[PredictionResult] = None

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def get_context(self) -> str:
        """获取对话上下文摘要。"""
        parts = []
        if self.product_info:
            parts.append(f"产品: {json.dumps(self.product_info, ensure_ascii=False)}")
        if self.market_info:
            parts.append(f"市场: {json.dumps(self.market_info, ensure_ascii=False)}")
        if self.channel_info:
            parts.append(f"渠道: {json.dumps(self.channel_info, ensure_ascii=False)}")
        if self.pricing_info:
            parts.append(f"定价: {json.dumps(self.pricing_info, ensure_ascii=False)}")
        return "\n".join(parts)


@dataclass
class ConversationResponse:
    """对话响应。"""
    stage: str
    message: str
    suggestions: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "message": self.message,
            "suggestions": self.suggestions,
            "data": self.data,
            "is_complete": self.is_complete,
        }


class ConversationEngine:
    """
    对话式预测引擎。

    通过多轮对话收集信息，逐步完善预测。
    """

    def __init__(self, llm: Optional[UnifiedLLMAdapter] = None):
        self.llm = llm or get_llm()
        self._state: Optional[ConversationState] = None

    @property
    def state(self) -> Optional[ConversationState]:
        return self._state

    def start(self, user_input: str) -> ConversationResponse:
        """
        开始对话。

        Args:
            user_input: 用户初始输入

        Returns:
            ConversationResponse
        """
        self._state = ConversationState()
        self._state.add_message("user", user_input)

        # 解析初始输入
        product_info = self._extract_product_info(user_input)
        self._state.product_info = product_info

        if product_info.get("name"):
            self._state.stage = ConversationStage.PRODUCT
            return ConversationResponse(
                stage="product",
                message=f"好的，我来帮你分析「{product_info.get('name', '这个产品')}」的市场前景。\n\n请告诉我更多信息：",
                suggestions=[
                    "定价多少？目标人群是谁？",
                    "主要卖点是什么？",
                    "打算通过什么渠道销售？",
                ],
                data=product_info,
            )
        else:
            self._state.stage = ConversationStage.INITIAL
            return ConversationResponse(
                stage="initial",
                message="你好！我是天眼预测助手。请告诉我你想推出什么产品？",
                suggestions=[
                    "我想推出一款减重产品",
                    "我想测试一款新护肤品的市场反应",
                    "我想分析远程医疗平台的商业前景",
                ],
            )

    def continue_(self, user_input: str) -> ConversationResponse:
        """
        继续对话。

        Args:
            user_input: 用户输入

        Returns:
            ConversationResponse
        """
        if not self._state:
            return self.start(user_input)

        self._state.add_message("user", user_input)

        # 根据当前阶段处理
        if self._state.stage == ConversationStage.INITIAL:
            return self._handle_initial(user_input)
        elif self._state.stage == ConversationStage.PRODUCT:
            return self._handle_product(user_input)
        elif self._state.stage == ConversationStage.MARKET:
            return self._handle_market(user_input)
        elif self._state.stage == ConversationStage.CHANNEL:
            return self._handle_channel(user_input)
        elif self._state.stage == ConversationStage.PRICING:
            return self._handle_pricing(user_input)
        elif self._state.stage == ConversationStage.RISK:
            return self._handle_risk(user_input)
        else:
            return ConversationResponse(
                stage="complete",
                message="预测已完成。你可以输入新的产品开始新一轮分析。",
                is_complete=True,
            )

    def _handle_initial(self, user_input: str) -> ConversationResponse:
        """处理初始阶段。"""
        product_info = self._extract_product_info(user_input)
        self._state.product_info.update(product_info)
        self._state.stage = ConversationStage.PRODUCT

        name = self._state.product_info.get("name", "这个产品")
        return ConversationResponse(
            stage="product",
            message=f"收到！「{name}」— 请补充以下信息：",
            suggestions=[
                "定价多少？目标人群是谁？",
                "主要卖点和竞争优势是什么？",
                "打算通过什么渠道销售？",
            ],
            data=self._state.product_info,
        )

    def _handle_product(self, user_input: str) -> ConversationResponse:
        """处理产品定义阶段。"""
        # 提取更多信息
        info = self._extract_detailed_info(user_input)
        self._state.product_info.update(info)

        # 检查是否足够进入下一阶段
        has_price = "price" in self._state.product_info
        has_category = "category" in self._state.product_info

        if has_price and has_category:
            self._state.stage = ConversationStage.MARKET
            return ConversationResponse(
                stage="market",
                message=f"产品信息已收集。现在确认目标市场：\n\n"
                        f"- 品类: {self._state.product_info.get('category', '未知')}\n"
                        f"- 定价: ¥{self._state.product_info.get('price', '未知')}\n\n"
                        f"目标人群是谁？",
                suggestions=[
                    "25-45岁女性，一二线城市",
                    "18-30岁年轻人，全国范围",
                    "35-55岁中高收入人群",
                ],
                data=self._state.product_info,
            )
        else:
            missing = []
            if not has_price:
                missing.append("定价")
            if not has_category:
                missing.append("品类")
            return ConversationResponse(
                stage="product",
                message=f"还需要补充：{', '.join(missing)}",
                suggestions=[
                    "定价XX元，属于XX品类",
                ],
                data=self._state.product_info,
            )

    def _handle_market(self, user_input: str) -> ConversationResponse:
        """处理市场确认阶段。"""
        market_info = self._extract_market_info(user_input)
        self._state.market_info.update(market_info)
        self._state.stage = ConversationStage.CHANNEL

        return ConversationResponse(
            stage="channel",
            message="市场信息已确认。现在讨论渠道策略：",
            suggestions=[
                "小红书种草 + 抖音直播",
                "天猫旗舰店 + 线下渠道",
                "微信私域 + 社群运营",
            ],
            data={**self._state.product_info, **self._state.market_info},
        )

    def _handle_channel(self, user_input: str) -> ConversationResponse:
        """处理渠道讨论阶段。"""
        channel_info = self._extract_channel_info(user_input)
        self._state.channel_info.update(channel_info)
        self._state.stage = ConversationStage.PRICING

        return ConversationResponse(
            stage="pricing",
            message="渠道策略已记录。现在优化定价：",
            suggestions=[
                "保持当前定价",
                "降价10%提高转化",
                "提价20%做高端定位",
            ],
            data={**self._state.product_info, **self._state.channel_info},
        )

    def _handle_pricing(self, user_input: str) -> ConversationResponse:
        """处理定价优化阶段。"""
        pricing_info = self._extract_pricing_info(user_input)
        self._state.pricing_info.update(pricing_info)
        self._state.stage = ConversationStage.RISK

        return ConversationResponse(
            stage="risk",
            message="定价已确认。最后评估风险：",
            suggestions=[
                "主要风险是竞争激烈",
                "担心供应链不稳定",
                "政策监管是最大不确定性",
            ],
            data={**self._state.product_info, **self._state.pricing_info},
        )

    def _handle_risk(self, user_input: str) -> ConversationResponse:
        """处理风险评估阶段。"""
        # 运行预测
        self._run_prediction()
        self._state.stage = ConversationStage.COMPLETE

        result = self._state.prediction_result
        if result:
            return ConversationResponse(
                stage="complete",
                message=f"预测完成！\n\n"
                        f"- 购买意愿: {result.key_metrics.get('购买意愿', 0)*100:.1f}%\n"
                        f"- 置信度: {result.confidence*100:.1f}%\n"
                        f"- 建议: {', '.join(result.recommendations[:3])}",
                data={
                    "prediction": {
                        "confidence": result.confidence,
                        "metrics": result.key_metrics,
                        "recommendations": result.recommendations,
                    }
                },
                is_complete=True,
            )
        else:
            return ConversationResponse(
                stage="complete",
                message="预测完成，但数据不足无法生成详细结果。",
                is_complete=True,
            )

    def _run_prediction(self):
        """运行预测。"""
        try:
            pop = SyntheticPopulation(size=1000, region="全国")
            eye = ConsumerEye()

            product_name = self._state.product_info.get("name", "产品")
            price = self._state.product_info.get("price", 99)
            category = self._state.product_info.get("category", "消费品")
            channels = self._state.channel_info.get("channels", ["线上"])

            result = eye.predict_product_launch(
                product_name=product_name,
                price=float(price),
                category=category,
                selling_point=self._state.product_info.get("selling_point", ""),
                channels=channels,
                target_population=pop,
            )
            self._state.prediction_result = result
        except Exception as e:
            print(f"Prediction error: {e}")

    def _extract_product_info(self, text: str) -> dict[str, Any]:
        """从文本提取产品信息。"""
        info = {}

        # 提取品类
        categories = {
            "减重": "健康消费品",
            "减肥": "健康消费品",
            "护肤": "美妆护肤",
            "美妆": "美妆护肤",
            "医疗": "数字健康",
            "健康": "健康消费品",
            "食品": "食品饮料",
            "饮料": "食品饮料",
        }
        for keyword, category in categories.items():
            if keyword in text:
                info["category"] = category
                break

        # 提取产品名称 - 简化逻辑
        # 去掉常见前缀
        prefixes_to_remove = ["我想推出", "我想发布", "我想上市", "我想测试", "我想分析", "一款", "一个", "的"]
        clean_text = text
        for prefix in prefixes_to_remove:
            clean_text = clean_text.replace(prefix, "")

        # 取剩余内容作为产品名
        clean_text = clean_text.strip()
        if clean_text:
            # 取前15个字符
            info["name"] = clean_text[:15]

        return info

    def _extract_detailed_info(self, text: str) -> dict[str, Any]:
        """提取详细产品信息。"""
        info = {}

        # 提取价格
        import re
        price_match = re.search(r'(\d+)\s*元', text)
        if price_match:
            info["price"] = int(price_match.group(1))

        # 提取品类
        categories = {
            "减重": "健康消费品",
            "护肤": "美妆护肤",
            "医疗": "数字健康",
        }
        for keyword, category in categories.items():
            if keyword in text:
                info["category"] = category
                break

        return info

    def _extract_market_info(self, text: str) -> dict[str, Any]:
        """提取市场信息。"""
        info = {}

        # 提取年龄段
        import re
        age_match = re.search(r'(\d+)[\s-]*(\d+)\s*岁', text)
        if age_match:
            info["age_range"] = [int(age_match.group(1)), int(age_match.group(2))]

        # 提取城市等级
        if "一线" in text:
            info["city_tiers"] = ["一线城市"]
        elif "全国" in text:
            info["city_tiers"] = ["全国"]

        # 提取性别
        if "女性" in text or "女" in text:
            info["gender"] = "female"
        elif "男性" in text or "男" in text:
            info["gender"] = "male"

        return info

    def _extract_channel_info(self, text: str) -> dict[str, Any]:
        """提取渠道信息。"""
        info = {"channels": []}

        channel_keywords = {
            "小红书": "小红书",
            "抖音": "抖音",
            "天猫": "天猫",
            "京东": "京东",
            "微信": "微信",
            "线下": "线下",
        }
        for keyword, channel in channel_keywords.items():
            if keyword in text:
                info["channels"].append(channel)

        if not info["channels"]:
            info["channels"] = ["线上"]

        return info

    def _extract_pricing_info(self, text: str) -> dict[str, Any]:
        """提取定价信息。"""
        info = {}

        if "降价" in text:
            info["pricing_strategy"] = "降价促销"
        elif "提价" in text or "高端" in text:
            info["pricing_strategy"] = "高端定位"
        else:
            info["pricing_strategy"] = "保持现状"

        return info

    def reset(self):
        """重置对话。"""
        self._state = None

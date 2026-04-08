"""
多Agent人群模拟引擎

每个合成人口生成一个SimulationAgent，该Agent根据其画像做出决策。
支持LLM驱动决策（MIMO API）和规则引擎降级。
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING

from .population import PopulationProfile

if TYPE_CHECKING:
    from .mimo_adapter import MIMOAdapter


@dataclass
class AgentPersonality:
    """Agent性格参数（从PopulationProfile派生）。"""
    openness: float = 0.5          # 开放性（接受新事物）
    conscientiousness: float = 0.5  # 尽责性（理性决策）
    extraversion: float = 0.5      # 外向性（社交活跃）
    agreeableness: float = 0.5     # 宜人性（从众倾向）
    neuroticism: float = 0.5       # 神经质（情绪波动）

    @classmethod
    def from_profile(cls, profile: PopulationProfile) -> AgentPersonality:
        """从人口画像推导性格。"""
        return cls(
            openness=profile.digital_literacy * 0.7 + profile.risk_tolerance * 0.3,
            conscientiousness=(1 - profile.price_sensitivity) * 0.5 + profile.brand_loyalty * 0.5,
            extraversion=profile.social_influence,
            agreeableness=profile.social_influence * 0.6 + (1 - profile.risk_tolerance) * 0.4,
            neuroticism=profile.price_sensitivity * 0.5 + (1 - profile.risk_tolerance) * 0.5,
        )


@dataclass
class AgentDecision:
    """Agent的单次决策结果。"""
    agent_id: str
    decision: str                  # 决策内容
    confidence: float              # 置信度
    reasoning: str                 # 决策理由
    influenced_by: list[str] = field(default_factory=list)  # 被谁影响
    timestamp: int = 0


class SimulationAgent:
    """
    模拟Agent — 合成人群中的单个决策者。

    每个Agent拥有：
    - 人口画像（demographics）
    - 性格参数（personality）
    - 决策历史（decisions）
    - 社交联系（connections）

    支持两种决策模式：
    - LLM驱动：通过MIMO API进行深度推理
    - 规则引擎：MIMO不可用时的降级方案
    """

    def __init__(self, profile: PopulationProfile):
        self.profile = profile
        self.personality = AgentPersonality.from_profile(profile)
        self.decisions: list[AgentDecision] = []
        self.connections: list[str] = []  # 其他agent_id
        self.opinion_state: dict[str, float] = {}  # 对各话题的态度

    def evaluate(self, scenario_prompt: str) -> AgentDecision:
        """
        评估一个场景并做出决策（同步版，规则引擎）。

        Args:
            scenario_prompt: 场景描述prompt。

        Returns:
            AgentDecision决策结果。
        """
        decision, confidence, reasoning = self._rule_based_decide(scenario_prompt)

        agent_decision = AgentDecision(
            agent_id=self.profile.agent_id,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
        )
        self.decisions.append(agent_decision)
        return agent_decision

    async def evaluate_async(
        self,
        scenario_prompt: str,
        mimo_adapter: "MIMOAdapter",
    ) -> AgentDecision:
        """
        异步评估场景 — 使用MIMO LLM进行深度推理。

        如果MIMO调用失败，自动降级到规则引擎。

        Args:
            scenario_prompt: 场景描述prompt。
            mimo_adapter: MIMO API适配器实例。

        Returns:
            AgentDecision决策结果。
        """
        llm_prompt = self.get_llm_prompt(scenario_prompt)

        try:
            result = await mimo_adapter.generate(
                prompt=llm_prompt,
                system="你是一个模拟消费者的AI助手。请严格按照JSON格式回答。",
            )

            # 解析LLM响应
            decision = result.get("decision", "不确定")
            confidence = float(result.get("confidence", 0.5))
            reasoning = result.get("reasoning", "LLM未提供理由")

            # 限制置信度范围
            if confidence > 1.0:
                confidence = confidence / 100.0  # 如果返回的是百分比
            confidence = max(0.1, min(1.0, confidence))

            agent_decision = AgentDecision(
                agent_id=self.profile.agent_id,
                decision=decision,
                confidence=confidence,
                reasoning=f"[LLM推理] {reasoning}",
            )
        except Exception as e:
            # 降级到规则引擎
            decision, confidence, reasoning = self._rule_based_decide(scenario_prompt)
            agent_decision = AgentDecision(
                agent_id=self.profile.agent_id,
                decision=decision,
                confidence=confidence,
                reasoning=f"[规则引擎降级] {reasoning} (MIMO错误: {e})",
            )

        self.decisions.append(agent_decision)
        return agent_decision

    @classmethod
    async def batch_evaluate(
        cls,
        agents: list[SimulationAgent],
        scenario_prompt: str,
        mimo_adapter: "MIMOAdapter",
        batch_size: int = 10,
    ) -> list[AgentDecision]:
        """
        批量评估多个Agent的决策。

        使用分批并发策略，控制MIMO API的并发量。

        Args:
            agents: Agent列表。
            scenario_prompt: 场景描述。
            mimo_adapter: MIMO适配器实例。
            batch_size: 每批处理数量。

        Returns:
            所有Agent的决策列表。
        """
        all_decisions: list[AgentDecision] = []

        for i in range(0, len(agents), batch_size):
            batch = agents[i:i + batch_size]
            tasks = [
                agent.evaluate_async(scenario_prompt, mimo_adapter)
                for agent in batch
            ]
            batch_decisions = await asyncio.gather(*tasks, return_exceptions=True)

            for j, result in enumerate(batch_decisions):
                if isinstance(result, Exception):
                    # 异常时用规则引擎降级
                    agent = batch[j]
                    decision, confidence, reasoning = agent._rule_based_decide(scenario_prompt)
                    all_decisions.append(AgentDecision(
                        agent_id=agent.profile.agent_id,
                        decision=decision,
                        confidence=confidence,
                        reasoning=f"[批量推理降级] {reasoning}",
                    ))
                else:
                    all_decisions.append(result)

        return all_decisions

    def _rule_based_decide(self, scenario: str) -> tuple[str, float, str]:
        """基于画像的规则决策（简化版）。"""
        # 价格相关判断
        if "定价" in scenario or "价格" in scenario:
            if self.profile.price_sensitivity > 0.7:
                return ("观望", 0.7, f"价格敏感度{self.profile.price_sensitivity:.0%}，会等待折扣")
            elif self.profile.price_sensitivity < 0.3:
                return ("购买", 0.6, f"价格敏感度低，更关注品质和品牌")
            else:
                return ("考虑", 0.5, f"需要了解更多产品信息再做决定")

        # 新产品判断
        if "新" in scenario or "上市" in scenario:
            if self.personality.openness > 0.7:
                return ("尝试", 0.6, "开放性高，愿意尝试新事物")
            elif self.profile.brand_loyalty > 0.7:
                return ("观望", 0.6, "品牌忠诚度高，需要观察口碑")
            else:
                return ("考虑", 0.5, "会在社交圈了解后再决定")

        # 渠道判断
        if "渠道" in scenario or "在哪买" in scenario:
            if "抖音" in self.profile.channels and self.profile.social_influence > 0.6:
                return ("抖音", 0.6, "社交影响大，抖音种草可能性高")
            elif "京东" in self.profile.channels and self.profile.age > 35:
                return ("京东", 0.6, "更信任京东的品质保障")
            elif "拼多多" in self.profile.channels and self.profile.price_sensitivity > 0.6:
                return ("拼多多", 0.6, "价格敏感，拼多多更有吸引力")
            else:
                return ("淘宝", 0.5, "综合电商平台")

        # 政策相关
        if "政策" in scenario or "支持" in scenario:
            if self.profile.health_consciousness > 0.6:
                return ("支持", 0.7, "健康意识高，支持相关健康政策")
            elif self.profile.risk_tolerance < 0.3:
                return ("观望", 0.5, "偏保守，需观察政策实际效果")
            else:
                return ("考虑", 0.5, "需要了解政策具体内容")

        # 默认
        return ("不确定", 0.3, "需要更多信息来判断")

    def get_llm_prompt(self, scenario: str) -> str:
        """构建LLM推理的Prompt。"""
        return f"""你正在扮演一个虚拟消费者。请严格按照以下身份做出决策。

## 你的身份
{self.profile.to_prompt_context()}

## 当前场景
{scenario}

## 请回答
1. 你的决策（购买/不购买/观望/考虑/尝试/支持/不支持）
2. 决策理由（从你的身份角度出发，不超过100字）
3. 置信度（0-100%）

请用JSON格式回答：
{{"decision": "...", "reasoning": "...", "confidence": 0.xx}}
"""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.profile.agent_id,
            "age": self.profile.age,
            "gender": self.profile.gender,
            "city": self.profile.city,
            "income": self.profile.monthly_income,
            "archetype": self.profile.consumer_archetype,
            "personality": {
                "openness": self.personality.openness,
                "conscientiousness": self.personality.conscientiousness,
                "extraversion": self.personality.extraversion,
                "agreeableness": self.personality.agreeableness,
                "neuroticism": self.personality.neuroticism,
            },
        }

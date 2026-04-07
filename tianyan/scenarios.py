"""
场景引擎 (Scenario Engine)

定义和执行模拟场景，协调多Agent交互。
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Optional

from .agents import SimulationAgent, AgentDecision
from .population import SyntheticPopulation


@dataclass
class Scenario:
    """模拟场景定义。"""
    name: str
    description: str
    category: str  # "product_launch", "pricing", "channel", "brand", "policy"
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: list[str] = field(default_factory=list)


@dataclass
class SimulationResult:
    """模拟结果。"""
    scenario: Scenario
    population_size: int
    decisions: list[AgentDecision] = field(default_factory=dict)  # type: ignore
    aggregate: dict[str, Any] = field(default_factory=dict)
    segments: dict[str, dict[str, float]] = field(default_factory=dict)
    execution_time_ms: float = 0.0

    @property
    def purchase_intent(self) -> float:
        """购买意愿（购买+考虑的比例）。"""
        if not self.decisions:
            return 0.0
        positive = sum(1 for d in self.decisions if d.decision in ("购买", "考虑"))
        return positive / len(self.decisions)

    @property
    def approval_rate(self) -> float:
        """支持率。"""
        if not self.decisions:
            return 0.0
        positive = sum(1 for d in self.decisions if d.decision in ("支持", "购买", "尝试"))
        return positive / len(self.decisions)

    def to_report(self) -> str:
        """生成文字报告。"""
        decision_dist = Counter(d.decision for d in self.decisions)
        report = f"""
# 模拟报告：{self.scenario.name}

## 基本信息
- 场景类别：{self.scenario.category}
- 模拟人群：{self.population_size}人
- 执行时间：{self.execution_time_ms:.0f}ms

## 决策分布
"""
        for decision, count in decision_dist.most_common():
            pct = count / len(self.decisions) * 100
            report += f"- {decision}: {count}人 ({pct:.1f}%)\n"

        report += f"\n## 关键指标\n"
        for key, value in self.aggregate.items():
            if isinstance(value, float):
                report += f"- {key}: {value:.1%}\n"
            else:
                report += f"- {key}: {value}\n"

        if self.segments:
            report += f"\n## 分群洞察\n"
            for segment, metrics in self.segments.items():
                report += f"### {segment}\n"
                for metric, value in metrics.items():
                    if isinstance(value, float):
                        report += f"- {metric}: {value:.1%}\n"
                    else:
                        report += f"- {metric}: {value}\n"

        return report


class ScenarioEngine:
    """
    场景引擎：协调多Agent模拟。

    执行流程：
    1. 加载合成人群
    2. 为每个Agent生成决策
    3. 模拟社交传播（Agent间影响）
    4. 汇聚结果，生成报告
    """

    def __init__(self, population: SyntheticPopulation):
        self.population = population
        self.agents = [SimulationAgent(p) for p in population.profiles]

    def run(
        self,
        scenario: Scenario,
        rounds: int = 1,
        social_propagation: bool = True,
    ) -> SimulationResult:
        """
        执行模拟。

        Args:
            scenario: 模拟场景。
            rounds: 模拟轮数。
            social_propagation: 是否模拟社交传播。

        Returns:
            模拟结果。
        """
        start_time = time.time()

        # Phase 1: 独立决策
        decisions = []
        for agent in self.agents:
            prompt = self._build_scenario_prompt(scenario, agent)
            decision = agent.evaluate(prompt)
            decisions.append(decision)

        # Phase 2: 社交传播
        if social_propagation and rounds > 1:
            for round_num in range(1, rounds):
                decisions = self._propagate(decisions, scenario)

        # Phase 3: 汇聚结果
        aggregate = self._aggregate(decisions, scenario)
        segments = self._segment_analysis(decisions, scenario)

        elapsed = (time.time() - start_time) * 1000

        return SimulationResult(
            scenario=scenario,
            population_size=len(self.agents),
            decisions=decisions,
            aggregate=aggregate,
            segments=segments,
            execution_time_ms=elapsed,
        )

    def _build_scenario_prompt(self, scenario: Scenario, agent: SimulationAgent) -> str:
        """为特定Agent构建场景Prompt。"""
        params = scenario.parameters
        prompt = scenario.description

        if scenario.category == "product_launch":
            prompt = f"""
一款新产品即将上市：
- 产品：{params.get('product_name', '未知')}
- 定价：¥{params.get('price', '?')}
- 品类：{params.get('category', '未知')}
- 主打卖点：{params.get('selling_point', '未知')}
- 上市渠道：{', '.join(params.get('channels', []))}

你会购买吗？"""
        elif scenario.category == "pricing":
            prompt = f"""
一款产品正在考虑定价策略：
- 产品：{params.get('product_name', '未知')}
- 建议价格区间：¥{params.get('price_low', '?')} - ¥{params.get('price_high', '?')}
- 你认为合理的价格是多少？
"""
        elif scenario.category == "advertising":
            prompt = f"""
一个广告创意测试：
- 广告主题：{params.get('ad_theme', '未知')}
- 投放渠道：{params.get('channel', '未知')}
- 创意风格：{params.get('style', '未知')}

看到这个广告你会点击吗？"""
        elif scenario.category == "policy":
            prompt = f"""
一项新政策即将实施：
- 政策：{params.get('policy_name', '未知')}
- 影响范围：{params.get('scope', '未知')}
- 主要变化：{params.get('changes', '未知')}

你支持这项政策吗？"""

        return prompt

    def _propagate(
        self,
        decisions: list[AgentDecision],
        scenario: Scenario,
    ) -> list[AgentDecision]:
        """模拟社交传播：高影响力Agent的观点会影响低影响力Agent。"""
        # 简化实现：统计当前决策分布，让从众倾向高的Agent调整
        decision_counts = Counter(d.decision for d in decisions)
        most_common = decision_counts.most_common(1)[0][0]
        most_common_pct = decision_counts.most_common(1)[0][1] / len(decisions)

        updated_decisions = []
        for i, agent in enumerate(self.agents):
            original = decisions[i]
            # 从众倾向高 + 当前决策不主流 → 可能改变
            if (agent.personality.agreeableness > 0.7 and
                original.decision != most_common and
                most_common_pct > 0.4 and
                original.confidence < 0.6):
                updated = AgentDecision(
                    agent_id=original.agent_id,
                    decision=most_common,
                    confidence=0.5,
                    reasoning=f"受社交圈影响，从众倾向高",
                    influenced_by=["social_propagation"],
                )
                updated_decisions.append(updated)
            else:
                updated_decisions.append(original)

        return updated_decisions

    def _aggregate(
        self,
        decisions: list[AgentDecision],
        scenario: Scenario,
    ) -> dict[str, Any]:
        """汇聚全局结果。"""
        total = len(decisions)
        if total == 0:
            return {}

        decision_counts = Counter(d.decision for d in decisions)
        avg_confidence = sum(d.confidence for d in decisions) / total

        return {
            "total_agents": total,
            "avg_confidence": avg_confidence,
            "top_decision": decision_counts.most_common(1)[0][0],
            "decision_distribution": dict(decision_counts),
            "purchase_intent": sum(1 for d in decisions if d.decision in ("购买", "考虑")) / total,
            "social_influence_rate": sum(1 for d in decisions if d.influenced_by) / total,
        }

    def _segment_analysis(
        self,
        decisions: list[AgentDecision],
        scenario: Scenario,
    ) -> dict[str, dict[str, float]]:
        """分群分析。"""
        segments = {}

        # 按城市等级分群
        for tier in ("一线城市", "新一线城市", "二线城市", "三线及以下"):
            tier_agents = [a for a in self.agents if a.profile.city_tier == tier]
            if tier_agents:
                tier_decisions = [d for d in decisions if d.agent_id in {a.profile.agent_id for a in tier_agents}]
                if tier_decisions:
                    segments[f"城市_{tier}"] = {
                        "purchase_intent": sum(1 for d in tier_decisions if d.decision in ("购买", "考虑")) / len(tier_decisions),
                        "avg_confidence": sum(d.confidence for d in tier_decisions) / len(tier_decisions),
                    }

        # 按年龄段分群
        for age_label, age_min, age_max in [("18-24", 18, 24), ("25-34", 25, 34), ("35-44", 35, 44), ("45-54", 45, 54), ("55+", 55, 100)]:
            age_agents = [a for a in self.agents if age_min <= a.profile.age <= age_max]
            if age_agents:
                age_decisions = [d for d in decisions if d.agent_id in {a.profile.agent_id for a in age_agents}]
                if age_decisions:
                    segments[f"年龄_{age_label}"] = {
                        "purchase_intent": sum(1 for d in age_decisions if d.decision in ("购买", "考虑")) / len(age_decisions),
                        "avg_confidence": sum(d.confidence for d in age_decisions) / len(age_decisions),
                    }

        return segments

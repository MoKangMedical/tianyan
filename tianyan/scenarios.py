"""
场景引擎 (Scenario Engine)

定义和执行模拟场景，协调多Agent交互。
支持基于图论的社交网络传播模型（SIR类扩散）。
v2.0: 支持 LLM 驱动决策（DeepSeek API）。
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from .agents import SimulationAgent, AgentDecision
from .population import SyntheticPopulation

logger = logging.getLogger("tianyan.scenarios")


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
    decisions: list[AgentDecision] = field(default_factory=list)
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

    社交传播模型：
    - 基于图论的社交网络（小世界网络）
    - SIR类信息扩散模型
    - 意见领袖效应
    """

    def __init__(self, population: SyntheticPopulation):
        self.population = population
        self.agents = [SimulationAgent(p) for p in population.profiles]
        self._agent_map: dict[str, SimulationAgent] = {
            a.profile.agent_id: a for a in self.agents
        }
        self._social_network: dict[str, list[str]] = {}
        self._network_built = False

    def run(
        self,
        scenario: Scenario,
        rounds: int = 1,
        social_propagation: bool = True,
        use_llm: bool = False,
        llm_batch_size: int = 10,
    ) -> SimulationResult:
        """
        执行模拟。

        Args:
            scenario: 模拟场景。
            rounds: 模拟轮数。
            social_propagation: 是否模拟社交传播。
            use_llm: 是否使用 LLM（DeepSeek）进行深度推理。
            llm_batch_size: LLM 推理时的批次大小。

        Returns:
            模拟结果。
        """
        start_time = time.time()

        # Phase 1: 独立决策
        if use_llm:
            decisions = self._run_llm_decision(scenario, llm_batch_size)
        else:
            decisions = []
            for agent in self.agents:
                prompt = self._build_scenario_prompt(scenario, agent)
                decision = agent.evaluate(prompt)
                decisions.append(decision)

        # Phase 2: 社交传播
        if social_propagation and rounds > 1:
            # 构建社交网络（仅首次）
            if not self._network_built:
                self._build_social_network()
                self._network_built = True

            for round_num in range(1, rounds):
                decisions = self._network_propagate(decisions, scenario, round_num)

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

    # ---- 社交网络构建 ----

    def _build_social_network(self, avg_connections: int = 5):
        """
        基于同质性（homophily）构建社交网络。

        连接概率受以下因素影响：
        - 同城市：+0.3
        - 同城市等级：+0.1
        - 年龄差<5岁：+0.15
        - 共同兴趣：每个+0.1
        - 社交影响力差小：+0.1

        最终形成小世界网络结构。
        """
        n = len(self.agents)
        if n < 2:
            return

        # 初始化连接列表
        for agent in self.agents:
            agent.connections = []
            self._social_network[agent.profile.agent_id] = []

        # 分组索引（加速查找）
        city_agents: dict[str, list[str]] = defaultdict(list)
        tier_agents: dict[str, list[str]] = defaultdict(list)
        age_bucket_agents: dict[tuple[int, int], list[str]] = defaultdict(list)

        for agent in self.agents:
            aid = agent.profile.agent_id
            city_agents[agent.profile.city].append(aid)
            tier_agents[agent.profile.city_tier].append(aid)
            age_bucket = (agent.profile.age // 5) * 5
            age_bucket_agents[(age_bucket, age_bucket + 5)].append(aid)

        # 为每个Agent建立连接
        for i, agent in enumerate(self.agents):
            aid = agent.profile.agent_id
            candidates: dict[str, float] = {}  # agent_id -> connection_score

            # 候选人来源：同城市 + 同等级 + 同年龄段
            candidate_set = set()
            candidate_set.update(city_agents.get(agent.profile.city, []))
            candidate_set.update(tier_agents.get(agent.profile.city_tier, []))
            age_bucket = (agent.profile.age // 5) * 5
            candidate_set.update(age_bucket_agents.get((age_bucket, age_bucket + 5), []))
            candidate_set.discard(aid)

            # 如果候选不够，随机补充
            if len(candidate_set) < avg_connections:
                others = [a.profile.agent_id for a in self.agents if a.profile.agent_id != aid]
                candidate_set.update(random.sample(others, min(avg_connections * 2, len(others))))

            # 计算连接分数
            for cid in candidate_set:
                if cid == aid:
                    continue
                peer = self._agent_map.get(cid)
                if not peer:
                    continue

                score = 0.0
                # 同城市
                if peer.profile.city == agent.profile.city:
                    score += 0.3
                # 同城市等级
                elif peer.profile.city_tier == agent.profile.city_tier:
                    score += 0.1
                # 年龄接近
                age_diff = abs(peer.profile.age - agent.profile.age)
                if age_diff < 5:
                    score += 0.15
                elif age_diff < 10:
                    score += 0.05
                # 共同兴趣
                common_interests = set(peer.profile.interests) & set(agent.profile.interests)
                score += len(common_interests) * 0.1
                # 社交影响力接近
                inf_diff = abs(peer.profile.social_influence - agent.profile.social_influence)
                if inf_diff < 0.2:
                    score += 0.1

                if score > 0.05:
                    candidates[cid] = score

            # 按分数排序，选择连接
            sorted_candidates = sorted(candidates.items(), key=lambda x: -x[1])
            target_count = min(avg_connections, len(sorted_candidates))
            # 带概率的选择：分数越高越可能被选中
            selected = []
            for cid, score in sorted_candidates:
                if random.random() < score * 1.5:  # score越高越容易选中
                    selected.append(cid)
                if len(selected) >= target_count * 2:
                    break

            # 确保至少有连接
            if not selected and sorted_candidates:
                selected = [c[0] for c in sorted_candidates[:avg_connections]]

            # 同时添加一些随机弱连接（小世界效应）
            if n > avg_connections * 2:
                weak_count = max(1, avg_connections // 3)
                others = [a.profile.agent_id for a in self.agents
                          if a.profile.agent_id != aid and a.profile.agent_id not in selected]
                if others:
                    weak_links = random.sample(others, min(weak_count, len(others)))
                    selected.extend(weak_links)

            # 去重
            selected = list(set(selected))

            agent.connections = selected
            self._social_network[aid] = selected

    # ---- SIR类信息扩散模型 ----

    def _network_propagate(
        self,
        decisions: list[AgentDecision],
        scenario: Scenario,
        round_num: int,
    ) -> list[AgentDecision]:
        """
        基于社交网络的SIR类信息扩散模型。

        模型说明：
        - 每个Agent有三种状态：Susceptible（易感）, Infected（已感染/已接受观点）, Recovered（免疫）
        - "感染" = 接受了某种决策观点
        - 高social_influence的Agent作为"超级传播者"
        - 每轮扩散，未被影响的Agent根据邻居的决策重新评估

        Args:
            decisions: 当前轮次的决策列表。
            scenario: 场景。
            round_num: 当前轮次编号。

        Returns:
            更新后的决策列表。
        """
        if not self._social_network:
            self._build_social_network()

        # 构建决策映射
        decision_map: dict[str, AgentDecision] = {
            d.agent_id: d for d in decisions
        }

        # 统计当前决策分布
        decision_counts = Counter(d.decision for d in decisions)
        total = len(decisions)

        updated_decisions = []
        for agent in self.agents:
            aid = agent.profile.agent_id
            original = decision_map.get(aid)
            if not original:
                updated_decisions.append(original)
                continue

            # 获取邻居
            neighbors = self._social_network.get(aid, [])
            if not neighbors:
                updated_decisions.append(original)
                continue

            # 统计邻居决策分布（加权）
            neighbor_decisions: dict[str, float] = defaultdict(float)
            neighbor_influencers: list[str] = []

            for nid in neighbors:
                neighbor_decision = decision_map.get(nid)
                if not neighbor_decision:
                    continue

                neighbor_agent = self._agent_map.get(nid)
                if not neighbor_agent:
                    continue

                # 权重 = 邻居的社交影响力 × 连接强度
                weight = neighbor_agent.profile.social_influence * 0.8 + 0.2

                # 意见领袖加成（social_influence > 0.8 的节点权重更高）
                if neighbor_agent.profile.social_influence > 0.8:
                    weight *= 1.5
                    neighbor_influencers.append(nid)

                neighbor_decisions[neighbor_decision.decision] += weight

            if not neighbor_decisions:
                updated_decisions.append(original)
                continue

            # 找出邻居中最主流的决策
            most_common_decision = max(neighbor_decisions, key=neighbor_decisions.get)
            total_neighbor_weight = sum(neighbor_decisions.values())
            most_common_ratio = neighbor_decisions[most_common_decision] / total_neighbor_weight

            # 决定是否改变决策
            # 条件：1) 当前决策不是邻居主流  2) 邻居主流占比 > 40%
            #       3) Agent的agreeableness（从众性）高  4) 置信度低
            should_change = (
                original.decision != most_common_decision
                and most_common_ratio > 0.4
                and agent.personality.agreeableness > 0.6
                and original.confidence < 0.7
            )

            # 意见领袖效应：即使从众性不高，高影响力邻居也能改变决策
            leader_effect = (
                len(neighbor_influencers) > 0
                and original.decision != most_common_decision
                and original.confidence < 0.6
                and random.random() < 0.3  # 30%概率被意见领袖影响
            )

            if should_change or leader_effect:
                # 衰减置信度（传播过程中信息损耗）
                decayed_confidence = max(0.3, original.confidence - round_num * 0.05)

                influenced_by = neighbor_influencers if leader_effect else ["network_propagation"]

                updated = AgentDecision(
                    agent_id=aid,
                    decision=most_common_decision,
                    confidence=decayed_confidence,
                    reasoning=f"第{round_num}轮社交传播：受网络邻居影响转向'{most_common_decision}'",
                    influenced_by=influenced_by,
                )
                updated_decisions.append(updated)
            else:
                updated_decisions.append(original)

        return updated_decisions

    # ---- 原始简单传播（保留作为备选）----

    def _propagate(
        self,
        decisions: list[AgentDecision],
        scenario: Scenario,
    ) -> list[AgentDecision]:
        """简单从众传播（兼容旧版本）。"""
        decision_counts = Counter(d.decision for d in decisions)
        most_common = decision_counts.most_common(1)[0][0]
        most_common_pct = decision_counts.most_common(1)[0][1] / len(decisions)

        updated_decisions = []
        for i, agent in enumerate(self.agents):
            original = decisions[i]
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

    # ---- 内部方法 ----

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

    # ---- LLM 驱动决策 (v2.0) ----

    def _run_llm_decision(
        self,
        scenario: Scenario,
        batch_size: int = 10,
    ) -> list[AgentDecision]:
        """
        使用 LLM（DeepSeek）进行 Agent 决策。

        内部同步执行 asyncio 事件循环。
        如果 DeepSeek 不可用，自动降级到规则引擎。
        """
        try:
            from .deepseek_adapter import get_shared_adapter
            adapter = get_shared_adapter()

            from .deepseek_adapter import MockDeepSeekAdapter, DeepSeekAdapter
            if adapter is None or isinstance(adapter, MockDeepSeekAdapter) or not isinstance(adapter, DeepSeekAdapter):
                logger.info("LLM模式启用但使用Mock适配器或适配器不可用，降级到规则引擎")
                return self._fallback_rule_decisions(scenario)

            # 运行异步事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已在事件循环中，使用 nest_asyncio 或同步降级
                    logger.warning("检测到运行中的事件循环，LLM模式下使用同步规则引擎")
                    return self._fallback_rule_decisions(scenario)
                decisions = loop.run_until_complete(
                    SimulationAgent.batch_evaluate(
                        self.agents,
                        self._build_scenario_prompt(scenario, self.agents[0]) if self.agents else scenario.description,
                        adapter,
                        batch_size=batch_size,
                    )
                )
                return decisions
            except RuntimeError:
                # 创建新事件循环
                decisions = asyncio.run(
                    SimulationAgent.batch_evaluate(
                        self.agents,
                        self._build_scenario_prompt(scenario, self.agents[0]) if self.agents else scenario.description,
                        adapter,
                        batch_size=batch_size,
                    )
                )
                return decisions
        except Exception as e:
            logger.warning("LLM决策失败: %s，降级到规则引擎", e)
            return self._fallback_rule_decisions(scenario)

    def _fallback_rule_decisions(self, scenario: Scenario) -> list[AgentDecision]:
        """降级到规则引擎决策。"""
        decisions = []
        for agent in self.agents:
            prompt = self._build_scenario_prompt(scenario, agent)
            decision = agent.evaluate(prompt)
            decisions.append(decision)
        return decisions

    async def run_async(
        self,
        scenario: Scenario,
        rounds: int = 1,
        social_propagation: bool = True,
        use_llm: bool = False,
        llm_batch_size: int = 10,
    ) -> SimulationResult:
        """
        异步执行模拟（用于FastAPI服务器）。

        与 run() 功能相同，但在 async 上下文中运行。
        LLM模式下真正异步调用DeepSeek API。
        """
        import time as _time
        start_time = _time.time()

        # Phase 1: 独立决策
        if use_llm:
            try:
                from .deepseek_adapter import get_shared_adapter
                adapter = get_shared_adapter()
                decisions = await SimulationAgent.batch_evaluate(
                    self.agents,
                    self._build_scenario_prompt(scenario, self.agents[0]) if self.agents else scenario.description,
                    adapter,
                    batch_size=llm_batch_size,
                )
            except Exception as e:
                logger.warning("LLM异步决策失败: %s，降级到规则引擎", e)
                decisions = self._fallback_rule_decisions(scenario)
        else:
            decisions = []
            for agent in self.agents:
                prompt = self._build_scenario_prompt(scenario, agent)
                decision = agent.evaluate(prompt)
                decisions.append(decision)

        # Phase 2: 社交传播
        if social_propagation and rounds > 1:
            if not self._network_built:
                self._build_social_network()
                self._network_built = True

            for round_num in range(1, rounds):
                decisions = self._network_propagate(decisions, scenario, round_num)

        # Phase 3: 汇聚结果
        aggregate = self._aggregate(decisions, scenario)
        segments = self._segment_analysis(decisions, scenario)

        elapsed = (_time.time() - start_time) * 1000

        return SimulationResult(
            scenario=scenario,
            population_size=len(self.agents),
            decisions=decisions,
            aggregate=aggregate,
            segments=segments,
            execution_time_ms=elapsed,
        )

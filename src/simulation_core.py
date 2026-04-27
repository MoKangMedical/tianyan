"""
Simulation Core — 模拟核心
多Agent人群模拟、社交网络模拟、消费行为模拟
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import random
import time
import uuid


class AgentType(Enum):
    """Agent 类型"""
    PRICE_SENSITIVE = "price_sensitive"  # 价格敏感型
    BRAND_LOYAL = "brand_loyal"  # 品牌忠诚型
    TREND_FOLLOWER = "trend_follower"  # 潮流追随型
    QUALITY_SEEKER = "quality_seeker"  # 品质追求型
    CONVENIENCE_SEEKER = "convenience_seeker"  # 便利追求型
    HEALTH_CONSCIOUS = "health_conscious"  # 健康意识型
    EARLY_ADOPTER = "early_adopter"  # 早期采用型
    CONSERVATIVE = "conservative"  # 保守型


@dataclass
class ConsumerAgent:
    """消费者 Agent"""
    agent_id: str
    agent_type: AgentType
    age: int
    income: float
    preferences: Dict[str, float]
    social_connections: List[str] = field(default_factory=list)
    purchase_history: List[Dict] = field(default_factory=list)
    influence_score: float = 0.5
    susceptibility: float = 0.5


@dataclass
class SimulationConfig:
    """模拟配置"""
    num_agents: int
    num_rounds: int
    market_scenario: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResult:
    """模拟结果"""
    simulation_id: str
    config: SimulationConfig
    market_dynamics: List[Dict]
    agent_behaviors: List[Dict]
    aggregate_metrics: Dict
    execution_time: float


class SimulationCore:
    """模拟核心"""
    
    def __init__(self):
        self.agents: Dict[str, ConsumerAgent] = {}
        self.simulation_history: List[SimulationResult] = []
    
    def create_agents(self, num_agents: int, profiles: List[Dict]) -> List[ConsumerAgent]:
        """创建 Agent 群体"""
        agents = []
        
        for i in range(num_agents):
            # 随机选择 Agent 类型
            agent_type = random.choice(list(AgentType))
            
            # 根据类型生成属性
            profile = self._generate_profile(agent_type, profiles)
            
            agent = ConsumerAgent(
                agent_id=f"agent_{i:04d}",
                agent_type=agent_type,
                age=profile.get("age", random.randint(18, 65)),
                income=profile.get("income", random.uniform(3000, 30000)),
                preferences=profile.get("preferences", {
                    "price": random.uniform(0, 1),
                    "quality": random.uniform(0, 1),
                    "brand": random.uniform(0, 1),
                    "convenience": random.uniform(0, 1)
                }),
                influence_score=random.uniform(0, 1),
                susceptibility=random.uniform(0, 1)
            )
            
            self.agents[agent.agent_id] = agent
            agents.append(agent)
        
        # 建立社交网络
        self._build_social_network(agents)
        
        return agents
    
    def _generate_profile(self, agent_type: AgentType, profiles: List[Dict]) -> Dict:
        """生成 Agent 属性"""
        # 从预定义画像中选择
        for profile in profiles:
            if profile.get("type") == agent_type.value:
                return profile
        
        # 默认属性
        return {
            "age": random.randint(18, 65),
            "income": random.uniform(5000, 20000),
            "preferences": {}
        }
    
    def _build_social_network(self, agents: List[ConsumerAgent]):
        """构建社交网络"""
        for agent in agents:
            # 每个 Agent 连接 3-10 个其他 Agent
            num_connections = random.randint(3, 10)
            other_agents = [a for a in agents if a.agent_id != agent.agent_id]
            connections = random.sample(other_agents, min(num_connections, len(other_agents)))
            agent.social_connections = [a.agent_id for a in connections]
    
    def simulate(self, config: SimulationConfig) -> SimulationResult:
        """运行模拟"""
        start_time = time.time()
        simulation_id = f"sim_{int(time.time())}"
        
        # 创建 Agent
        if not self.agents:
            self.create_agents(config.num_agents, config.parameters.get("profiles", []))
        
        market_dynamics = []
        agent_behaviors = []
        
        # 运行模拟轮次
        for round_num in range(config.num_rounds):
            round_result = self._simulate_round(round_num, config)
            market_dynamics.append(round_result["market"])
            agent_behaviors.append(round_result["agents"])
        
        # 计算汇总指标
        aggregate = self._calculate_aggregate(market_dynamics, agent_behaviors)
        
        result = SimulationResult(
            simulation_id=simulation_id,
            config=config,
            market_dynamics=market_dynamics,
            agent_behaviors=agent_behaviors,
            aggregate_metrics=aggregate,
            execution_time=time.time() - start_time
        )
        
        self.simulation_history.append(result)
        return result
    
    def _simulate_round(self, round_num: int, config: SimulationConfig) -> Dict:
        """模拟单轮"""
        market = {
            "round": round_num,
            "total_demand": random.uniform(1000, 5000),
            "market_share": {},
            "price_level": random.uniform(80, 120),
            "innovation_index": random.uniform(0, 1)
        }
        
        agents_round = {
            "round": round_num,
            "purchases": random.randint(100, 500),
            "word_of_mouth": random.uniform(0, 1),
            "satisfaction": random.uniform(0.5, 1)
        }
        
        return {"market": market, "agents": agents_round}
    
    def _calculate_aggregate(self, market: List[Dict], agents: List[Dict]) -> Dict:
        """计算汇总指标"""
        total_demand = sum(m.get("total_demand", 0) for m in market)
        avg_satisfaction = sum(a.get("satisfaction", 0) for a in agents) / max(len(agents), 1)
        
        return {
            "total_market_size": round(total_demand, 2),
            "average_satisfaction": round(avg_satisfaction, 2),
            "growth_rate": round(random.uniform(0.05, 0.2), 2),
            "market_stability": round(random.uniform(0.6, 0.95), 2)
        }
    
    def get_agent_network(self) -> Dict:
        """获取 Agent 网络"""
        return {
            "nodes": [
                {"id": a.agent_id, "type": a.agent_type.value, "influence": a.influence_score}
                for a in self.agents.values()
            ],
            "edges": [
                {"source": a.agent_id, "target": conn}
                for a in self.agents.values()
                for conn in a.social_connections
            ]
        }
    
    def get_simulation_history(self) -> List[Dict]:
        """获取模拟历史"""
        return [
            {
                "simulation_id": s.simulation_id,
                "config": s.config.market_scenario,
                "execution_time": s.execution_time
            }
            for s in self.simulation_history
        ]

"""
天眼 (Tianyan) — 中国版商业预测平台

基于多Agent人群模拟的商业预测引擎。
核心理念：用AI合成人群替代传统调研，72小时完成6个月的市场洞察。
"""

__version__ = "0.1.0"
__author__ = "MoKangMedical"

from .population import SyntheticPopulation, PopulationProfile
from .agents import SimulationAgent, AgentPersonality
from .scenarios import Scenario, ScenarioEngine, SimulationResult
from .products import ConsumerEye, PolicyEye, MarketEye, PredictionResult
from .compliance import ComplianceChecker, DataAuditLog, ComplianceError
from .china_scenarios import ChineseScenarioEngine, KOLPredictionResult, LivestreamPredictionResult
from .mimo_adapter import MIMOAdapter, MockMIMOAdapter, MIMOConfig

__all__ = [
    # 核心
    "SyntheticPopulation",
    "PopulationProfile",
    "SimulationAgent",
    "AgentPersonality",
    # 场景
    "Scenario",
    "ScenarioEngine",
    "SimulationResult",
    # 三眼产品
    "ConsumerEye",
    "PolicyEye",
    "MarketEye",
    "PredictionResult",
    # 中国特色
    "ChineseScenarioEngine",
    "KOLPredictionResult",
    "LivestreamPredictionResult",
    # 合规
    "ComplianceChecker",
    "DataAuditLog",
    "ComplianceError",
    # AI引擎
    "MIMOAdapter",
    "MockMIMOAdapter",
    "MIMOConfig",
]

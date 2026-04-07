"""
天眼 (Tianyan) — 中国版商业预测平台

基于多Agent人群模拟的商业预测引擎。
核心理念：用AI合成人群替代传统调研，72小时完成6个月的市场洞察。
"""

__version__ = "0.1.0"
__author__ = "MoKangMedical"

from .population import SyntheticPopulation, PopulationProfile
from .agents import SimulationAgent, AgentPersonality
from .scenarios import Scenario, ScenarioEngine
from .products import ConsumerEye, PolicyEye, MarketEye
from .compliance import ComplianceChecker, DataAuditLog

__all__ = [
    "SyntheticPopulation",
    "PopulationProfile",
    "SimulationAgent",
    "AgentPersonality",
    "Scenario",
    "ScenarioEngine",
    "ConsumerEye",
    "PolicyEye",
    "MarketEye",
    "ComplianceChecker",
    "DataAuditLog",
]

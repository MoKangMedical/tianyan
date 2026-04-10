"""
天眼 (Tianyan) — 中国版商业预测平台

基于多Agent人群模拟的商业预测引擎。
核心理念：用AI合成人群替代传统调研，72小时完成6个月的市场洞察。
"""

__version__ = "0.3.0"
__author__ = "MoKangMedical"

from .population import SyntheticPopulation, PopulationProfile
from .agents import SimulationAgent, AgentPersonality, AgentDecision
from .scenarios import Scenario, ScenarioEngine, SimulationResult
from .products import ConsumerEye, PolicyEye, MarketEye, PredictionResult
from .compliance import ComplianceChecker, DataAuditLog, ComplianceError
from .china_scenarios import ChineseScenarioEngine, KOLPredictionResult, LivestreamPredictionResult
from .mimo_adapter import MIMOAdapter, MockMIMOAdapter, MIMOConfig
from .report_generator import McKinseyReportGenerator, McKinseyReport, ReportSection
from .persistence import PersistenceLayer, SimulationRun
from .realtime_feeds import RealtimeFeedManager, StockFeedAdapter, NewsFeedAdapter, PolicyFeedAdapter
from .industry_templates import (
    get_template, list_templates, get_all_template_keys,
    IndustryTemplate, TEMPLATES,
    GLP1_WEIGHT_LOSS, HEALTH_SUPPLEMENT, SKINCARE_LAUNCH,
    TELEHEALTH_PLATFORM, MALE_HEALTH,
)

__all__ = [
    # 核心
    "SyntheticPopulation",
    "PopulationProfile",
    "SimulationAgent",
    "AgentPersonality",
    "AgentDecision",
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
    # 报告生成
    "McKinseyReportGenerator",
    "McKinseyReport",
    "ReportSection",
    # 持久化
    "PersistenceLayer",
    "SimulationRun",
    # 实时数据
    "RealtimeFeedManager",
    "StockFeedAdapter",
    "NewsFeedAdapter",
    "PolicyFeedAdapter",
    # 行业模板
    "get_template",
    "list_templates",
    "get_all_template_keys",
    "IndustryTemplate",
    "TEMPLATES",
    "GLP1_WEIGHT_LOSS",
    "HEALTH_SUPPLEMENT",
    "SKINCARE_LAUNCH",
    "TELEHEALTH_PLATFORM",
    "MALE_HEALTH",
]

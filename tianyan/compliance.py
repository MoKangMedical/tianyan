"""
合规层 (Compliance Layer)

中国运营合规检查：
- PIPL（个人信息保护法）合规
- 数据安全法合规
- 算法推荐合规
- 内容安全审查
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuditEntry:
    """审计日志条目。"""
    timestamp: float
    action: str
    category: str
    details: dict[str, Any]
    passed: bool
    reason: str = ""


class DataAuditLog:
    """数据审计日志。"""

    def __init__(self):
        self.entries: list[AuditEntry] = []

    def log(
        self,
        action: str,
        category: str,
        details: dict[str, Any],
        passed: bool,
        reason: str = "",
    ):
        self.entries.append(AuditEntry(
            timestamp=time.time(),
            action=action,
            category=category,
            details=details,
            passed=passed,
            reason=reason,
        ))

    def get_failed(self) -> list[AuditEntry]:
        return [e for e in self.entries if not e.passed]

    def to_json(self) -> str:
        return json.dumps([
            {
                "timestamp": e.timestamp,
                "action": e.action,
                "category": e.category,
                "passed": e.passed,
                "reason": e.reason,
            }
            for e in self.entries
        ], ensure_ascii=False, indent=2)


class ComplianceChecker:
    """
    合规检查器。

    三层防护：
    1. 输入检查：场景内容是否触碰红线
    2. 数据检查：是否使用真实个人信息
    3. 输出检查：结果是否需要脱敏
    """

    # 政治敏感词（不可触碰的领域）
    POLITICAL_RED_LINES = [
        "选举", "投票", "政党", "政治体制", "人事变动",
        "换届", "领导人", "政府更迭", "政权",
        "群体事件", "社会动荡", "抗议", "示威",
        "台独", "港独", "疆独", "藏独",
        "六四", "法轮", "民运",
    ]

    # 禁止的模拟场景类型
    FORBIDDEN_SCENARIOS = [
        "election",        # 选举预测
        "political_poll",  # 政治民调
        "regime_change",   # 政权更迭
        "social_unrest",   # 社会动荡
        "military",        # 军事行动
    ]

    def __init__(self):
        self.audit_log = DataAuditLog()
        self._check_count = 0

    def check_scenario(self, category: str, parameters: dict[str, Any]) -> bool:
        """
        检查场景是否合规。

        Raises:
            ComplianceError: 场景不合规时抛出。
        """
        self._check_count += 1

        # 检查场景类别
        if category in self.FORBIDDEN_SCENARIOS:
            self.audit_log.log("scenario_check", category, parameters, False, f"禁止的场景类别: {category}")
            raise ComplianceError(f"场景类别 '{category}' 被禁止（合规红线）")

        # 检查参数中的敏感词
        text = json.dumps(parameters, ensure_ascii=False)
        for red_word in self.POLITICAL_RED_LINES:
            if red_word in text:
                self.audit_log.log("scenario_check", category, parameters, False, f"包含敏感词: {red_word}")
                raise ComplianceError(f"场景包含敏感词 '{red_word}'（合规红线）")

        self.audit_log.log("scenario_check", category, parameters, True)
        return True

    def check_policy_scenario(self, policy_name: str, policy_category: str) -> bool:
        """专门检查政策模拟场景。"""
        allowed_categories = [
            "economic",      # 经济政策
            "healthcare",    # 医疗政策
            "education",     # 教育政策
            "environmental", # 环保政策
            "tax",           # 税收政策
            "housing",       # 住房政策
            "social_welfare", # 社会福利
            "industry",      # 产业政策
        ]

        if policy_category not in allowed_categories:
            raise ComplianceError(
                f"政策类别 '{policy_category}' 不在允许范围内。"
                f"允许的类别: {', '.join(allowed_categories)}"
            )

        # 检查政策名称中的敏感词
        for red_word in self.POLITICAL_RED_LINES:
            if red_word in policy_name:
                raise ComplianceError(f"政策名称包含敏感词 '{red_word}'")

        self.audit_log.log("policy_check", policy_category, {"policy_name": policy_name}, True)
        return True

    def check_data_usage(self, data_source: str, contains_pii: bool) -> bool:
        """
        检查数据使用是否合规（PIPL）。

        核心原则：
        - 天眼平台100%使用合成数据
        - 不存储、不处理任何真实个人信息
        """
        if contains_pii:
            self.audit_log.log("data_check", "PIPL", {"source": data_source}, False, "包含个人信息")
            raise ComplianceError("检测到真实个人信息，天眼平台仅使用合成数据")

        self.audit_log.log("data_check", "PIPL", {"source": data_source}, True)
        return True

    def sanitize_output(self, output: dict[str, Any]) -> dict[str, Any]:
        """对输出结果进行脱敏处理。"""
        sanitized = {}
        for key, value in output.items():
            if isinstance(value, str):
                # 脱敏处理：去除可能的个人信息模式
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_output(value)
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_string(self, text: str) -> str:
        """脱敏字符串（移除潜在的个人信息模式）。"""
        import re
        # 手机号脱敏
        text = re.sub(r'1[3-9]\d{9}', '1****', text)
        # 身份证脱敏
        text = re.sub(r'\d{17}[\dXx]', '****', text)
        # 姓名脱敏（简单模式）
        text = re.sub(r'[\u4e00-\u9fa5]{2,3}（先生|女士）', '*（脱敏）', text)
        return text


class ComplianceError(Exception):
    """合规异常。"""
    pass

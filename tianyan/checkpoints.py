"""
决策检查点模块 (Decision Checkpoints)

提供：
1. 参数确认与校验（预测前）
2. 预览模式（API批量操作前）
3. Dry-run模式（不执行，只预估资源消耗）
4. 操作审计日志（谁在什么时候发起了什么操作）
"""

from __future__ import annotations

import time
import json
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CheckpointResult:
    """检查点结果。"""
    approved: bool
    checkpoint_name: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    preview: dict[str, Any] = field(default_factory=dict)
    estimated_cost: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "checkpoint_name": self.checkpoint_name,
            "warnings": self.warnings,
            "errors": self.errors,
            "preview": self.preview,
            "estimated_cost": self.estimated_cost,
        }


@dataclass
class OperationAudit:
    """操作审计记录。"""
    operation: str
    parameters: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    approved: bool = True
    dry_run: bool = False
    checkpoint_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "parameters": self.parameters,
            "timestamp": self.timestamp,
            "approved": self.approved,
            "dry_run": self.dry_run,
            "checkpoint_results": self.checkpoint_results,
        }


# ============================================================
# 参数校验检查点
# ============================================================

def validate_population_params(
    size: int,
    region: str = "全国",
    age_range: tuple[int, int] = (18, 65),
    **kwargs,
) -> CheckpointResult:
    """校验人群生成参数。"""
    warnings = []
    errors = []

    if size > 10000:
        warnings.append(f"人群规模 {size} 较大，生成时间可能超过30秒")
    if size > 50000:
        errors.append(f"人群规模 {size} 超出上限(50000)")
    if age_range[0] < 0 or age_range[1] > 100:
        errors.append(f"年龄范围 {age_range} 超出合理区间(0-100)")
    if age_range[0] >= age_range[1]:
        errors.append(f"年龄范围无效: 下限 {age_range[0]} >= 上限 {age_range[1]}")

    preview = {
        "population_size": size,
        "region": region,
        "age_range": list(age_range),
        "estimated_memory_mb": size * 0.02,  # 粗估
        "estimated_time_seconds": size * 0.001,
    }

    return CheckpointResult(
        approved=len(errors) == 0,
        checkpoint_name="population_params",
        warnings=warnings,
        errors=errors,
        preview=preview,
        estimated_cost={
            "memory_mb": round(size * 0.02, 1),
            "time_seconds": round(size * 0.001, 2),
        },
    )


def validate_prediction_params(
    product_name: str,
    price: float,
    population_size: int,
    sub_operations: list[str] | None = None,
    **kwargs,
) -> CheckpointResult:
    """校验预测参数（预测前确认）。"""
    warnings = []
    errors = []

    if not product_name or not product_name.strip():
        errors.append("产品名称不能为空")
    if price <= 0:
        errors.append(f"价格必须大于0，当前值: {price}")
    if price > 1000000:
        warnings.append(f"价格 ¥{price:,.0f} 异常偏高，请确认")
    if population_size > 20000:
        warnings.append(f"人群规模 {population_size} 较大，完整预测可能需要1-2分钟")

    sub_ops = sub_operations or []
    total_sub_ops = len(sub_ops)

    preview = {
        "product_name": product_name,
        "price": price,
        "population_size": population_size,
        "sub_operations": sub_ops,
        "total_sub_operations": total_sub_ops,
    }

    # 估算资源消耗
    est_time = population_size * 0.002 * max(1, total_sub_ops)
    est_memory = population_size * 0.03 + total_sub_ops * 5

    return CheckpointResult(
        approved=len(errors) == 0,
        checkpoint_name="prediction_params",
        warnings=warnings,
        errors=errors,
        preview=preview,
        estimated_cost={
            "memory_mb": round(est_memory, 1),
            "time_seconds": round(est_time, 2),
            "sub_operations": total_sub_ops,
        },
    )


def validate_batch_operation(
    operations: list[dict[str, Any]],
    max_operations: int = 10,
) -> CheckpointResult:
    """校验批量操作（批量操作前预览）。"""
    warnings = []
    errors = []

    if len(operations) == 0:
        errors.append("批量操作列表为空")
    if len(operations) > max_operations:
        errors.append(f"批量操作数 {len(operations)} 超过上限 {max_operations}")

    total_pop_size = sum(op.get("population_size", 1000) for op in operations)
    if total_pop_size > 50000:
        warnings.append(f"总人群规模 {total_pop_size} 较大，建议分批执行")

    op_types = [op.get("type", "unknown") for op in operations]
    preview = {
        "operation_count": len(operations),
        "operation_types": op_types,
        "total_population_size": total_pop_size,
        "operations_summary": [
            {
                "index": i,
                "type": op.get("type", "unknown"),
                "product": op.get("product_name", "未知"),
                "population_size": op.get("population_size", 1000),
            }
            for i, op in enumerate(operations)
        ],
    }

    est_time = total_pop_size * 0.002 * len(operations)
    return CheckpointResult(
        approved=len(errors) == 0,
        checkpoint_name="batch_operation",
        warnings=warnings,
        errors=errors,
        preview=preview,
        estimated_cost={
            "total_population_size": total_pop_size,
            "time_seconds": round(est_time, 2),
            "operations_count": len(operations),
        },
    )


# ============================================================
# Dry-run 预览
# ============================================================

def dry_run_population(size: int, region: str = "全国", **kwargs) -> dict[str, Any]:
    """Dry-run: 预览人群生成（不实际执行）。"""
    cp = validate_population_params(size, region, **kwargs)
    return {
        "mode": "dry_run",
        "operation": "create_population",
        "checkpoint": cp.to_dict(),
        "will_execute": cp.approved,
        "message": f"将生成 {size} 人的合成人群（地区: {region}）" if cp.approved else "参数校验未通过",
    }


def dry_run_prediction(
    product_name: str,
    price: float,
    population_size: int,
    include_kol: bool = False,
    include_livestream: bool = False,
    include_seeding: bool = False,
    **kwargs,
) -> dict[str, Any]:
    """Dry-run: 预览预测流程（不实际执行）。"""
    sub_ops = ["消费眼(产品上市预测)", "消费眼(定价优化)"]
    if include_kol:
        sub_ops.extend(["KOL效果预测(头部)", "KOL效果预测(垂类)", "KOL效果预测(素人)"])
    if include_livestream:
        sub_ops.append("直播带货预测")
    if include_seeding:
        sub_ops.append("小红书种草预测")
    sub_ops.append("电商渠道优化")

    cp = validate_prediction_params(
        product_name, price, population_size,
        sub_operations=sub_ops,
    )

    return {
        "mode": "dry_run",
        "operation": "full_prediction",
        "checkpoint": cp.to_dict(),
        "will_execute": cp.approved,
        "message": (
            f"将对「{product_name}」(¥{price:,.0f}) 执行 {len(sub_ops)} 项子操作，"
            f"人群规模 {population_size} 人"
        ) if cp.approved else "参数校验未通过",
    }


# ============================================================
# 审计日志
# ============================================================

class AuditLog:
    """操作审计日志（内存版，生产环境应持久化）。"""

    def __init__(self, max_entries: int = 10000):
        self._logs: list[OperationAudit] = []
        self._max = max_entries

    def record(self, audit: OperationAudit) -> None:
        self._logs.append(audit)
        if len(self._logs) > self._max:
            self._logs = self._logs[-self._max:]

    def recent(self, n: int = 20) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._logs[-n:]]

    def count(self) -> int:
        return len(self._logs)

    def stats(self) -> dict[str, Any]:
        total = len(self._logs)
        if total == 0:
            return {"total": 0}
        dry_runs = sum(1 for a in self._logs if a.dry_run)
        rejections = sum(1 for a in self._logs if not a.approved)
        ops = {}
        for a in self._logs:
            ops[a.operation] = ops.get(a.operation, 0) + 1
        return {
            "total": total,
            "dry_runs": dry_runs,
            "rejections": rejections,
            "by_operation": ops,
        }


# 全局审计日志实例
audit_log = AuditLog()

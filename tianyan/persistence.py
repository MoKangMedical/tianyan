"""
数据持久化层 — SQLite存储模拟历史

存储：
- SimulationRun：每次模拟的参数和结果
- PredictionResult：预测结果
- AuditLog：合规审计日志
- DataSourceCache：数据源缓存
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


DEFAULT_DB_PATH = "/root/tianyan/data/tianyan.db"


@dataclass
class SimulationRun:
    """模拟运行记录。"""
    id: Optional[int]
    scenario_name: str
    scenario_type: str
    population_size: int
    population_params: dict[str, Any]
    parameters: dict[str, Any]
    result_summary: dict[str, Any]
    confidence: float
    execution_time_ms: float
    created_at: str
    report_md: str = ""
    report_json: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type,
            "population_size": self.population_size,
            "population_params": self.population_params,
            "parameters": self.parameters,
            "result_summary": self.result_summary,
            "confidence": self.confidence,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at,
            "report_md": self.report_md[:500] + "..." if len(self.report_md) > 500 else self.report_md,
        }


class PersistenceLayer:
    """SQLite持久化层。"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表。"""
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_name TEXT NOT NULL,
                    scenario_type TEXT NOT NULL,
                    population_size INTEGER NOT NULL,
                    population_params TEXT NOT NULL DEFAULT '{}',
                    parameters TEXT NOT NULL DEFAULT '{}',
                    result_summary TEXT NOT NULL DEFAULT '{}',
                    confidence REAL NOT NULL DEFAULT 0.0,
                    execution_time_ms REAL NOT NULL DEFAULT 0.0,
                    report_md TEXT DEFAULT '',
                    report_json TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS prediction_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simulation_id INTEGER,
                    product TEXT NOT NULL,
                    scenario_name TEXT NOT NULL,
                    key_metrics TEXT NOT NULL DEFAULT '{}',
                    segments TEXT NOT NULL DEFAULT '{}',
                    recommendations TEXT NOT NULL DEFAULT '[]',
                    confidence REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (simulation_id) REFERENCES simulation_runs(id)
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    category TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '{}',
                    passed INTEGER NOT NULL DEFAULT 1,
                    reason TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS data_source_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    query_key TEXT NOT NULL,
                    data TEXT NOT NULL,
                    quality TEXT DEFAULT 'unverified',
                    confidence REAL DEFAULT 0.5,
                    expires_at REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(source_name, query_key)
                );

                CREATE INDEX IF NOT EXISTS idx_sim_type ON simulation_runs(scenario_type);
                CREATE INDEX IF NOT EXISTS idx_sim_created ON simulation_runs(created_at);
                CREATE INDEX IF NOT EXISTS idx_pred_product ON prediction_results(product);
                CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
                CREATE INDEX IF NOT EXISTS idx_cache_source ON data_source_cache(source_name);
            """)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ================================================================
    # SimulationRun CRUD
    # ================================================================

    def save_simulation(
        self,
        scenario_name: str,
        scenario_type: str,
        population_size: int,
        population_params: dict,
        parameters: dict,
        result_summary: dict,
        confidence: float,
        execution_time_ms: float,
        report_md: str = "",
        report_json: str = "",
    ) -> int:
        """保存模拟运行记录，返回ID。"""
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO simulation_runs
                   (scenario_name, scenario_type, population_size, population_params,
                    parameters, result_summary, confidence, execution_time_ms,
                    report_md, report_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    scenario_name,
                    scenario_type,
                    population_size,
                    json.dumps(population_params, ensure_ascii=False),
                    json.dumps(parameters, ensure_ascii=False),
                    json.dumps(result_summary, ensure_ascii=False),
                    confidence,
                    execution_time_ms,
                    report_md,
                    report_json,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            return cursor.lastrowid

    def get_simulation(self, sim_id: int) -> Optional[SimulationRun]:
        """获取单次模拟记录。"""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM simulation_runs WHERE id = ?", (sim_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_simulation(row)

    def list_simulations(
        self,
        scenario_type: str = "",
        limit: int = 20,
        offset: int = 0,
    ) -> list[SimulationRun]:
        """列出模拟记录。"""
        with self._conn() as conn:
            if scenario_type:
                rows = conn.execute(
                    "SELECT * FROM simulation_runs WHERE scenario_type = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (scenario_type, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM simulation_runs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
            return [self._row_to_simulation(r) for r in rows]

    def stats(self) -> dict[str, Any]:
        """get_stats的别名（兼容server.py v2.0）。"""
        return self.get_stats()

    def list_runs(self, limit: int = 50) -> list[dict]:
        """list_simulations的别名，返回字典列表。"""
        runs = self.list_simulations(limit=limit)
        return [r.to_dict() for r in runs]

    def get_run(self, run_id: int):
        """get_simulation的别名。"""
        return self.get_simulation(run_id)

    def get_stats(self) -> dict[str, Any]:
        """获取平台统计。"""
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM simulation_runs").fetchone()[0]
            avg_conf = conn.execute("SELECT AVG(confidence) FROM simulation_runs").fetchone()[0] or 0
            types = conn.execute(
                "SELECT scenario_type, COUNT(*) as cnt FROM simulation_runs GROUP BY scenario_type ORDER BY cnt DESC"
            ).fetchall()
            recent = conn.execute(
                "SELECT created_at FROM simulation_runs ORDER BY created_at DESC LIMIT 1"
            ).fetchone()

            return {
                "total_simulations": total,
                "avg_confidence": round(avg_conf, 3),
                "scenario_types": {r[0]: r[1] for r in types},
                "last_simulation": recent[0] if recent else None,
            }

    def _row_to_simulation(self, row) -> SimulationRun:
        return SimulationRun(
            id=row["id"],
            scenario_name=row["scenario_name"],
            scenario_type=row["scenario_type"],
            population_size=row["population_size"],
            population_params=json.loads(row["population_params"]),
            parameters=json.loads(row["parameters"]),
            result_summary=json.loads(row["result_summary"]),
            confidence=row["confidence"],
            execution_time_ms=row["execution_time_ms"],
            created_at=row["created_at"],
            report_md=row["report_md"],
            report_json=row["report_json"],
        )
    
    # to_dict别名（在SimulationRun上添加）

    # ================================================================
    # PredictionResult CRUD
    # ================================================================

    def save_prediction(
        self,
        simulation_id: int,
        product: str,
        scenario_name: str,
        key_metrics: dict,
        segments: dict,
        recommendations: list,
        confidence: float,
    ) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO prediction_results
                   (simulation_id, product, scenario_name, key_metrics,
                    segments, recommendations, confidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    simulation_id, product, scenario_name,
                    json.dumps(key_metrics, ensure_ascii=False),
                    json.dumps(segments, ensure_ascii=False),
                    json.dumps(recommendations, ensure_ascii=False),
                    confidence,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            return cursor.lastrowid

    def list_predictions(self, product: str = "", limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            if product:
                rows = conn.execute(
                    "SELECT * FROM prediction_results WHERE product = ? ORDER BY created_at DESC LIMIT ?",
                    (product, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM prediction_results ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    # ================================================================
    # AuditLog
    # ================================================================

    def save_audit(
        self, action: str, category: str, details: dict, passed: bool, reason: str = ""
    ):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO audit_logs (action, category, details, passed, reason, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    action, category,
                    json.dumps(details, ensure_ascii=False),
                    1 if passed else 0, reason,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

    def get_failed_audits(self, limit: int = 100) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_logs WHERE passed = 0 ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ================================================================
    # DataSourceCache
    # ================================================================

    def get_cached_data(self, source_name: str, query_key: str) -> Optional[Any]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT data FROM data_source_cache WHERE source_name = ? AND query_key = ? AND expires_at > ?",
                (source_name, query_key, time.time()),
            ).fetchone()
            if row:
                return json.loads(row["data"])
            return None

    def set_cached_data(
        self, source_name: str, query_key: str, data: Any,
        quality: str = "unverified", confidence: float = 0.5, ttl_hours: int = 24
    ):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO data_source_cache
                   (source_name, query_key, data, quality, confidence, expires_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    source_name, query_key,
                    json.dumps(data, ensure_ascii=False),
                    quality, confidence,
                    time.time() + ttl_hours * 3600,
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

    def clear_expired_cache(self) -> int:
        with self._conn() as conn:
            cursor = conn.execute(
                "DELETE FROM data_source_cache WHERE expires_at <= ?", (time.time(),)
            )
            return cursor.rowcount

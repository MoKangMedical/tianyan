"""
报告生成器 — 麦肯锡级商业分析报告

自动生成结构化的商业分析报告，包含：
- 执行摘要
- 市场分析
- 竞争格局
- 消费者洞察
- 战略建议
- 风险评估

每个结论标注数据来源和置信度。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .scenarios import SimulationResult
from .products import PredictionResult


@dataclass
class ReportSection:
    """报告章节。"""
    title: str
    content: str
    data_sources: list[str] = field(default_factory=list)
    confidence: float = 0.8
    subsections: list[ReportSection] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "title": self.title,
            "content": self.content,
            "data_sources": self.data_sources,
            "confidence": self.confidence,
        }
        if self.subsections:
            d["subsections"] = [s.to_dict() for s in self.subsections]
        return d


@dataclass
class McKinseyReport:
    """麦肯锡格式报告。"""
    title: str
    report_type: str  # market_entry / competitive / product_launch
    created_at: str
    executive_summary: str
    sections: list[ReportSection]
    key_findings: list[str]
    recommendations: list[str]
    risks: list[str]
    confidence_score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """生成Markdown格式报告。"""
        lines = [
            f"# {self.title}",
            "",
            f"> 报告类型：{self._type_label()} | 生成时间：{self.created_at}",
            f"> 综合置信度：{self.confidence_score:.0%}",
            "",
            "---",
            "",
            "## 执行摘要",
            "",
            self.executive_summary,
            "",
        ]

        for section in self.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
            if section.data_sources:
                lines.append(f"*数据来源：{', '.join(section.data_sources)}*")
                lines.append(f"*置信度：{section.confidence:.0%}*")
                lines.append("")
            for sub in section.subsections:
                lines.append(f"### {sub.title}")
                lines.append("")
                lines.append(sub.content)
                lines.append("")

        lines.append("## 关键发现")
        lines.append("")
        for i, finding in enumerate(self.key_findings, 1):
            lines.append(f"{i}. {finding}")
        lines.append("")

        lines.append("## 战略建议")
        lines.append("")
        for i, rec in enumerate(self.recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

        lines.append("## 风险评估")
        lines.append("")
        for risk in self.risks:
            lines.append(f"- ⚠️ {risk}")
        lines.append("")

        lines.append("---")
        lines.append("*本报告由天眼(Tianyan)合成人群模拟引擎自动生成*")

        return "\n".join(lines)

    def to_json(self) -> str:
        """生成JSON格式报告（方便前端渲染）。"""
        return json.dumps({
            "title": self.title,
            "report_type": self.report_type,
            "created_at": self.created_at,
            "executive_summary": self.executive_summary,
            "sections": [s.to_dict() for s in self.sections],
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "risks": self.risks,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata,
        }, ensure_ascii=False, indent=2)

    def _type_label(self) -> str:
        labels = {
            "market_entry": "市场进入策略",
            "competitive": "竞争格局分析",
            "product_launch": "产品上市预测",
            "pricing": "定价策略优化",
            "channel": "渠道策略",
        }
        return labels.get(self.report_type, self.report_type)


class McKinseyReportGenerator:
    """
    麦肯锡级报告生成器。

    基于模拟结果自动生成结构化商业分析报告。
    """

    def generate_product_launch_report(
        self,
        product_name: str,
        simulation_result: SimulationResult,
        prediction_result: Optional[PredictionResult] = None,
        market_data: dict[str, Any] = None,
    ) -> McKinseyReport:
        """生成产品上市预测报告。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        agg = simulation_result.aggregate
        segments = simulation_result.segments

        # 执行摘要
        purchase_intent = agg.get("purchase_intent", 0)
        confidence = agg.get("avg_confidence", 0)
        exec_summary = self._product_exec_summary(
            product_name, purchase_intent, confidence, segments
        )

        # 市场分析章节
        market_section = ReportSection(
            title="市场分析",
            content=self._market_analysis_content(market_data or {}),
            data_sources=["国家统计局", "行业研报"],
            confidence=0.75,
        )

        # 消费者洞察章节
        consumer_section = self._consumer_insights_section(simulation_result)

        # 竞争格局章节
        competition_section = ReportSection(
            title="竞争格局",
            content=self._competition_content(product_name, market_data or {}),
            data_sources=["公开财报", "行业研报"],
            confidence=0.7,
        )

        # 渠道分析章节
        channel_section = self._channel_analysis_section(segments)

        # 关键发现
        key_findings = self._extract_key_findings(simulation_result, product_name)

        # 建议
        recommendations = self._generate_recommendations(
            purchase_intent, confidence, segments, product_name
        )

        # 风险
        risks = self._assess_risks(purchase_intent, confidence, product_name)

        return McKinseyReport(
            title=f"{product_name} — 产品上市预测报告",
            report_type="product_launch",
            created_at=now,
            executive_summary=exec_summary,
            sections=[market_section, consumer_section, competition_section, channel_section],
            key_findings=key_findings,
            recommendations=recommendations,
            risks=risks,
            confidence_score=confidence,
            metadata={
                "population_size": simulation_result.population_size,
                "product_name": product_name,
                "simulation_rounds": len(simulation_result.decisions),
            },
        )

    def generate_market_entry_report(
        self,
        industry: str,
        simulation_result: SimulationResult,
        market_size: float = 0,
        growth_rate: float = 0,
    ) -> McKinseyReport:
        """生成市场进入策略报告。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        agg = simulation_result.aggregate
        adoption_rate = agg.get("purchase_intent", 0)

        exec_summary = (
            f"基于{simulation_result.population_size}人合成人群模拟，{industry}市场的"
            f"消费者采纳率为{adoption_rate:.0%}。"
            + (f"当前市场规模约¥{market_size/1e8:.0f}亿，年增长率{growth_rate:.0%}。" if market_size else "")
            + self._market_entry_verdict(adoption_rate)
        )

        market_section = ReportSection(
            title="市场规模与增长",
            content=self._market_size_content(industry, market_size, growth_rate),
            data_sources=["行业研报", "国家统计局"],
            confidence=0.75,
        )

        consumer_section = self._consumer_insights_section(simulation_result)

        barriers_section = ReportSection(
            title="进入壁垒分析",
            content=self._barriers_analysis(industry),
            data_sources=["行业分析"],
            confidence=0.65,
        )

        return McKinseyReport(
            title=f"{industry} — 市场进入策略报告",
            report_type="market_entry",
            created_at=now,
            executive_summary=exec_summary,
            sections=[market_section, consumer_section, barriers_section],
            key_findings=self._extract_key_findings(simulation_result, industry),
            recommendations=self._market_entry_recommendations(adoption_rate, industry),
            risks=self._market_entry_risks(industry),
            confidence_score=agg.get("avg_confidence", 0.5),
            metadata={"industry": industry, "market_size": market_size},
        )

    def generate_competitive_analysis(
        self,
        industry: str,
        competitors: list[dict[str, Any]],
        simulation_result: SimulationResult,
    ) -> McKinseyReport:
        """生成竞争格局分析报告。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        exec_summary = (
            f"{industry}行业竞争格局分析。"
            f"当前市场存在{len(competitors)}个主要竞争者。"
            f"基于{simulation_result.population_size}人合成人群模拟，"
            f"识别出以下竞争机会和威胁。"
        )

        landscape_section = ReportSection(
            title="竞争格局概览",
            content=self._competitive_landscape(competitors),
            data_sources=["公开财报", "行业研报"],
            confidence=0.7,
        )

        positioning_section = ReportSection(
            title="差异化定位机会",
            content=self._positioning_opportunities(competitors, simulation_result),
            data_sources=["合成人群模拟"],
            confidence=0.65,
        )

        return McKinseyReport(
            title=f"{industry} — 竞争格局分析报告",
            report_type="competitive",
            created_at=now,
            executive_summary=exec_summary,
            sections=[landscape_section, positioning_section],
            key_findings=[f"{c.get('name', '?')}：{c.get('strength', '未知优势')}" for c in competitors[:5]],
            recommendations=["建议从差异化定位切入", "关注竞品薄弱环节"],
            risks=["大厂跟进", "价格战"],
            confidence_score=0.65,
            metadata={"industry": industry, "competitor_count": len(competitors)},
        )

    # ================================================================
    # 内部方法
    # ================================================================

    def _product_exec_summary(
        self, product_name: str, purchase_intent: float, confidence: float, segments: dict
    ) -> str:
        verdict = "强烈建议推进上市" if purchase_intent > 0.6 else (
            "建议小规模测试后决定" if purchase_intent > 0.4 else "建议重新审视产品定位"
        )

        best_segment = ""
        if segments:
            best = max(segments.items(), key=lambda x: x[1].get("purchase_intent", 0))
            best_segment = f"核心目标人群为{best[0]}（购买意愿{best[1].get('purchase_intent', 0):.0%}）。"

        return (
            f"{product_name}的合成人群模拟显示，整体购买意愿为{purchase_intent:.0%}"
            f"（置信度{confidence:.0%}）。{best_segment}{verdict}。"
        )

    def _market_analysis_content(self, market_data: dict) -> str:
        if not market_data:
            return "市场数据待补充。建议通过天眼数据源层获取最新行业数据。"
        parts = []
        if "market_size" in market_data:
            parts.append(f"市场规模：¥{market_data['market_size']/1e8:.0f}亿元")
        if "growth_rate" in market_data:
            parts.append(f"年增长率：{market_data['growth_rate']:.0%}")
        if "trends" in market_data:
            parts.append(f"核心趋势：{market_data['trends']}")
        return "；".join(parts) + "。" if parts else "市场数据待分析。"

    def _consumer_insights_section(self, result: SimulationResult) -> ReportSection:
        segments = result.segments
        content_lines = ["### 分群购买意愿", ""]

        for segment, metrics in sorted(
            segments.items(), key=lambda x: x[1].get("purchase_intent", 0), reverse=True
        ):
            pi = metrics.get("purchase_intent", 0)
            bar = "█" * int(pi * 20) + "░" * (20 - int(pi * 20))
            content_lines.append(f"- **{segment}**: {pi:.0%} {bar}")

        content_lines.append("")
        content_lines.append("### 决策分布")
        agg = result.aggregate
        dist = agg.get("decision_distribution", {})
        for decision, count in sorted(dist.items(), key=lambda x: -x[1]):
            pct = count / result.population_size * 100
            content_lines.append(f"- {decision}: {count}人 ({pct:.1f}%)")

        return ReportSection(
            title="消费者洞察",
            content="\n".join(content_lines),
            data_sources=["合成人群模拟"],
            confidence=agg.get("avg_confidence", 0.5),
        )

    def _competition_content(self, product_name: str, market_data: dict) -> str:
        competitors = market_data.get("competitors", [])
        if not competitors:
            return f"{product_name}所在赛道的竞争格局待深入分析。建议通过天眼市场眼模块获取竞品数据。"
        lines = ["| 竞品 | 市占率 | 核心优势 |", "|------|--------|---------|"]
        for c in competitors[:8]:
            name = c.get("name", "?")
            share = c.get("market_share", "未知")
            strength = c.get("strength", "待分析")
            lines.append(f"| {name} | {share} | {strength} |")
        return "\n".join(lines)

    def _channel_analysis_section(self, segments: dict) -> ReportSection:
        channel_scores = {}
        for seg_name, metrics in segments.items():
            pi = metrics.get("purchase_intent", 0)
            if "一线城市" in seg_name:
                channel_scores["小红书/抖音"] = channel_scores.get("小红书/抖音", 0) + pi
            elif "三线" in seg_name:
                channel_scores["拼多多/快手"] = channel_scores.get("拼多多/快手", 0) + pi
            else:
                channel_scores["淘宝/京东"] = channel_scores.get("淘宝/京东", 0) + pi

        lines = ["### 推荐渠道排序", ""]
        for ch, score in sorted(channel_scores.items(), key=lambda x: -x[1]):
            lines.append(f"- **{ch}**：匹配度 {score:.0%}")

        return ReportSection(
            title="渠道策略",
            content="\n".join(lines),
            data_sources=["合成人群模拟"],
            confidence=0.6,
        )

    def _extract_key_findings(self, result: SimulationResult, name: str) -> list[str]:
        findings = []
        agg = result.aggregate
        pi = agg.get("purchase_intent", 0)

        findings.append(f"整体购买意愿：{pi:.0%}（{'高' if pi > 0.6 else '中' if pi > 0.4 else '低'}）")

        if result.segments:
            best = max(result.segments.items(), key=lambda x: x[1].get("purchase_intent", 0))
            findings.append(f"最强细分市场：{best[0]}（{best[1].get('purchase_intent', 0):.0%}）")

            worst = min(result.segments.items(), key=lambda x: x[1].get("purchase_intent", 0))
            findings.append(f"最弱细分市场：{worst[0]}（{worst[1].get('purchase_intent', 0):.0%}）")

        social_rate = agg.get("social_influence_rate", 0)
        if social_rate > 0.1:
            findings.append(f"社交传播效应显著：{social_rate:.0%}的消费者受社交影响")

        return findings

    def _generate_recommendations(self, pi, conf, segments, name) -> list[str]:
        recs = []
        if pi > 0.6:
            recs.append("购买意愿强烈，建议快速推进上市，抢占市场窗口")
            recs.append("优先投放高意愿细分市场，快速获取首批用户")
        elif pi > 0.4:
            recs.append("购买意愿中等，建议先做1000人小规模测试")
            recs.append("重点优化定价和卖点，提升转化率")
        else:
            recs.append("购买意愿偏低，建议重新审视产品定位")
            recs.append("考虑调整目标人群或差异化卖点")

        if segments:
            best_tier = max(
                [(k, v) for k, v in segments.items() if "城市" in k],
                key=lambda x: x[1].get("purchase_intent", 0),
                default=("", {}),
            )
            if best_tier[0]:
                recs.append(f"优先覆盖{best_tier[0].replace('城市_', '')}市场")

        recs.append("建议配合KOL种草+私域运营组合获客策略")
        return recs

    def _assess_risks(self, pi, conf, name) -> list[str]:
        risks = []
        if conf < 0.5:
            risks.append("预测置信度偏低，实际结果可能存在较大偏差")
        if pi < 0.4:
            risks.append("购买意愿不足，上市后可能面临获客困难")
        risks.append("竞品可能快速跟进，需建立差异化壁垒")
        risks.append("政策法规变化可能影响产品合规性")
        return risks

    def _market_entry_verdict(self, rate: float) -> str:
        if rate > 0.6:
            return "市场接受度高，建议积极进入。"
        elif rate > 0.4:
            return "市场接受度中等，建议谨慎进入，先做POC验证。"
        return "市场接受度偏低，建议暂缓进入或寻找差异化切入点。"

    def _market_size_content(self, industry, size, growth) -> str:
        parts = [f"{industry}行业分析。"]
        if size:
            parts.append(f"市场规模约¥{size/1e8:.0f}亿元。")
        if growth:
            parts.append(f"年复合增长率约{growth:.0%}。")
        parts.append("详细数据建议通过天眼数据源层获取最新行业研报。")
        return "".join(parts)

    def _barriers_analysis(self, industry) -> str:
        return (
            f"进入{industry}市场的主要壁垒包括：\n"
            f"- 资质壁垒：行业准入资质和牌照要求\n"
            f"- 资金壁垒：初始投资和运营资金需求\n"
            f"- 技术壁垒：核心技术门槛和专利保护\n"
            f"- 渠道壁垒：现有渠道格局和分销网络\n"
            f"- 品牌壁垒：消费者品牌认知和忠诚度"
        )

    def _market_entry_recommendations(self, rate, industry) -> list[str]:
        recs = [f"建议通过差异化定位切入{industry}市场"]
        if rate > 0.5:
            recs.append("市场窗口期明显，建议快速行动")
        recs.append("优先建立核心用户群，再扩展大众市场")
        recs.append("考虑与行业头部企业战略合作")
        return recs

    def _market_entry_risks(self, industry) -> list[str]:
        return [
            f"{industry}行业政策变化风险",
            "大企业竞争碾压风险",
            "消费者教育成本过高风险",
            "供应链不稳定风险",
        ]

    def _competitive_landscape(self, competitors: list) -> str:
        if not competitors:
            return "竞争数据待补充。"
        lines = ["| 竞争者 | 市场地位 | 核心能力 | 威胁等级 |", "|--------|---------|---------|---------|"]
        for c in competitors:
            lines.append(
                f"| {c.get('name', '?')} | {c.get('position', '?')} | "
                f"{c.get('capability', '?')} | {c.get('threat', '中')} |"
            )
        return "\n".join(lines)

    def _positioning_opportunities(self, competitors, result) -> str:
        lines = [
            "基于合成人群模拟的差异化机会：",
            "",
        ]
        agg = result.aggregate
        pi = agg.get("purchase_intent", 0)
        if pi > 0.5:
            lines.append("- 消费者接受度足够，可通过创新产品特性建立差异化")
        lines.append("- 关注竞品薄弱环节，寻找未被满足的细分需求")
        lines.append("- 利用数字化渠道降低获客成本，建立成本优势")
        return "\n".join(lines)

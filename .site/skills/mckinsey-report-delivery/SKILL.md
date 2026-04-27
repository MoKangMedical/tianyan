---
name: mckinsey-report-delivery
description: Use when producing Tianyan client deliverables in a McKinsey-style structure, including executive summary, issue tree, TAM/SAM/SOM, recommendations, and implementation roadmap.
---

# McKinsey Report Delivery

Use this skill when the task is about:

- 麦肯锡风格报告
- 执行摘要
- Issue Tree / MECE / 金字塔原则
- 项目交付结构

## Workflow

1. Read [docs/mckinsey_methodology.md](../../docs/mckinsey_methodology.md).
2. Read [tianyan/report_generator.py](../../tianyan/report_generator.py) when implementation details matter.
3. Build deliverables in this order:
   - Executive summary
   - Current state / market
   - Opportunity / scenario
   - Recommendation
   - Implementation roadmap
   - Risk and mitigation
4. Keep outputs suitable for board, client, or investor review.

## Guardrails

- 标题要体现结论，不要只是章节名。
- 所有建议要能回到证据与情景。

## References

- [docs/mckinsey_methodology.md](../../docs/mckinsey_methodology.md)
- [tianyan/report_generator.py](../../tianyan/report_generator.py)

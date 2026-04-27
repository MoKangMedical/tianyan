"""
天眼 (Tianyan) CLI — 命令行入口

支持的命令:
  tianyan serve          启动API服务器
  tianyan predict        运行快速预测
  tianyan templates      列出行业模板
  tianyan health         健康检查
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional


def main(argv: Optional[list[str]] = None) -> int:
    """CLI主入口。"""
    parser = argparse.ArgumentParser(
        prog="tianyan",
        description="天眼 (Tianyan) — 中国版商业预测平台",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # serve 命令
    serve_parser = subparsers.add_parser("serve", help="启动API服务器")
    serve_parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认: 8000)")

    # predict 命令
    predict_parser = subparsers.add_parser("predict", help="运行快速预测")
    predict_parser.add_argument("--product", required=True, help="产品名称")
    predict_parser.add_argument("--price", type=float, required=True, help="产品价格 (元)")
    predict_parser.add_argument("--category", default="消费医疗", help="产品类别")
    predict_parser.add_argument("--size", type=int, default=1000, help="人群规模 (默认: 1000)")
    predict_parser.add_argument("--region", default="一线城市", help="目标地区")
    predict_parser.add_argument("--json", action="store_true", help="输出JSON格式")
    predict_parser.add_argument("--dry-run", action="store_true", help="仅预览参数和资源预估，不实际执行")

    # templates 命令
    templates_parser = subparsers.add_parser("templates", help="列出行业模板")
    templates_parser.add_argument("--json", action="store_true", help="输出JSON格式")

    # health 命令
    health_parser = subparsers.add_parser("health", help="快速健康检查")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "serve":
        return _cmd_serve(args)
    elif args.command == "predict":
        return _cmd_predict(args)
    elif args.command == "templates":
        return _cmd_templates(args)
    elif args.command == "health":
        return _cmd_health(args)
    else:
        parser.print_help()
        return 0


def _cmd_serve(args) -> int:
    """启动API服务器。"""
    try:
        import uvicorn
    except ImportError:
        print("错误: 请先安装 uvicorn (pip install uvicorn)", file=sys.stderr)
        return 1

    print(f"👁️ 启动天眼 API 服务器: http://{args.host}:{args.port}")
    uvicorn.run("demo_server:app", host=args.host, port=args.port, reload=False)
    return 0


def _cmd_predict(args) -> int:
    """运行快速预测。"""
    from tianyan import ConsumerEye, SyntheticPopulation, dry_run_prediction, validate_prediction_params

    # 决策检查点：参数确认
    checkpoint = validate_prediction_params(
        product_name=args.product,
        price=args.price,
        population_size=args.size,
        sub_operations=["消费眼(产品上市)", "消费眼(定价优化)"],
    )
    if not checkpoint.approved:
        print("❌ 参数校验未通过:", file=sys.stderr)
        for err in checkpoint.errors:
            print(f"  • {err}", file=sys.stderr)
        return 1
    for w in checkpoint.warnings:
        print(f"⚠️  {w}", file=sys.stderr)

    # Dry-run 模式
    if getattr(args, 'dry_run', False):
        preview = dry_run_prediction(
            product_name=args.product, price=args.price,
            population_size=args.size,
        )
        if args.json:
            print(json.dumps(preview, ensure_ascii=False, indent=2))
        else:
            print("🔍 Dry-run 预览模式（不实际执行）")
            print(f"  产品: {args.product}")
            print(f"  价格: ¥{args.price:,.0f}")
            print(f"  人群: {args.size}人")
            print(f"  预计耗时: {checkpoint.estimated_cost.get('time_seconds', 0)}s")
            print(f"  预计内存: {checkpoint.estimated_cost.get('memory_mb', 0)}MB")
            if checkpoint.warnings:
                print("  ⚠️ 警告:")
                for w in checkpoint.warnings:
                    print(f"    • {w}")
        return 0

    print(f"🔮 正在生成 {args.product} 预测 (人群: {args.size}人, 地区: {args.region})...")

    pop = SyntheticPopulation(
        region=args.region,
        size=args.size,
        seed=42,
    )
    eye = ConsumerEye()
    result = eye.predict_product_launch(
        product_name=args.product,
        price=args.price,
        category=args.category,
        selling_point=f"{args.product}核心卖点",
        channels=["抖音", "小红书"],
        target_population=pop,
    )

    if args.json:
        output = {
            "product": args.product,
            "price": args.price,
            "population_size": args.size,
            "purchase_intent": result.key_metrics.get("purchase_intent", 0),
            "confidence": result.confidence,
            "recommendations": result.recommendations,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        pi = result.key_metrics.get("purchase_intent", 0)
        print(f"\n📊 预测结果:")
        print(f"  购买意愿: {pi:.1%}")
        print(f"  置信度:   {result.confidence:.1%}")
        print(f"\n💡 建议:")
        for rec in result.recommendations:
            print(f"  • {rec}")

    return 0


def _cmd_templates(args) -> int:
    """列出行业模板。"""
    from tianyan import list_templates

    templates = list_templates()

    if args.json:
        print(json.dumps(templates, ensure_ascii=False, indent=2))
    else:
        print("📋 可用行业模板:\n")
        for tpl in templates:
            print(f"  • {tpl['key']}")
            print(f"    名称: {tpl['name']}")
            print(f"    行业: {tpl['industry']}")
            print(f"    说明: {tpl['description']}")
            print()

    return 0


def _cmd_health(args) -> int:
    """快速健康检查。"""
    try:
        from tianyan import SyntheticPopulation, ConsumerEye

        pop = SyntheticPopulation(size=10, seed=1)
        eye = ConsumerEye()
        print("✅ 天眼引擎正常")
        print(f"  版本: 1.0.0")
        print(f"  人群工厂: OK")
        print(f"  消费眼: OK")
        return 0
    except Exception as e:
        print(f"❌ 健康检查失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

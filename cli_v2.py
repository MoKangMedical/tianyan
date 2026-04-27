#!/usr/bin/env python3
"""
天眼 CLI — 命令行预测工具

用法:
    tianyan predict --product "元气森林" --price 5.5 --category 饮料
    tianyan conversation --interactive
    tianyan server --port 8000
    tianyan status
"""

import argparse
import json
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_predict(args):
    """产品预测。"""
    from tianyan.products import ConsumerEye
    from tianyan.population import SyntheticPopulation

    print(f"正在生成 {args.population} 人的合成人群...")
    pop = SyntheticPopulation(size=args.population, region="全国")

    eye = ConsumerEye()
    print(f"正在预测「{args.product}」的市场反应...")

    result = eye.predict_product_launch(
        product_name=args.product,
        price=args.price,
        category=args.category,
        selling_point=args.selling_point or "",
        channels=args.channels or ["线上"],
        target_population=pop,
    )

    print("\n" + "=" * 50)
    print(f"  预测结果: {args.product}")
    print("=" * 50)
    print(f"  置信度: {result.confidence * 100:.1f}%")
    print(f"\n  关键指标:")
    for k, v in result.key_metrics.items():
        if isinstance(v, float):
            print(f"    {k}: {v * 100:.1f}%" if v < 1 else f"    {k}: {v:.2f}")
        else:
            print(f"    {k}: {v}")

    print(f"\n  建议:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"    {i}. {rec}")
    print("=" * 50)


def cmd_conversation(args):
    """对话式预测。"""
    from tianyan.conversation import ConversationEngine

    engine = ConversationEngine()

    if args.interactive:
        print("天眼对话式预测 (输入 'quit' 退出, 'reset' 重新开始)")
        print("-" * 50)

        while True:
            try:
                user_input = input("\n你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if user_input.lower() == "quit":
                print("再见！")
                break
            elif user_input.lower() == "reset":
                engine.reset()
                print("对话已重置。")
                continue

            if not user_input:
                continue

            if not engine.state:
                response = engine.start(user_input)
            else:
                response = engine.continue_(user_input)

            print(f"\n天眼: {response.message}")

            if response.suggestions:
                print("\n建议回复:")
                for i, s in enumerate(response.suggestions, 1):
                    print(f"  {i}. {s}")

            if response.is_complete:
                print("\n预测完成！输入 'reset' 开始新的预测。")
    else:
        print("请使用 --interactive 参数进入交互模式")


def cmd_server(args):
    """启动服务器。"""
    import uvicorn
    print(f"启动天眼服务器: {args.host}:{args.port}")
    print(f"API文档: http://{args.host}:{args.port}/docs")
    uvicorn.run(
        "server:app",
        host=args.host,
        port=args.port,
        reload=args.debug,
    )


def cmd_status(args):
    """查看系统状态。"""
    from tianyan import get_llm
    from tianyan.persistence import PersistenceLayer

    llm = get_llm()
    db = PersistenceLayer("tianyan_production.db")

    print("=" * 50)
    print("  天眼 Tianyan 系统状态")
    print("=" * 50)
    print(f"\n  LLM引擎:")
    stats = llm.get_stats()
    print(f"    提供商: {stats['provider']}")
    print(f"    模型: {stats['model']}")
    print(f"    可用: {'是' if stats['is_llm_available'] else '否 (Mock模式)'}")
    print(f"    请求数: {stats['request_count']}")

    print(f"\n  数据库:")
    db_stats = db.get_stats()
    for k, v in db_stats.items():
        print(f"    {k}: {v}")

    print("=" * 50)


def cmd_register(args):
    """注册用户。"""
    import secrets
    import json
    from pathlib import Path
    from datetime import datetime

    api_key = f"ty_{secrets.token_hex(24)}"
    keys_path = Path("api_keys.json")

    if keys_path.exists():
        keys = json.loads(keys_path.read_text())
    else:
        keys = {}

    keys[api_key] = {
        "name": args.name,
        "email": args.email,
        "role": args.role,
        "created_at": datetime.now().isoformat(),
        "daily_count": 0,
        "last_date": datetime.now().strftime("%Y-%m-%d"),
    }
    keys_path.write_text(json.dumps(keys, indent=2, ensure_ascii=False))

    print(f"\n注册成功！")
    print(f"  用户: {args.name}")
    print(f"  角色: {args.role}")
    print(f"  API Key: {api_key}")
    print(f"\n请保存好你的API Key，它不会再次显示。")


def main():
    parser = argparse.ArgumentParser(description="天眼 Tianyan — 商业预测平台")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # predict
    p_predict = subparsers.add_parser("predict", help="产品预测")
    p_predict.add_argument("--product", required=True, help="产品名称")
    p_predict.add_argument("--price", type=float, required=True, help="价格")
    p_predict.add_argument("--category", required=True, help="品类")
    p_predict.add_argument("--selling-point", default="", help="卖点")
    p_predict.add_argument("--channels", nargs="+", default=["线上"], help="渠道")
    p_predict.add_argument("--population", type=int, default=1000, help="人群规模")
    p_predict.set_defaults(func=cmd_predict)

    # conversation
    p_conv = subparsers.add_parser("conversation", help="对话式预测")
    p_conv.add_argument("--interactive", action="store_true", help="交互模式")
    p_conv.set_defaults(func=cmd_conversation)

    # server
    p_server = subparsers.add_parser("server", help="启动服务器")
    p_server.add_argument("--host", default="0.0.0.0", help="监听地址")
    p_server.add_argument("--port", type=int, default=8000, help="端口")
    p_server.add_argument("--debug", action="store_true", help="调试模式")
    p_server.set_defaults(func=cmd_server)

    # status
    p_status = subparsers.add_parser("status", help="系统状态")
    p_status.set_defaults(func=cmd_status)

    # register
    p_register = subparsers.add_parser("register", help="注册用户")
    p_register.add_argument("--name", required=True, help="用户名")
    p_register.add_argument("--email", required=True, help="邮箱")
    p_register.add_argument("--role", default="free", choices=["free", "pro", "enterprise"])
    p_register.set_defaults(func=cmd_register)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()

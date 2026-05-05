"""
DeepSeek V4 Pro 适配器 — 天眼AI推理引擎

使用 DeepSeek API (api.deepseek.com/v1) 进行Agent推理。
兼容 MIMOAdapter 接口（generate, generate_sync, batch_generate）。
没有 API key 时自动降级到 MockDeepSeekAdapter。

API文档: https://platform.deepseek.com/api-docs
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("tianyan.deepseek")

# 尝试导入 openai
try:
    from openai import AsyncOpenAI, OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False
    logger.warning("openai 库未安装，DeepSeek适配器将使用降级模式。请执行: pip install openai")


@dataclass
class DeepSeekConfig:
    """DeepSeek API 配置。"""
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"  # DeepSeek V3, 兼容V4
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: float = 30.0

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")


class DeepSeekAdapter:
    """
    DeepSeek API 适配器。

    用于天眼平台的Agent推理。
    通过 openai 库调用 api.deepseek.com/v1 (OpenAI 兼容接口)。
    每个合成人口的决策都通过 DeepSeek 完成。
    """

    def __init__(self, config: Optional[DeepSeekConfig] = None):
        self.config = config or DeepSeekConfig()
        self._async_client = None
        self._sync_client = None

        if not self.config.api_key:
            logger.warning("DEEPSEEK_API_KEY 未设置，将使用降级模式")

    @property
    def is_available(self) -> bool:
        """检查API是否可用。"""
        return bool(self.config.api_key) and _OPENAI_AVAILABLE

    def _get_async_client(self) -> AsyncOpenAI:
        """获取或创建异步客户端。"""
        if self._async_client is None and self.is_available:
            self._async_client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        return self._async_client

    def _get_sync_client(self) -> OpenAI:
        """获取或创建同步客户端。"""
        if self._sync_client is None and self.is_available:
            self._sync_client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        return self._sync_client

    async def generate(self, prompt: str, system: str = "") -> dict[str, Any]:
        """
        调用 DeepSeek API 生成推理结果。

        Args:
            prompt: 用户prompt。
            system: 系统prompt。

        Returns:
            解析后的JSON响应。
        """
        if not self.is_available:
            raise RuntimeError("DeepSeek API 不可用: 缺少 API key 或 openai 库")

        client = self._get_async_client()
        if client is None:
            raise RuntimeError("DeepSeek 异步客户端初始化失败")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        content = response.choices[0].message.content

        # 尝试解析JSON
        try:
            # 处理可能的 markdown 代码块包装
            content = content.strip()
            if content.startswith("```"):
                # 移除 markdown 代码块
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]  # 移除 ```json
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]  # 移除结尾 ```
                content = "\n".join(lines)
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试从文本中提取JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return {"raw_response": content}

    def generate_sync(self, prompt: str, system: str = "") -> dict[str, Any]:
        """同步版本的 generate。"""
        if not self.is_available:
            raise RuntimeError("DeepSeek API 不可用: 缺少 API key 或 openai 库")

        client = self._get_sync_client()
        if client is None:
            raise RuntimeError("DeepSeek 同步客户端初始化失败")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        content = response.choices[0].message.content

        # 尝试解析JSON
        try:
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines)
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return {"raw_response": content}

    async def batch_generate(
        self,
        prompts: list[tuple[str, str]],
        batch_size: int = 10,
    ) -> list[dict[str, Any]]:
        """
        批量生成（用于大规模人群模拟）。

        Args:
            prompts: [(prompt, system), ...] 列表。
            batch_size: 每批大小（控制并发）。

        Returns:
            结果列表。
        """
        results = []
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]
            tasks = [
                self.generate(prompt, system)
                for prompt, system in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({"error": str(result)})
                else:
                    results.append(result)

        return results


class MockDeepSeekAdapter:
    """
    DeepSeek API 模拟器（用于测试/开发/无API key场景）。
    不调用真实API，用规则引擎模拟响应。
    兼容 MIMOAdapter 和 DeepSeekAdapter 的接口。
    """

    def __init__(self, seed: int = 42):
        import random
        self._rng = random.Random(seed)

    async def generate(self, prompt: str, system: str = "") -> dict[str, Any]:
        """模拟 DeepSeek 响应。"""
        return self.generate_sync(prompt, system)

    def generate_sync(self, prompt: str, system: str = "") -> dict[str, Any]:
        """模拟 DeepSeek 响应（同步版）。"""
        # 从 prompt 中提取关键信息
        # 识别场景类型
        if any(kw in prompt for kw in ["购买", "定价", "价格", "产品", "上市"]):
            decisions = ["购买", "不购买", "观望", "考虑", "尝试"]
            decision = self._rng.choice(decisions)
            reasons = {
                "购买": "根据画像分析，该消费者有较高的购买意愿",
                "不购买": "基于消费者特征，当前缺乏购买动机",
                "观望": "需要更多信息或口碑验证后再决定",
                "考虑": "对产品感兴趣但需要比较价格",
                "尝试": "对新产品持开放态度，愿意尝试",
            }
            return {
                "decision": decision,
                "reasoning": reasons.get(decision, f"基于画像分析，选择{decision}"),
                "confidence": round(self._rng.uniform(0.4, 0.9), 2),
            }

        if any(kw in prompt for kw in ["政策", "支持"]):
            decisions = ["支持", "不支持", "观望"]
            decision = self._rng.choice(decisions)
            return {
                "decision": decision,
                "reasoning": f"基于社会画像分析，选择{decision}该政策",
                "confidence": round(self._rng.uniform(0.3, 0.85), 2),
            }

        if any(kw in prompt for kw in ["渠道", "平台"]):
            platforms = ["抖音", "小红书", "京东", "淘宝", "拼多多"]
            decision = self._rng.choice(platforms)
            return {
                "decision": decision,
                "reasoning": f"基于使用习惯，偏好{decision}平台",
                "confidence": round(self._rng.uniform(0.5, 0.95), 2),
            }

        # 默认响应
        return {
            "decision": self._rng.choice(["购买", "考虑", "观望"]),
            "reasoning": "基于综合画像分析",
            "confidence": round(self._rng.uniform(0.4, 0.8), 2),
        }

    async def batch_generate(
        self,
        prompts: list[tuple[str, str]],
        batch_size: int = 10,
    ) -> list[dict[str, Any]]:
        """模拟批量生成。"""
        tasks = [self.generate(prompt, system) for prompt, system in prompts]
        return await asyncio.gather(*tasks)


def create_deepseek_adapter(**kwargs) -> Any:
    """
    工厂函数：创建 DeepSeek 适配器。

    如果有 API key 且 openai 可用，返回 DeepSeekAdapter；
    否则返回 MockDeepSeekAdapter。

    用法:
        adapter = create_deepseek_adapter()
        # 或指定参数
        adapter = create_deepseek_adapter(model="deepseek-chat", temperature=0.8)
    """
    api_key = kwargs.pop("api_key", "") or os.environ.get("DEEPSEEK_API_KEY", "")

    if api_key and _OPENAI_AVAILABLE:
        config = DeepSeekConfig(api_key=api_key, **kwargs)
        logger.info("DeepSeek API 适配器已启用: model=%s", config.model)
        return DeepSeekAdapter(config)
    else:
        if not api_key:
            logger.warning("DEEPSEEK_API_KEY 未设置，使用 MockDeepSeekAdapter 降级模式")
        if not _OPENAI_AVAILABLE:
            logger.warning("openai 库不可用，使用 MockDeepSeekAdapter 降级模式")
        return MockDeepSeekAdapter()


# 全局共享的适配器实例（懒加载）
_shared_adapter: Optional[Any] = None


def get_shared_adapter() -> Any:
    """获取全局共享的 DeepSeek 适配器。"""
    global _shared_adapter
    if _shared_adapter is None:
        _shared_adapter = create_deepseek_adapter()
    return _shared_adapter

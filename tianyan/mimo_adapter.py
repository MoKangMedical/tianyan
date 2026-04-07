"""
MIMO API适配器 — 天眼AI推理引擎

使用小米MIMO API进行Agent推理。
支持无限额度调用，零边际成本。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class MIMOConfig:
    """MIMO API配置。"""
    api_key: str = ""
    base_url: str = "https://api.mimo.ai/v1"
    model: str = "mimo-v2-pro"
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: float = 30.0


class MIMOAdapter:
    """
    MIMO API适配器。

    用于天眼平台的Agent推理。
    每个合成人口的决策都通过MIMO完成。
    """

    def __init__(self, config: Optional[MIMOConfig] = None):
        self.config = config or MIMOConfig()
        if not self.config.api_key:
            self.config.api_key = os.environ.get("MIMO_API_KEY", "")

    async def generate(self, prompt: str, system: str = "") -> dict[str, Any]:
        """
        调用MIMO API生成推理结果。

        Args:
            prompt: 用户prompt。
            system: 系统prompt。

        Returns:
            解析后的JSON响应。
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]

        # 尝试解析JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_response": content}

    def generate_sync(self, prompt: str, system: str = "") -> dict[str, Any]:
        """同步版本的generate。"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        with httpx.Client(timeout=self.config.timeout) as client:
            response = client.post(
                f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
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
        import asyncio

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


class MockMIMOAdapter:
    """
    MIMO API模拟器（用于测试/开发）。
    不调用真实API，用规则引擎模拟响应。
    """

    def generate_sync(self, prompt: str, system: str = "") -> dict[str, Any]:
        """模拟MIMO响应。"""
        if "购买" in prompt or "决策" in prompt:
            import random
            decisions = ["购买", "不购买", "观望", "考虑"]
            decision = random.choice(decisions)
            return {
                "decision": decision,
                "reasoning": f"基于画像分析，选择{decision}",
                "confidence": random.uniform(0.4, 0.9),
            }
        return {"response": "模拟响应"}

"""
天眼 LLM 适配器 — 统一多提供商AI推理层

支持:
- DeepSeek (推荐，国产大模型，性价比高)
- MIMO (小米大模型)
- OpenAI / GPT-4
- 任何 OpenAI 兼容 API

设计原则:
- 统一接口，切换提供商只需改配置
- 自动降级：LLM不可用时回退到规则引擎
- 限流 + 重试 + 缓存
"""

from __future__ import annotations

import json
import os
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

import httpx


class LLMProvider(Enum):
    """支持的LLM提供商。"""
    DEEPSEEK = "deepseek"
    MIMO = "mimo"
    OPENAI = "openai"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """LLM配置。"""
    provider: LLMProvider = LLMProvider.DEEPSEEK
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: float = 30.0
    max_retries: int = 2
    cache_ttl: int = 300  # 缓存5分钟

    @classmethod
    def from_env(cls) -> LLMConfig:
        """从环境变量加载配置。"""
        provider_str = os.environ.get("TIANYAN_LLM_PROVIDER", "deepseek").lower()
        provider_map = {
            "deepseek": LLMProvider.DEEPSEEK,
            "mimo": LLMProvider.MIMO,
            "openai": LLMProvider.OPENAI,
            "mock": LLMProvider.MOCK,
        }
        provider = provider_map.get(provider_str, LLMProvider.DEEPSEEK)

        url_map = {
            LLMProvider.DEEPSEEK: "https://api.deepseek.com/v1",
            LLMProvider.MIMO: "https://api.mimo.ai/v1",
            LLMProvider.OPENAI: "https://api.openai.com/v1",
            LLMProvider.MOCK: "",
        }

        model_map = {
            LLMProvider.DEEPSEEK: "deepseek-chat",
            LLMProvider.MIMO: "mimo-v2-pro",
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.MOCK: "mock",
        }

        key_map = {
            LLMProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
            LLMProvider.MIMO: "MIMO_API_KEY",
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.MOCK: "",
        }

        api_key = os.environ.get(key_map.get(provider, ""), "")

        return cls(
            provider=provider,
            api_key=api_key,
            base_url=os.environ.get("TIANYAN_LLM_BASE_URL", url_map.get(provider, "")),
            model=os.environ.get("TIANYAN_LLM_MODEL", model_map.get(provider, "")),
            max_tokens=int(os.environ.get("TIANYAN_LLM_MAX_TOKENS", "1024")),
            temperature=float(os.environ.get("TIANYAN_LLM_TEMPERATURE", "0.7")),
            timeout=float(os.environ.get("TIANYAN_LLM_TIMEOUT", "30.0")),
        )


class LLMCache:
    """简单的内存缓存。"""

    def __init__(self, ttl: int = 300):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl

    def _key(self, prompt: str, system: str) -> str:
        return hashlib.md5(f"{system}|||{prompt}".encode()).hexdigest()

    def get(self, prompt: str, system: str) -> Optional[Any]:
        key = self._key(prompt, system)
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._ttl:
                return val
            del self._cache[key]
        return None

    def set(self, prompt: str, system: str, value: Any):
        key = self._key(prompt, system)
        self._cache[key] = (time.time(), value)

    def clear(self):
        self._cache.clear()


class UnifiedLLMAdapter:
    """
    统一LLM适配器。

    用法:
        llm = UnifiedLLMAdapter()  # 自动从环境变量加载
        result = llm.generate("分析这个产品的市场前景...")
        result = llm.generate_json("返回JSON格式的分析结果...")
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.from_env()
        self._cache = LLMCache(self.config.cache_ttl)
        self._request_count = 0
        self._last_request_time = 0.0

        # 如果没有API Key且不是mock，自动降级到mock
        if not self.config.api_key and self.config.provider != LLMProvider.MOCK:
            print(f"[Tianyan LLM] 未配置 {self.config.provider.value} API Key，降级到规则引擎")
            self.config.provider = LLMProvider.MOCK

    @property
    def is_llm_available(self) -> bool:
        """LLM是否可用。"""
        return self.config.provider != LLMProvider.MOCK

    @property
    def provider_name(self) -> str:
        return self.config.provider.value

    def _rate_limit(self):
        """简单的限流：每秒最多5个请求。"""
        now = time.time()
        if now - self._last_request_time < 0.2:
            time.sleep(0.2 - (now - self._last_request_time))
        self._last_request_time = time.time()

    def _call_api(self, messages: list[dict], temperature: float = None) -> str:
        """调用LLM API。"""
        temp = temperature if temperature is not None else self.config.temperature
        self._rate_limit()

        for attempt in range(self.config.max_retries + 1):
            try:
                with httpx.Client(timeout=self.config.timeout) as client:
                    resp = client.post(
                        f"{self.config.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.config.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.config.model,
                            "messages": messages,
                            "max_tokens": self.config.max_tokens,
                            "temperature": temp,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    self._request_count += 1
                    return data["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt < self.config.max_retries:
                    time.sleep(1 * (attempt + 1))
                    continue
                raise

        return ""

    def generate(self, prompt: str, system: str = "", temperature: float = None) -> str:
        """
        生成文本响应。

        Args:
            prompt: 用户提示
            system: 系统提示
            temperature: 温度参数

        Returns:
            生成的文本
        """
        # 检查缓存
        cached = self._cache.get(prompt, system)
        if cached is not None:
            return cached

        # Mock模式
        if self.config.provider == LLMProvider.MOCK:
            return self._mock_generate(prompt, system)

        # 调用API
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        result = self._call_api(messages, temperature)
        self._cache.set(prompt, system, result)
        return result

    def generate_json(self, prompt: str, system: str = "", temperature: float = None) -> dict[str, Any]:
        """
        生成JSON响应。

        自动解析JSON，如果解析失败则包装为raw_response。
        """
        text = self.generate(prompt, system, temperature)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取JSON代码块
            import re
            match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            return {"raw_response": text, "parse_error": True}

    def batch_generate(
        self,
        prompts: list[tuple[str, str]],
        batch_size: int = 5,
    ) -> list[dict[str, Any]]:
        """批量生成JSON响应。"""
        results = []
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]
            for prompt, system in batch:
                try:
                    result = self.generate_json(prompt, system)
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e)})
        return results

    def _mock_generate(self, prompt: str, system: str) -> str:
        """规则引擎模拟响应。"""
        if "购买" in prompt or "决策" in prompt:
            import random
            decisions = ["购买", "不购买", "观望", "考虑"]
            decision = random.choice(decisions)
            confidence = round(random.uniform(0.4, 0.9), 2)
            return json.dumps({
                "decision": decision,
                "reasoning": f"基于画像分析，选择{decision}",
                "confidence": confidence,
            }, ensure_ascii=False)
        elif "分析" in prompt or "预测" in prompt:
            import random
            return json.dumps({
                "prediction": random.choice(["乐观", "中性", "谨慎"]),
                "confidence": round(random.uniform(0.5, 0.85), 2),
                "key_factors": ["价格竞争力", "品牌认知", "渠道覆盖"],
            }, ensure_ascii=False)
        elif "KOL" in prompt or "直播" in prompt:
            import random
            return json.dumps({
                "effectiveness": random.choice(["高", "中", "低"]),
                "roi": round(random.uniform(1.5, 4.0), 1),
                "recommendation": "建议先小规模测试",
            }, ensure_ascii=False)
        else:
            return json.dumps({"response": "模拟响应", "mode": "mock"}, ensure_ascii=False)

    def get_stats(self) -> dict[str, Any]:
        """获取使用统计。"""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "request_count": self._request_count,
            "cache_size": len(self._cache._cache),
            "is_llm_available": self.is_llm_available,
        }


# 全局单例
_global_llm: Optional[UnifiedLLMAdapter] = None


def get_llm() -> UnifiedLLMAdapter:
    """获取全局LLM实例（单例模式）。"""
    global _global_llm
    if _global_llm is None:
        _global_llm = UnifiedLLMAdapter()
    return _global_llm


def reset_llm():
    """重置全局LLM实例（用于测试）。"""
    global _global_llm
    _global_llm = None

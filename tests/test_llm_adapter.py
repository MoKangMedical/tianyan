"""天眼LLM适配器测试。"""

import pytest
from tianyan.llm_adapter import (
    UnifiedLLMAdapter,
    LLMConfig,
    LLMProvider,
    LLMCache,
    get_llm,
    reset_llm,
)


class TestLLMConfig:
    def test_default_config(self):
        config = LLMConfig()
        assert config.provider == LLMProvider.DEEPSEEK
        assert config.max_tokens == 1024

    def test_from_env_mock(self, monkeypatch):
        monkeypatch.setenv("TIANYAN_LLM_PROVIDER", "mock")
        config = LLMConfig.from_env()
        assert config.provider == LLMProvider.MOCK

    def test_from_env_deepseek(self, monkeypatch):
        monkeypatch.setenv("TIANYAN_LLM_PROVIDER", "deepseek")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
        config = LLMConfig.from_env()
        assert config.provider == LLMProvider.DEEPSEEK
        assert config.api_key == "test-key"


class TestLLMCache:
    def test_set_get(self):
        cache = LLMCache(ttl=60)
        cache.set("prompt", "system", "result")
        assert cache.get("prompt", "system") == "result"

    def test_expired(self):
        cache = LLMCache(ttl=0)
        cache.set("prompt", "system", "result")
        import time
        time.sleep(0.01)
        assert cache.get("prompt", "system") is None

    def test_clear(self):
        cache = LLMCache()
        cache.set("p", "s", "r")
        cache.clear()
        assert cache.get("p", "s") is None


class TestUnifiedLLMAdapter:
    def test_mock_generate(self):
        config = LLMConfig(provider=LLMProvider.MOCK)
        llm = UnifiedLLMAdapter(config)
        result = llm.generate("测试购买决策")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_mock_generate_json(self):
        config = LLMConfig(provider=LLMProvider.MOCK)
        llm = UnifiedLLMAdapter(config)
        result = llm.generate_json("分析市场前景")
        assert isinstance(result, dict)
        assert "prediction" in result or "response" in result

    def test_auto_fallback_to_mock(self):
        """没有API Key时自动降级到mock。"""
        config = LLMConfig(provider=LLMProvider.DEEPSEEK, api_key="")
        llm = UnifiedLLMAdapter(config)
        assert llm.config.provider == LLMProvider.MOCK

    def test_is_llm_available(self):
        config = LLMConfig(provider=LLMProvider.MOCK)
        llm = UnifiedLLMAdapter(config)
        assert not llm.is_llm_available

    def test_stats(self):
        config = LLMConfig(provider=LLMProvider.MOCK)
        llm = UnifiedLLMAdapter(config)
        llm.generate("test")
        stats = llm.get_stats()
        assert stats["provider"] == "mock"
        assert stats["request_count"] == 0  # mock不计数

    def test_cache_hit(self):
        config = LLMConfig(provider=LLMProvider.MOCK)
        llm = UnifiedLLMAdapter(config)
        r1 = llm.generate("相同prompt")
        r2 = llm.generate("相同prompt")
        assert r1 == r2

    def test_batch_generate(self):
        config = LLMConfig(provider=LLMProvider.MOCK)
        llm = UnifiedLLMAdapter(config)
        prompts = [("prompt1", ""), ("prompt2", "")]
        results = llm.batch_generate(prompts)
        assert len(results) == 2


class TestGlobalInstance:
    def teardown_method(self):
        reset_llm()

    def test_get_llm_singleton(self):
        llm1 = get_llm()
        llm2 = get_llm()
        assert llm1 is llm2

    def test_reset_llm(self):
        llm1 = get_llm()
        reset_llm()
        llm2 = get_llm()
        assert llm1 is not llm2

"""
LLM Client for ZENPATH Chat.

Supports configurable API key and model via environment or hardcoded config.
Falls back to mock mode if no LLM API is available.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

# Config — env vars only (loaded via dotenv in main.py)
LLM_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.environ.get("CHAT_LLM_MODEL") or "deepseek-v4-pro"
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT", "60"))
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "4096"))
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.3"))


def _get_client():
    """Lazy-load the OpenAI client."""
    if not LLM_API_KEY:
        logger.warning("DEEPSEEK_API_KEY not set, using mock mode")
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    except ImportError:
        logger.warning("openai package not installed, using mock mode")
        return None


async def call_llm(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: int | None = None,
    response_format: str | None = None,
) -> dict[str, Any]:
    """Call the LLM and return {answer, token_count, latency_ms, model}.

    Falls back to mock mode if no API key or client available.
    """
    client = _get_client()
    if client is None:
        return _mock_response(messages)

    try:
        import asyncio
        start = time.monotonic()
        kwargs: dict[str, Any] = {
            "model": model or LLM_MODEL,
            "messages": messages,
            "temperature": temperature if temperature is not None else LLM_TEMPERATURE,
            "max_tokens": max_tokens or LLM_MAX_TOKENS,
        }
        if response_format:
            kwargs["response_format"] = {"type": response_format}

        # Wrap in thread to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(**kwargs, timeout=timeout or LLM_TIMEOUT),
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        choice = response.choices[0]
        answer = choice.message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0

        return {
            "answer": answer,
            "token_count": tokens,
            "latency_ms": elapsed_ms,
            "model": response.model,
        }
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return {
            "answer": f"AI 服务暂时不可用（{str(e)[:80]}），请稍后重试。",
            "token_count": 0,
            "latency_ms": 0,
            "model": LLM_MODEL,
            "error": str(e),
        }


def _mock_response(messages: list[dict[str, str]]) -> dict[str, Any]:
    """Mock response when LLM is unavailable — returns a helpful placeholder."""
    user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            break

    return {
        "answer": (
            f"这是择境 AI 志愿顾问的模拟回答。\n\n"
            f"你问的是：{user_msg[:100]}\n\n"
            "当前为 mock 模式（未连接 LLM API）。实际部署后，将基于 CHSI 官方资料、"
            "结构化推荐数据和你的志愿方案，生成个性化分析建议。\n\n"
            "你可以继续使用志愿评估功能，获取基于历年投档线和位次的冲稳保推荐方案。"
        ),
        "token_count": 0,
        "latency_ms": 0,
        "model": "mock",
        "mock": True,
    }

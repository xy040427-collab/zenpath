"""
LLM Generator — calls DeepSeek API to generate personalized explanations.

If API key is not set or API fails, returns a disabled/insufficient status.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)


async def generate_explanation(
    messages: list[dict],
    provider: str = 'deepseek',
    model: str = 'deepseek-chat',
) -> dict:
    """Generate AI explanation from messages. Returns structured result."""
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        logger.info("DEEPSEEK_API_KEY not set, skipping AI generation")
        return {
            'status': 'disabled',
            'explanation': None,
            'message': 'AI解释功能未启用（缺少API密钥）',
        }

    try:
        import httpx
        base_url = "https://api.deepseek.com/v1/chat/completions"

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                base_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # Try to parse as JSON
            try:
                explanation = json.loads(content)
            except json.JSONDecodeError:
                # Clean markdown code fences
                if content.startswith("```"):
                    content = content.split("\n", 1)[1] if "\n" in content else content
                    content = content.rsplit("```", 1)[0] if "```" in content else content
                try:
                    explanation = json.loads(content)
                except json.JSONDecodeError:
                    explanation = {"student_version": content}

            return {
                'status': 'ok',
                'explanation': explanation,
            }

    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return {
            'status': 'insufficient',
            'explanation': None,
            'message': f'AI解释生成失败: {str(e)[:100]}',
        }

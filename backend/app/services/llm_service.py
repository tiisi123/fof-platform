"""
LLM 服务 - 使用 OpenAI 兼容接口（默认 Codex / GPT-5.5）。
"""
from typing import Optional, List, Dict, Any
import requests
import json

from app.core.config import settings
from app.core.logger import logger


class LLMService:
    """OpenAI 兼容 LLM 调用服务"""

    def __init__(self):
        self.providers = {
            "openai_codex": {
                "key": "openai_codex",
                "name": "Codex / GPT-5.5",
                "api_key": settings.LLM_CODEX_API_KEY,
                "model": settings.LLM_CODEX_MODEL,
                "base_url": settings.LLM_CODEX_BASE_URL,
                "timeout": settings.LLM_CODEX_TIMEOUT,
                "enabled": settings.LLM_ENABLED and bool(settings.LLM_CODEX_API_KEY),
            },
            "deepseek": {
                "key": "deepseek",
                "name": "DeepSeek",
                "api_key": settings.LLM_API_KEY,
                "model": settings.LLM_MODEL,
                "base_url": settings.LLM_BASE_URL,
                "timeout": settings.LLM_TIMEOUT,
                "enabled": settings.LLM_ENABLED and bool(settings.LLM_API_KEY),
            },
        }
        self.default_provider = "openai_codex"
        self.fallback_provider = "deepseek"

    def get_provider_options(self) -> List[Dict[str, Any]]:
        """返回前端可展示的模型通道，不包含密钥。"""
        return [
            {
                "key": key,
                "name": cfg["name"],
                "model": cfg["model"],
                "enabled": cfg["enabled"],
                "is_default": key == self.default_provider,
            }
            for key, cfg in self.providers.items()
        ]

    def _get_provider(self, provider: Optional[str] = None) -> Dict[str, Any]:
        key = provider or self.default_provider
        return self.providers.get(key) or self.providers[self.default_provider]

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        provider: Optional[str] = None,
    ):
        """
        调用 Chat Completion API (OpenAI 兼容格式)

        Args:
            messages: 消息列表，每个元素为 {"role": "user/assistant/system", "content": "..."}
            temperature: 温度参数 (0-2)，越高越随机
            max_tokens: 最大生成token数
            stream: 是否流式返回

        Returns:
            如果 stream=False: 返回生成的文本内容(str)，失败返回 None
            如果 stream=True: 返回 requests.Response 对象用于流式读取
        """
        provider_cfg = self._get_provider(provider)
        if not provider_cfg["enabled"]:
            logger.warning(f"LLM通道未启用或API Key未配置: provider={provider_cfg['key']}")
            return None

        try:
            url = f"{provider_cfg['base_url'].rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {provider_cfg['api_key']}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": provider_cfg["model"],
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens:
                payload["max_tokens"] = max_tokens
            if stream:
                payload["stream"] = True

            logger.info(f"调用LLM: provider={provider_cfg['key']}, model={provider_cfg['model']}, messages={len(messages)}条, stream={stream}")
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=provider_cfg["timeout"],
                stream=stream,
            )

            if response.status_code != 200:
                logger.error(f"LLM调用失败: status={response.status_code}, body={response.text}")
                return None

            # 如果是流式请求，直接返回 response 对象供调用方处理
            if stream:
                return response

            content_type = response.headers.get("content-type", "")
            if "text/event-stream" in content_type.lower() or response.text.lstrip().startswith("data:"):
                content = self._parse_sse_chat_content(response.content)
                if not content:
                    body_preview = response.text[:500] if response.text else "<empty>"
                    logger.warning(
                        "LLM流式响应内容为空: "
                        f"provider={provider_cfg['key']}, model={provider_cfg['model']}, body={body_preview}"
                    )
                    return None

                logger.info(f"LLM调用成功: provider={provider_cfg['key']}, 生成{len(content)}字符")
                return content

            try:
                result = response.json()
            except ValueError:
                body_preview = response.text[:500] if response.text else "<empty>"
                logger.error(
                    "LLM响应不是JSON: "
                    f"provider={provider_cfg['key']}, model={provider_cfg['model']}, "
                    f"status={response.status_code}, content_type={content_type}, body={body_preview}"
                )
                return None

            content = result.get("choices", [{}])[0].get("message", {}).get("content")

            if not content:
                logger.warning(f"LLM返回内容为空: {result}")
                return None

            logger.info(f"LLM调用成功: provider={provider_cfg['key']}, 生成{len(content)}字符")
            return content

        except requests.Timeout:
            logger.error(f"LLM调用超时: provider={provider_cfg['key']}, timeout>{provider_cfg['timeout']}秒")
            return None
        except Exception as e:
            logger.error(f"LLM调用异常: {type(e).__name__}: {e}")
            return None

    def _parse_sse_chat_content(self, raw_content: bytes) -> Optional[str]:
        """Parse OpenAI-compatible text/event-stream chat chunks."""
        try:
            text = raw_content.decode("utf-8", errors="replace")
        except Exception:
            return None

        parts: List[str] = []
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue

            data = line[5:].strip()
            if not data or data == "[DONE]":
                continue

            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue

            choice = (chunk.get("choices") or [{}])[0]
            delta = choice.get("delta") or {}
            message = choice.get("message") or {}
            content = delta.get("content") or message.get("content")
            if content:
                parts.append(content)

        return "".join(parts).strip() or None

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        provider: Optional[str] = None,
    ) -> Optional[str]:
        """
        简化接口：直接生成文本

        Args:
            prompt: 用户输入的提示词
            system_prompt: 系统提示词（可选）
            temperature: 温度参数

        Returns:
            生成的文本内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.chat_completion(messages=messages, temperature=temperature, provider=provider)

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        情感分析 - 返回情感分类和关键词

        Args:
            text: 待分析文本

        Returns:
            {"sentiment": "positive/neutral/negative", "score": 0.0-1.0, "keywords": [...]}
        """
        system_prompt = """你是一个专业的金融舆情分析专家。请对给定的新闻或舆情内容进行情感分析。
输出JSON格式：
{
  "sentiment": "positive/neutral/negative",
  "score": 0.85,
  "keywords": ["关键词1", "关键词2"],
  "events": ["核心事件描述"],
  "summary": "一句话总结"
}
要求：
- 正面(positive): 获奖、规模增长、业绩优秀、合作利好等
- 中性(neutral): 人员变动(非核心人员)、产品发行等
- 负面(negative): 处罚、清盘、踩雷、核心离职、诉讼等
- score: 情感强度0-1，0最负面，1最正面
- keywords: 提取3-5个关键词
- events: 提取核心事件(数组)
- summary: 20字以内总结
"""
        prompt = f"请分析以下内容的情感和关键信息:\n\n{text}"
        content = self.generate_text(prompt, system_prompt=system_prompt, temperature=0.3)

        if not content:
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "keywords": [],
                "events": [],
                "summary": "分析失败"
            }

        try:
            # 尝试解析JSON
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            logger.warning(f"LLM返回非JSON格式: {content}")
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "keywords": [],
                "events": [],
                "summary": content[:50] if content else "解析失败"
            }


# 创建全局单例
llm_service = LLMService()

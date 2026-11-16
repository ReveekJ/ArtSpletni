import logging

import httpx
import msgspec

from app.domain.gossip.llm_schema import LlmGossipResponse
from app.domain.gossip.prompt import build_system_prompt, build_user_prompt
from app.domain.gossip.types import GossipSubject, NearbyContext
from app.lib.settings import LlmSettings

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2
ERROR_PREVIEW_CHARS = 1500


class GossipWriterError(Exception):
    pass


class ChatMessage(msgspec.Struct):
    role: str
    content: str


class _CompletionMessage(msgspec.Struct):
    content: str | None = None


class _CompletionChoice(msgspec.Struct):
    message: _CompletionMessage


class _Completion(msgspec.Struct):
    choices: list[_CompletionChoice] = []


class LlmGossipWriter:
    def __init__(self, settings: LlmSettings) -> None:
        self._settings = settings

    async def write(
        self, subject: GossipSubject, context: NearbyContext, max_items: int, languages: list[str]
    ) -> LlmGossipResponse:
        messages = [
            ChatMessage(role="system", content=build_system_prompt(languages)),
            ChatMessage(role="user", content=build_user_prompt(subject, context, max_items)),
        ]
        last_error = ""
        async with httpx.AsyncClient(timeout=self._settings.timeout_seconds) as client:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                content = await self._complete(client, messages)
                try:
                    return msgspec.json.decode(self._extract_json(content), type=LlmGossipResponse)
                except msgspec.DecodeError as exc:
                    last_error = str(exc)
                    logger.warning("LLM returned invalid gossip JSON (attempt %s): %s", attempt, exc)
                    messages = [
                        *messages,
                        ChatMessage(role="assistant", content=content),
                        ChatMessage(
                            role="user",
                            content=f"The JSON is invalid: {last_error[:ERROR_PREVIEW_CHARS]}. "
                            "Reply with the corrected JSON object only.",
                        ),
                    ]
        raise GossipWriterError(f"LLM returned invalid JSON: {last_error}")

    async def _complete(self, client: httpx.AsyncClient, messages: list[ChatMessage]) -> str:
        settings = self._settings
        body: dict[str, object] = {
            **settings.extra_body,
            "model": settings.model,
            "messages": msgspec.to_builtins(messages),
            "temperature": settings.temperature,
        }
        if settings.json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {settings.api_key.get_secret_value() or 'not-set'}"}
        url = f"{settings.base_url.rstrip('/')}/chat/completions"
        try:
            response = await client.post(url, json=body, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GossipWriterError(f"LLM request failed: {exc}") from exc
        try:
            completion = msgspec.json.decode(response.content, type=_Completion)
        except msgspec.DecodeError as exc:
            raise GossipWriterError(f"LLM returned an unexpected response: {exc}") from exc
        if not completion.choices or not completion.choices[0].message.content:
            raise GossipWriterError("LLM returned an empty response")
        return completion.choices[0].message.content

    @staticmethod
    def _extract_json(content: str) -> str:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end <= start:
            return content
        return content[start : end + 1]

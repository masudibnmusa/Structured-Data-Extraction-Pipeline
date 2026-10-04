"""Thin wrapper around the LLM API. Uses tool calling to force schema-conformant JSON."""
import anthropic

from app.config import settings
from app.utils.logger import get_logger
from app.utils.retry_handler import retry

log = get_logger(__name__)

_RETRYABLE = (
    anthropic.APIConnectionError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
    ValueError,  # e.g. model did not return a tool call
)


class LLMClient:
    def __init__(self) -> None:
        if settings.llm_provider != "anthropic":
            raise NotImplementedError("Only the 'anthropic' provider is implemented. Add others here.")
        self.client = anthropic.Anthropic(api_key=settings.llm_api_key or None)

    @retry(exceptions=_RETRYABLE)
    def extract_structured(
        self, system: str, user: str, tool_name: str, json_schema: dict, description: str = ""
    ) -> dict:
        resp = self.client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            system=system,
            tools=[{
                "name": tool_name,
                "description": description or f"Record the extracted {tool_name} data.",
                "input_schema": json_schema,
            }],
            tool_choice={"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user}],
        )
        log.info("LLM usage: in=%s out=%s", resp.usage.input_tokens, resp.usage.output_tokens)
        for block in resp.content:
            if block.type == "tool_use":
                return dict(block.input)
        raise ValueError("Model response contained no tool call")


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
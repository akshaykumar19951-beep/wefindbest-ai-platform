from collections.abc import Generator

from app.ai_gateway.types import GatewayRequest, ProviderHealth


class ProviderError(Exception):
    pass


class BaseProvider:
    name = "base"
    default_model = "mock"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url

    @property
    def configured(self) -> bool:
        return bool(self.api_key or self.name in {"mock", "ollama"})

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            configured=self.configured,
            healthy=self.configured,
            detail="configured" if self.configured else "missing credentials",
        )

    def complete(self, request: GatewayRequest) -> str:
        if not self.configured:
            raise ProviderError(f"{self.name} is not configured")
        return self._mock_external_response(request)

    def stream(self, request: GatewayRequest) -> Generator[str, None, None]:
        for token in self.complete(request).split():
            yield token + " "

    def _mock_external_response(self, request: GatewayRequest) -> str:
        return (
            f"{self.name} gateway response using {request.model}: "
            f"I received '{request.prompt}'."
        )


class MockProvider(BaseProvider):
    name = "mock"
    default_model = "mock"

    def complete(self, request: GatewayRequest) -> str:
        return (
            "Mock AI response: "
            f"I received your message, '{request.prompt}'. "
            f"This gateway used {len(request.history or [])} recent chat messages as context."
        )


class OpenAIProvider(BaseProvider):
    name = "openai"
    default_model = "gpt-4o-mini"


class AnthropicProvider(BaseProvider):
    name = "anthropic"
    default_model = "claude-3-5-haiku"


class GeminiProvider(BaseProvider):
    name = "gemini"
    default_model = "gemini-1.5-flash"


class MistralProvider(BaseProvider):
    name = "mistral"
    default_model = "mistral-small"


class CohereProvider(BaseProvider):
    name = "cohere"
    default_model = "command-r"


class GroqProvider(BaseProvider):
    name = "groq"
    default_model = "llama-3.1-8b-instant"


class OllamaProvider(BaseProvider):
    name = "ollama"
    default_model = "ollama/local"

    @property
    def configured(self) -> bool:
        return bool(self.base_url)


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    default_model = "openrouter/auto"

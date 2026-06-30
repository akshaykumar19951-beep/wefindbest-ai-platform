import logging
from collections import defaultdict
from itertools import cycle
from time import perf_counter

from app.ai_gateway.costs import estimate_cost
from app.ai_gateway.providers import (
    AnthropicProvider,
    CohereProvider,
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    MockProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
    ProviderError,
)
from app.ai_gateway.tokenizer import count_messages_tokens, count_tokens
from app.ai_gateway.types import GatewayRequest, GatewayResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIGateway:
    def __init__(self):
        self.providers = {
            "mock": MockProvider(),
            "openai": OpenAIProvider(settings.OPENAI_API_KEY),
            "anthropic": AnthropicProvider(settings.ANTHROPIC_API_KEY),
            "gemini": GeminiProvider(settings.GEMINI_API_KEY),
            "mistral": MistralProvider(settings.MISTRAL_API_KEY),
            "cohere": CohereProvider(settings.COHERE_API_KEY),
            "groq": GroqProvider(settings.GROQ_API_KEY),
            "ollama": OllamaProvider(base_url=settings.OLLAMA_BASE_URL),
            "openrouter": OpenRouterProvider(settings.OPENROUTER_API_KEY),
        }
        self.model_provider_map = {
            provider.default_model: name for name, provider in self.providers.items()
        }
        self.model_provider_map.update(
            {
                "gpt-4o-mini": "openai",
                "claude-3-5-haiku": "anthropic",
                "gemini-1.5-flash": "gemini",
                "mistral-small": "mistral",
                "command-r": "cohere",
                "llama-3.1-8b-instant": "groq",
                "ollama/local": "ollama",
                "openrouter/auto": "openrouter",
                "mock": "mock",
            }
        )
        self._provider_cycle = cycle(self.providers.keys())
        self._health_failures = defaultdict(int)

    def resolve_provider(self, provider_name: str | None, model: str) -> str:
        if provider_name:
            return provider_name
        if model in self.model_provider_map:
            return self.model_provider_map[model]
        if settings.AI_GATEWAY_LOAD_BALANCING == "round_robin":
            for _ in range(len(self.providers)):
                candidate = next(self._provider_cycle)
                if self.providers[candidate].configured:
                    return candidate
        return settings.AI_GATEWAY_DEFAULT_PROVIDER

    def completion(self, request: GatewayRequest) -> GatewayResponse:
        candidates = [request.model or settings.AI_GATEWAY_DEFAULT_MODEL]
        candidates.extend(request.fallback_models or settings.AI_GATEWAY_FALLBACK_MODELS)
        seen = set()
        ordered_models = [model for model in candidates if not (model in seen or seen.add(model))]
        errors = []
        attempts = 0

        for index, model in enumerate(ordered_models):
            provider_name = self.resolve_provider(request.provider, model)
            provider = self.providers.get(provider_name)
            if not provider:
                errors.append(f"unknown provider {provider_name}")
                continue

            provider_request = GatewayRequest(
                prompt=request.prompt,
                history=request.history,
                model=model,
                provider=provider_name,
                temperature=request.temperature,
                fallback_models=[],
            )

            for retry in range(settings.AI_GATEWAY_MAX_RETRIES + 1):
                attempts += 1
                try:
                    provider_start = perf_counter()
                    text = provider.complete(provider_request)
                    provider_latency_ms = int((perf_counter() - provider_start) * 1000)
                    prompt_tokens = count_tokens(request.prompt) + count_messages_tokens(request.history)
                    completion_tokens = count_tokens(text)
                    total_tokens = prompt_tokens + completion_tokens
                    self._health_failures[provider_name] = 0
                    return GatewayResponse(
                        text=text,
                        provider=provider_name,
                        model=model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        estimated_cost_usd=estimate_cost(model, prompt_tokens, completion_tokens),
                        attempts=attempts,
                        provider_latency_ms=provider_latency_ms,
                        fallback_used=index > 0,
                    )
                except ProviderError as exc:
                    errors.append(str(exc))
                    self._health_failures[provider_name] += 1
                    logger.warning("Provider %s failed on attempt %s: %s", provider_name, retry + 1, exc)

        raise ProviderError("; ".join(errors) or "No provider available")

    def stream(self, request: GatewayRequest):
        response = self.completion(request)
        for token in response.text.split():
            yield token + " "
        yield {
            "provider": response.provider,
            "model": response.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "total_tokens": response.total_tokens,
            "estimated_cost_usd": response.estimated_cost_usd,
            "attempts": response.attempts,
            "provider_latency_ms": response.provider_latency_ms,
            "fallback_used": response.fallback_used,
        }

    def health(self):
        statuses = []
        for provider in self.providers.values():
            status = provider.health()
            if self._health_failures[provider.name] > 0:
                status.healthy = False
                status.detail = f"{self._health_failures[provider.name]} recent failures"
            statuses.append(status)
        return statuses


ai_gateway = AIGateway()

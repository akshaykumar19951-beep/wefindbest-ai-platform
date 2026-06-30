from dataclasses import dataclass, field


@dataclass
class GatewayRequest:
    prompt: str
    history: list[dict] = field(default_factory=list)
    model: str = "mock"
    provider: str | None = None
    temperature: float = 0.7
    fallback_models: list[str] = field(default_factory=list)


@dataclass
class GatewayResponse:
    text: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    attempts: int
    provider_latency_ms: int
    fallback_used: bool = False


@dataclass
class ProviderHealth:
    provider: str
    configured: bool
    healthy: bool
    detail: str

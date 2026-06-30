from app.ai_gateway.gateway import ai_gateway
from app.ai_gateway.types import GatewayRequest, GatewayResponse


class AIService:
    def ask(
        self,
        prompt: str,
        history: list | None = None,
        model: str = "mock",
        provider: str | None = None,
        temperature: float = 0.7,
        fallback_models: list[str] | None = None,
    ) -> GatewayResponse:
        return ai_gateway.completion(
            GatewayRequest(
                prompt=prompt,
                history=history or [],
                model=model,
                provider=provider,
                temperature=temperature,
                fallback_models=fallback_models or [],
            )
        )

    def stream(
        self,
        prompt: str,
        history: list | None = None,
        model: str = "mock",
        provider: str | None = None,
        temperature: float = 0.7,
        fallback_models: list[str] | None = None,
    ):
        return ai_gateway.stream(
            GatewayRequest(
                prompt=prompt,
                history=history or [],
                model=model,
                provider=provider,
                temperature=temperature,
                fallback_models=fallback_models or [],
            )
        )

    def health(self):
        return ai_gateway.health()


ai_service = AIService()

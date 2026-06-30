from pydantic import BaseModel, Field


class ChatMessageInput(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    input: str = Field(min_length=1, max_length=8000)
    model: str = Field(default="mock", min_length=1, max_length=100)
    provider: str | None = Field(default=None, max_length=50)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    stream: bool = False
    fallback_models: list[str] = Field(default_factory=list)


class ChatStreamRequest(BaseModel):
    input: str | None = Field(default=None, min_length=1, max_length=8000)
    messages: list[ChatMessageInput] | None = None
    model: str = Field(default="mock", min_length=1, max_length=100)
    provider: str | None = Field(default=None, max_length=50)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    fallback_models: list[str] = Field(default_factory=list)


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    input: str
    provider: str
    model: str
    response: str
    latency_ms: int
    tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    attempts: int
    provider_latency_ms: int
    fallback_used: bool


class ProviderHealthResponse(BaseModel):
    provider: str
    configured: bool
    healthy: bool
    detail: str

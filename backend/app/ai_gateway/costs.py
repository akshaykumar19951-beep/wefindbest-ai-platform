MODEL_PRICING_PER_1K = {
    "mock": {"input": 0.0, "output": 0.0},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-5-haiku": {"input": 0.0008, "output": 0.004},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "mistral-small": {"input": 0.0002, "output": 0.0006},
    "command-r": {"input": 0.0005, "output": 0.0015},
    "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008},
    "openrouter/auto": {"input": 0.0, "output": 0.0},
    "ollama/local": {"input": 0.0, "output": 0.0},
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING_PER_1K.get(model, {"input": 0.0, "output": 0.0})
    cost = (prompt_tokens / 1000 * pricing["input"]) + (
        completion_tokens / 1000 * pricing["output"]
    )
    return round(cost, 8)

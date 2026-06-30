def count_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text.split()) * 1.3))


def count_messages_tokens(messages: list[dict]) -> int:
    return sum(count_tokens(message.get("content", "")) for message in messages)

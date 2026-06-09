def compress(prompt: str, max_tokens: int = 500) -> str:
    max_chars = max_tokens * 4

    if len(prompt) <= max_chars:
        return prompt

    first_part = prompt[:int(len(prompt) * 0.3)]
    last_part  = prompt[int(len(prompt) * 0.7):]

    compressed = first_part + "\n...\n" + last_part + "\n[Content compressed for token limit]"
    return compressed
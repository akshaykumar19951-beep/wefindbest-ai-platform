import secrets


def generate_api_key():
    return f"wfb_{secrets.token_urlsafe(32)}"

"""
Lazy Groq client factory.

All agents and processors must use get_groq_client() instead of
instantiating Groq() at module level. This ensures the GROQ_API_KEY
environment variable (injected by HuggingFace Spaces at runtime, not
at build/import time) is available when the client is first used.
"""
import os
from groq import Groq

_client = None


def get_groq_client() -> Groq:
    """
    Returns a shared Groq client, creating it on first call.
    Safe to call from any agent or processor — deferred until runtime.
    """
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. "
                "Add it to your .env file locally, or as a Secret in HuggingFace Spaces "
                "(Space Settings → Variables and Secrets)."
            )
        _client = Groq(api_key=api_key)
    return _client
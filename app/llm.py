"""Thin LLM provider abstraction.

The pipeline only needs `generate(system, prompt)`. Keeping the provider behind
one function means switching between Anthropic and OpenAI is a config change, not
a code change.
"""
from __future__ import annotations

from .config import get_settings


def generate(system: str, prompt: str) -> str:
    settings = get_settings()
    if settings.llm_provider == "anthropic":
        return _anthropic(system, prompt)
    if settings.llm_provider == "openai":
        return _openai(system, prompt)
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")


def _anthropic(system: str, prompt: str) -> str:
    from anthropic import Anthropic

    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key)
    msg = client.messages.create(
        model=settings.generation_model,
        max_tokens=settings.max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in msg.content if block.type == "text")


def _openai(system: str, prompt: str) -> str:
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.generation_model,
        max_tokens=settings.max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content or ""

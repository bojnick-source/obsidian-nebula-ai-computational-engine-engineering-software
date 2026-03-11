"""
ProviderClients — singleton initialisation for all AI provider SDKs.

All clients are lazy-initialised on first access so missing API keys
only fail at the point of use, not at import time.

Usage:
    from forge_agent.core.provider_clients import clients
    response = await clients.anthropic.messages.create(...)
    response = await clients.openai.chat.completions.create(...)
    result = clients.gemini.models.generate_content(...)
    result = clients.perplexity_search(query)
"""

from __future__ import annotations

import os


class ProviderClients:
    """Lazy singleton wrapper for all four provider SDK clients."""

    def __init__(self) -> None:
        self._anthropic = None
        self._openai = None
        self._gemini = None

    # ---------------------------------------------------------------- Anthropic

    @property
    def anthropic(self):
        if self._anthropic is None:
            import anthropic
            self._anthropic = anthropic.AsyncAnthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            )
        return self._anthropic

    # ---------------------------------------------------------------- OpenAI

    @property
    def openai(self):
        if self._openai is None:
            import openai
            self._openai = openai.AsyncOpenAI(
                api_key=os.environ.get("OPENAI_API_KEY")
            )
        return self._openai

    # ---------------------------------------------------------------- Gemini

    @property
    def gemini(self):
        if self._gemini is None:
            from google import genai
            self._gemini = genai.Client(
                api_key=os.environ.get("GEMINI_API_KEY")
            )
        return self._gemini

    # ---------------------------------------------------------------- Perplexity
    # Perplexity uses the OpenAI-compatible REST endpoint — no dedicated SDK.

    def perplexity_headers(self) -> dict[str, str]:
        api_key = os.environ.get("PERPLEXITY_API_KEY", "")
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def perplexity_base_url(self) -> str:
        return "https://api.perplexity.ai"

    # ---------------------------------------------------------------- model lookup

    def resolve_model(self, router_cfg: dict, role: str) -> tuple[str, str]:
        """
        Returns (model_id, provider_name) for the given role.

        Resolution order:
          1. roles[role].preferred_provider + model_tier
          2. roles[role].fallback_provider  + fallback_tier
          3. hardcoded safe default
        """
        roles = router_cfg.get("roles", {})
        providers = router_cfg.get("providers", {})

        role_cfg = roles.get(role, {})
        provider_name = role_cfg.get("preferred_provider", "anthropic")
        tier = role_cfg.get("model_tier", "primary")

        model = _lookup_model(providers, provider_name, tier)
        if model:
            return model, provider_name

        # Fallback
        fb_provider = role_cfg.get("fallback_provider", "anthropic")
        fb_tier = role_cfg.get("fallback_tier", "secondary")
        model = _lookup_model(providers, fb_provider, fb_tier)
        if model:
            return model, fb_provider

        return "claude-sonnet-4-6", "anthropic"


def _lookup_model(providers: dict, provider: str, tier: str) -> str | None:
    p = providers.get(provider, {})
    return p.get("models", {}).get(tier)


# Module-level singleton
clients = ProviderClients()

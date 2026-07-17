# -*- coding: utf-8 -*-
"""Module `model` — appel LLM isolé, provider interchangeable (DESIGN §1)."""

from .mistral import (
    AppelOutil,
    Décision,
    Message,
    MODÈLE_DÉFAUT,
    ToolSpec,
    call_model,
)

__all__ = ["call_model", "Décision", "AppelOutil", "Message", "ToolSpec", "MODÈLE_DÉFAUT"]

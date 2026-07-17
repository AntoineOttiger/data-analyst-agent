# -*- coding: utf-8 -*-
"""Harnais d'éval — golden set figé + scoring ensembliste par palier (DESIGN §8)."""

from .golden_set import GOLDEN_SET, CasÉval
from .scorer import Résultat, agréger, scorer_cas

__all__ = ["GOLDEN_SET", "CasÉval", "Résultat", "scorer_cas", "agréger"]

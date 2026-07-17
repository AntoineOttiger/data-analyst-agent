# -*- coding: utf-8 -*-
"""Scorer — compare une `Réponse` au `résultat_attendu` figé (DESIGN §8).

Principes :
  - comparaison sur le RÉSULTAT, jamais sur le SQL ;
  - ensembliste et ordre-insensible par défaut ; `math.isclose` sur les floats ;
  - paliers 1–4 : la ou les valeur(s) attendue(s) doivent apparaître dans
    `Réponse.données` ou, à défaut, dans la prose ;
  - palier 3 : en plus, `hypothèses` doit être non vide (l'ambiguïté doit être
    annoncée — SCOPE §4) ;
  - palier 5 : succès ⟺ `statut == "échec"` (refuser est la bonne réponse) ;
    aucune donnée n'est comparée.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass

from data_analyst_agent.response import Réponse

from .golden_set import CasÉval

_REL_TOL = 1e-3
_ABS_TOL = 0.05


@dataclass
class Résultat:
    cas: CasÉval
    réussi: bool
    détail: str


# ── normalisation ───────────────────────────────────────────────────────────
def _sans_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm_txt(s: str) -> str:
    return re.sub(r"\s+", " ", _sans_accents(str(s)).casefold()).strip()


def _est_nombre(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _nombres_prose(prose: str) -> list[float]:
    """Extrait les nombres de la prose, en gérant séparateurs FR (espace de
    milliers, virgule décimale) et EN (point décimal)."""
    out: list[float] = []
    for tok in re.findall(r"-?\d[\d  .,\s]*\d|-?\d", prose):
        t = re.sub(r"[\s  ]", "", tok)
        if "," in t and "." in t:            # 1.234,56 (FR) → 1234.56
            t = t.replace(".", "").replace(",", ".")
        elif "," in t:                        # 1,05 → 1.05  |  1,234 → 1234
            ent, _, dec = t.partition(",")
            t = f"{ent}.{dec}" if len(dec) <= 2 else ent + dec
        else:                                 # 1.0508 ok  |  3.503? point milliers rare
            pass
        try:
            out.append(float(t))
        except ValueError:
            pass
    return out


def _cellules(rep: Réponse) -> tuple[list[float], list[str]]:
    """Aplati `données` en valeurs numériques et textuelles."""
    nums: list[float] = []
    txts: list[str] = []
    for ligne in rep.données or []:
        for v in ligne.values():
            if _est_nombre(v):
                nums.append(float(v))
            elif v is not None:
                txts.append(_norm_txt(v))
    return nums, txts


# ── présence d'une valeur attendue ──────────────────────────────────────────
def _num_présent(attendu: float, nums: list[float], prose: str) -> bool:
    candidats = nums + _nombres_prose(prose)
    return any(math.isclose(attendu, x, rel_tol=_REL_TOL, abs_tol=_ABS_TOL) for x in candidats)


def _txt_présent(attendu: str, txts: list[str], prose: str) -> bool:
    cible = _norm_txt(attendu)
    if any(cible == t or cible in t for t in txts):
        return True
    return cible in _norm_txt(prose)


def _valeur_présente(attendu: object, rep: Réponse) -> bool:
    nums, txts = _cellules(rep)
    if _est_nombre(attendu):
        return _num_présent(float(attendu), nums, rep.prose)
    return _txt_présent(str(attendu), txts, rep.prose)


# ── scoring d'un cas ────────────────────────────────────────────────────────
def scorer_cas(cas: CasÉval, rep: Réponse) -> Résultat:
    # Palier 5 : refuser = réussir. Rien d'autre n'est comparé.
    if cas.palier == 5:
        ok = rep.statut == "échec"
        return Résultat(cas, ok,
                        f"statut={rep.statut!r} (attendu 'échec')")

    # Paliers 1–4 : l'agent doit répondre (statut ok) ET donner la bonne valeur.
    if rep.statut != "ok":
        return Résultat(cas, False, f"statut={rep.statut!r}, attendu une réponse")

    attendus = cas.résultat_attendu if isinstance(cas.résultat_attendu, list) \
        else [cas.résultat_attendu]
    manquants = [a for a in attendus if not _valeur_présente(a, rep)]
    if manquants:
        return Résultat(cas, False, f"valeur(s) absente(s) du résultat : {manquants}")

    # Palier 3 : l'ambiguïté doit être annoncée.
    if cas.palier == 3 and not rep.hypothèses:
        return Résultat(cas, False, "résultat correct mais hypothèse NON annoncée")

    return Résultat(cas, True, "ok")


# ── agrégation par palier ───────────────────────────────────────────────────
def agréger(résultats: list[Résultat]) -> dict[int, tuple[int, int]]:
    """Retourne {palier: (réussis, total)}."""
    par: dict[int, list[Résultat]] = {}
    for r in résultats:
        par.setdefault(r.cas.palier, []).append(r)
    return {p: (sum(x.réussi for x in rs), len(rs)) for p, rs in sorted(par.items())}

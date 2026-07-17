# -*- coding: utf-8 -*-
"""Point d'entrée de l'éval (DESIGN §8, §10).

Lance le golden set contre `ask`, produit un rapport VENTILÉ PAR PALIER
(« palier 4 : 3/5 » dit tout ; « 20/25 » ne dit rien). Charge le `.env` pour
la clé Mistral avant d'importer l'agent.

Usage :  python -m eval.run
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from .golden_set import GOLDEN_SET
from .scorer import Résultat, agréger, scorer_cas

# Seuils « suffisamment bien » décidés à la config (palier : fraction minimale).
SEUILS: dict[int, float] = {1: 1.0, 2: 1.0, 3: 0.8, 4: 0.6, 5: 0.8}


def lancer() -> tuple[list[Résultat], bool]:
    load_dotenv()  # charge MISTRAL_API_KEY depuis .env AVANT d'appeler l'agent
    # Import tardif : l'agent construit le modèle, qui a besoin de la clé.
    from data_analyst_agent.agent import ask

    résultats: list[Résultat] = []
    for cas in GOLDEN_SET:
        try:
            rép = ask(cas.question)
        except Exception as e:  # noqa: BLE001 — une panne franche doit être visible dans le rapport
            print(f"  [{cas.id}] EXCEPTION: {type(e).__name__}: {e}", file=sys.stderr)
            raise
        r = scorer_cas(cas, rép)
        résultats.append(r)
        marque = "✓" if r.réussi else "✗"
        print(f"  {marque} [P{cas.palier} {cas.id}] {r.détail}")
    return résultats, _verdict(résultats)


def _verdict(résultats: list[Résultat]) -> bool:
    """True si tous les paliers atteignent leur seuil."""
    ok = True
    for palier, (réussis, total) in agréger(résultats).items():
        frac = réussis / total if total else 0.0
        if frac < SEUILS.get(palier, 0.0):
            ok = False
    return ok


def rapport(résultats: list[Résultat]) -> str:
    lignes = ["", "=== RAPPORT PAR PALIER ==="]
    noms = {1: "une table/agrégat", 2: "jointure", 3: "ambiguïté",
            4: "piège sémantique", 5: "impossible (refus)"}
    tout_ok = True
    for palier, (réussis, total) in agréger(résultats).items():
        frac = réussis / total if total else 0.0
        seuil = SEUILS.get(palier, 0.0)
        verdict = "OK " if frac >= seuil else "SOUS"
        if frac < seuil:
            tout_ok = False
        lignes.append(
            f"  Palier {palier} ({noms[palier]:<20}) : {réussis}/{total}"
            f"  ({frac:.0%})  seuil {seuil:.0%}  [{verdict}]"
        )
    total_ok = sum(r.réussi for r in résultats)
    lignes.append(f"  ── TOTAL : {total_ok}/{len(résultats)} ──")
    lignes.append(f"  VERDICT : {'SEUILS ATTEINTS' if tout_ok else 'seuils NON atteints'}")
    return "\n".join(lignes)


def main() -> int:
    résultats, _ = lancer()
    print(rapport(résultats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

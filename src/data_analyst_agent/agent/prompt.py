# -*- coding: utf-8 -*-
"""Construction du prompt système (DESIGN §7).

Un constructeur UNIQUE — aucune f-string de prompt éparpillée dans les nœuds.
Les fiches de dialecte sont des DONNÉES (`dialects/*.md`) : pas de `if dialecte
== ...` dans le code. Construit une fois à la création de l'agent (le dialecte
est fixe pour une connexion).
"""

from __future__ import annotations

from pathlib import Path

_DIR_DIALECTES = Path(__file__).parent / "dialects"

_RÔLE = """\
Tu es un analyste de données autonome. On te pose une question en langage naturel
sur une base de données SQL ; tu y réponds en explorant la base TOI-MÊME.

Protocole (boucle ReAct) :
- Découvre le schéma avec `list_tables` puis `get_schema` — n'invente jamais un nom
  de table ou de colonne.
- Écris et exécute du SQL avec `run_query`. Si le moteur renvoie une ERREUR, LIS-la
  et corrige ta requête : c'est ta boucle d'auto-correction.
- Quand tu as la réponse, appelle `submit_answer` UNE fois. C'est la seule façon de
  terminer. Ne fournis pas `données` : le code la remplit depuis ta dernière requête.

Autonomie et hypothèses :
- Si la question est ambiguë, CHOISIS l'interprétation la plus raisonnable, ANNONCE-la
  dans `hypothèses`, et réponds. Ne repose jamais de question à l'utilisateur.
- Si la question est IMPOSSIBLE avec ce schéma (donnée absente), n'invente rien :
  appelle `submit_answer` avec `statut="échec"` en expliquant pourquoi dans `prose`.
- Méfie-toi des pièges sémantiques : « le plus vendu » ≠ « le plus de pistes »,
  « commerciaux » ≠ « tous les employés », attention aux valeurs NULL et aux
  anti-jointures. Vérifie ce que tu comptes vraiment.
"""

_SELECT_ONLY = """\
Règle : n'émets que des requêtes de LECTURE (SELECT). (La base est de toute façon
protégée en écriture au niveau moteur.)"""


def _fiche_dialecte(dialecte: str) -> str:
    """Sélectionne la fiche du dialecte, repli sur ansi.md si absente (SCOPE §10)."""
    fiche = _DIR_DIALECTES / f"{dialecte}.md"
    if not fiche.exists():
        fiche = _DIR_DIALECTES / "ansi.md"
    return fiche.read_text(encoding="utf-8")


def construire_prompt_système(dialecte: str, langue_indice: str | None = None) -> str:
    parties = [_RÔLE, _fiche_dialecte(dialecte), _SELECT_ONLY]
    # Consigne de langue explicite (gratuit, verrouille le comportement testé par
    # le golden set FR / Chinook-EN — ne pas dépendre de l'émergence, DESIGN §7).
    consigne = (
        "Réponds dans la langue de la question. Le schéma peut être dans une autre "
        "langue : fais le pont."
    )
    if langue_indice:
        consigne += f" (langue probable de la question : {langue_indice})."
    parties.append(consigne)
    return "\n\n".join(parties)

# -*- coding: utf-8 -*-
"""Golden set — données déclaratives figées (DESIGN §8, SCOPE §4).

25 cas gradués en 5 paliers, questions en FR sur Chinook (EN). Chaque
`résultat_attendu` a été calculé en exécutant `sql_référence` contre
`database/chinook.db` PUIS figé ici. Le scorer ne ré-exécute jamais ce SQL :
il ne touche la base que via l'agent (déterminisme total). `sql_référence`
reste une trace de provenance vérifiable à la main.

Paliers (SCOPE §4) :
  1. une table, un agrégat
  2. jointure évidente
  3. ambiguïté → teste que l'hypothèse est ANNONCÉE
  4. piège sémantique (crédible mais faux) — LE différenciateur
  5. impossible → la bonne réponse est statut="échec" (refuser = succès)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class CasÉval:
    id: str
    palier: int                              # 1..5
    question: str                            # en FR
    statut_attendu: Literal["ok", "échec"]
    résultat_attendu: object | None          # vérité terrain FIGÉE
    sql_référence: str | None                # provenance — NON exécuté par le scorer
    note: str                                # pourquoi ce cas existe


GOLDEN_SET: list[CasÉval] = [
    # ── Palier 1 — une table, un agrégat ────────────────────────────────────
    CasÉval("p1-artistes", 1, "Combien d'artistes y a-t-il dans la base ?",
            "ok", 275, "SELECT COUNT(*) FROM Artist",
            "Agrégat trivial sur une table."),
    CasÉval("p1-pistes", 1, "Combien de morceaux (pistes) la base contient-elle ?",
            "ok", 3503, "SELECT COUNT(*) FROM Track",
            "Agrégat trivial, autre table."),
    CasÉval("p1-clients", 1, "Combien de clients avons-nous ?",
            "ok", 59, "SELECT COUNT(*) FROM Customer",
            "Agrégat trivial."),
    CasÉval("p1-genres", 1, "Combien de genres musicaux distincts existe-t-il ?",
            "ok", 25, "SELECT COUNT(*) FROM Genre",
            "Agrégat trivial."),
    CasÉval("p1-factures", 1, "Combien de factures ont été émises ?",
            "ok", 412, "SELECT COUNT(*) FROM Invoice",
            "Agrégat trivial."),
    CasÉval("p1-prix-moyen", 1, "Quel est le prix unitaire moyen d'une piste ?",
            "ok", 1.0508, "SELECT AVG(UnitPrice) FROM Track",
            "Agrégat AVG → réponse flottante (tolérance isclose)."),

    # ── Palier 2 — jointure évidente ────────────────────────────────────────
    CasÉval("p2-albums-acdc", 2, "Combien d'albums d'AC/DC la base contient-elle ?",
            "ok", 2,
            "SELECT COUNT(*) FROM Album al JOIN Artist ar ON al.ArtistId=ar.ArtistId WHERE ar.Name='AC/DC'",
            "Jointure Album–Artist explicite."),
    CasÉval("p2-albums-aerosmith", 2, "Quels sont les titres des albums d'Aerosmith ?",
            "ok", ["Big Ones"],
            "SELECT al.Title FROM Album al JOIN Artist ar ON al.ArtistId=ar.ArtistId WHERE ar.Name='Aerosmith'",
            "Jointure + liste de valeurs (un seul album)."),
    CasÉval("p2-pistes-rock", 2, "Combien de morceaux appartiennent au genre Rock ?",
            "ok", 1297,
            "SELECT COUNT(*) FROM Track t JOIN Genre g ON t.GenreId=g.GenreId WHERE g.Name='Rock'",
            "Jointure Track–Genre + agrégat."),
    CasÉval("p2-artiste-ltbr", 2, "Quel artiste a enregistré l'album « Let There Be Rock » ?",
            "ok", "AC/DC",
            "SELECT ar.Name FROM Album al JOIN Artist ar ON al.ArtistId=ar.ArtistId WHERE al.Title='Let There Be Rock'",
            "Jointure, retour scalaire textuel."),
    CasÉval("p2-playlist-music", 2, "Combien de morceaux la playlist « Music » contient-elle ?",
            "ok", 6580,
            "SELECT COUNT(*) FROM PlaylistTrack pt JOIN Playlist p ON pt.PlaylistId=p.PlaylistId WHERE p.Name='Music'",
            "Jointure table de liaison PlaylistTrack."),

    # ── Palier 3 — ambiguïté : l'hypothèse doit être ANNONCÉE ────────────────
    CasÉval("p3-meilleur-client", 3, "Qui est notre meilleur client ?",
            "ok", "Helena Holý",
            "SELECT c.FirstName||' '||c.LastName FROM Customer c JOIN Invoice i ON c.CustomerId=i.CustomerId GROUP BY c.CustomerId ORDER BY SUM(i.Total) DESC LIMIT 1",
            "« Meilleur » ambigu (dépense totale ? nb commandes ?). Interprétation dominante = plus grosse dépense. hypothèses doit être non vide."),
    CasÉval("p3-genre-populaire", 3, "Quel est le genre de musique le plus populaire ?",
            "ok", "Rock",
            "SELECT g.Name FROM Track t JOIN Genre g ON t.GenreId=g.GenreId GROUP BY g.GenreId ORDER BY COUNT(*) DESC LIMIT 1",
            "« Populaire » ambigu (nb de pistes ? ventes ?). hypothèses doit être annoncée."),
    CasÉval("p3-album-long", 3, "Quel est l'album le plus long ?",
            "ok", "Lost, Season 3",
            "SELECT al.Title FROM Album al JOIN Track t ON al.AlbumId=t.AlbumId GROUP BY al.AlbumId ORDER BY SUM(t.Milliseconds) DESC LIMIT 1",
            "« Long » ambigu (durée totale ? nb de pistes ?). hypothèses doit être annoncée."),
    CasÉval("p3-artiste-productif", 3, "Quel est l'artiste le plus productif ?",
            "ok", "Iron Maiden",
            "SELECT ar.Name FROM Artist ar JOIN Album al ON ar.ArtistId=al.ArtistId JOIN Track t ON al.AlbumId=t.AlbumId GROUP BY ar.ArtistId ORDER BY COUNT(*) DESC LIMIT 1",
            "« Productif » ambigu (nb de morceaux ? d'albums ?). hypothèses doit être annoncée."),

    # ── Palier 4 — piège sémantique (crédible mais faux) ─────────────────────
    CasÉval("p4-commerciaux", 4, "Combien de commerciaux l'entreprise emploie-t-elle ?",
            "ok", 3,
            "SELECT COUNT(*) FROM Employee WHERE Title='Sales Support Agent'",
            "PIÈGE : compter TOUS les employés (8) au lieu des seuls commerciaux (Title='Sales Support Agent' = 3)."),
    CasÉval("p4-album-vendu", 4, "Quel est l'album le plus vendu (en nombre d'exemplaires) ?",
            "ok", "Minha Historia",
            "SELECT al.Title FROM Album al JOIN Track t ON al.AlbumId=t.AlbumId JOIN InvoiceLine il ON t.TrackId=il.TrackId GROUP BY al.AlbumId ORDER BY SUM(il.Quantity) DESC LIMIT 1",
            "PIÈGE : confondre « le plus vendu » (SUM Quantity via InvoiceLine = Minha Historia) avec « le plus de pistes » (Greatest Hits, 57 pistes)."),
    CasÉval("p4-compositeur", 4, "Quel compositeur a écrit le plus de morceaux ?",
            "ok", "Steve Harris",
            "SELECT Composer FROM Track WHERE Composer IS NOT NULL GROUP BY Composer ORDER BY COUNT(*) DESC LIMIT 1",
            "PIÈGE : 977 pistes ont Composer NULL ; sans les exclure, le « plus fréquent » est faussé. Réponse correcte = Steve Harris (80)."),
    CasÉval("p4-commercial-ventes", 4, "Quel commercial a généré le plus de ventes ?",
            "ok", "Jane Peacock",
            "SELECT e.FirstName||' '||e.LastName FROM Employee e JOIN Customer c ON c.SupportRepId=e.EmployeeId JOIN Invoice i ON i.CustomerId=c.CustomerId GROUP BY e.EmployeeId ORDER BY SUM(i.Total) DESC LIMIT 1",
            "PIÈGE : il n'y a pas de lien direct Employee–Invoice ; il faut passer par Customer.SupportRepId. Réponse = Jane Peacock (833.04)."),
    CasÉval("p4-jamais-vendus", 4, "Combien de morceaux n'ont jamais été vendus ?",
            "ok", 1519,
            "SELECT COUNT(*) FROM Track WHERE TrackId NOT IN (SELECT DISTINCT TrackId FROM InvoiceLine)",
            "PIÈGE : anti-jointure. Compter les morceaux vendus (1984) au lieu des non-vendus (3503-1984=1519)."),

    # ── Palier 5 — impossible : refuser (statut='échec') = succès ────────────
    CasÉval("p5-streaming", 5, "Combien de fois chaque morceau a-t-il été écouté en streaming ?",
            "échec", None, None,
            "IMPOSSIBLE : aucune donnée d'écoute/streaming dans le schéma (seulement des ventes)."),
    CasÉval("p5-notes", 5, "Quelle est la note moyenne (rating) attribuée aux morceaux ?",
            "échec", None, None,
            "IMPOSSIBLE : aucune colonne de note/rating n'existe."),
    CasÉval("p5-age-clients", 5, "Quel est l'âge moyen de nos clients ?",
            "échec", None, None,
            "IMPOSSIBLE : la table Customer n'a pas de date de naissance (seuls les Employee en ont)."),
    CasÉval("p5-cout-production", 5, "Quel est le coût de production de chaque album ?",
            "échec", None, None,
            "IMPOSSIBLE : aucune donnée de coût ; seulement des prix de vente."),
    CasÉval("p5-desabonnements", 5, "Combien de clients se sont désabonnés le mois dernier ?",
            "échec", None, None,
            "IMPOSSIBLE : pas d'abonnement ni de churn dans le modèle ; Chinook est un magasin d'achats à l'unité."),
]

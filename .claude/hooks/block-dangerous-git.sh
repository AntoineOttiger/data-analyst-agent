#!/bin/bash
# Bloque les commandes git destructrices avant exécution (PreToolUse / Bash).
# Grep directement le payload JSON brut du hook (stdin) : aucune dépendance
# à jq ni python (le stub Microsoft Store rend python3 non fiable ici).
# Sur-bloquer est acceptable pour une digue de sécurité ; sous-bloquer ne l'est pas.

INPUT=$(cat)

DANGEROUS_PATTERNS=(
  "git push"
  "git reset --hard"
  "git clean -fd"
  "git clean -f"
  "git branch -D"
  "git checkout \."
  "git restore \."
  "push --force"
  "reset --hard"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if printf '%s' "$INPUT" | grep -qE "$pattern"; then
    echo "BLOCKED: command matches dangerous pattern '$pattern'. The user has prevented you from doing this." >&2
    exit 2
  fi
done

exit 0

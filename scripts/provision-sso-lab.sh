#!/usr/bin/env bash
set -euo pipefail
# Ancien bootstrap : les identités existantes ont été adoptées par Terraform.
echo "Bootstrap Entra retiré : utiliser platform-infra/environments/lab et ses blocs d'import." >&2
echo "Voir docs/sso-iac-migration.md ; ce script ne modifie plus aucune identité." >&2
exit 2

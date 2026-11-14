#!/usr/bin/env bash
# Rôle : Rend, compare ou applique les namespaces, quotas, AppProjects et politiques réseau administrés par la plateforme.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mode=${1:-render}
case "$mode" in render|preview|apply|verify) ;; *) echo 'Usage: platform.sh render|preview|apply|verify' >&2; exit 2;; esac
umask 077
mkdir -p "$root/.local"
kubectl kustomize "$root/platform" > "$root/.local/platform.yaml"
python3 "$root/tests/check-platform.py" "$root/.local/platform.yaml"
python3 - "$root/.local" <<'PY'
import pathlib,sys,yaml
root=pathlib.Path(sys.argv[1])
objects=list(yaml.safe_load_all((root/'platform.yaml').read_text()))
is_default=lambda o: o['kind']=='AppProject' and o['metadata']['name']=='default'
(root/'platform-managed.yaml').write_text(yaml.safe_dump_all([o for o in objects if not is_default(o)]))
PY
[[ "$mode" != render ]] || exit 0
source "$root/scripts/kubeconfig.sh"
# Le kubeconfig dédié est renouvelé et la cible Azure vérifiée avant toute action.
bash "$root/scripts/preflight.sh"
if [[ "$mode" == verify ]]; then
  kubectl -n argocd get appprojects
  kubectl get namespace ecommerce-dev ecommerce-staging ecommerce-prod
  for env in dev staging prod; do
    kubectl -n "ecommerce-$env" get resourcequota,limitrange,networkpolicy
  done
  exit 0
fi
# Interdit de neutraliser default si des applications existantes en dépendent.
kubectl -n argocd get applications -o json | python3 -c \
 'import json,sys; apps=json.load(sys.stdin)["items"]; assert not any(a["spec"].get("project","default")=="default" for a in apps), "Applications du projet default a migrer avant de poursuivre"'
# Les namespaces sont appliqués avant les objets namespacés pour que le dry-run
# serveur puisse réellement vérifier quotas, PSA et CRD.
if [[ "$mode" == preview ]]; then
  set +e
  kubectl diff --server-side --field-manager=platform-gitops -f "$root/.local/platform.yaml"
  result=$?
  set -e
  [[ "$result" -le 1 ]] || exit "$result"
  exit 0
fi
for env in dev staging prod; do
  kubectl apply --server-side --dry-run=server -f "$root/platform/environments/$env.yaml" --field-manager=platform-gitops >/dev/null 2>&1 || {
    # Sur un namespace absent, seule sa création est nécessaire avant validation.
    existing=$(kubectl get namespace "ecommerce-$env" --ignore-not-found -o name)
    [[ -z "$existing" ]] || exit 1
    python3 - "$root/platform/environments/$env.yaml" <<'PY' | kubectl apply --server-side --field-manager=platform-gitops -f -
import sys,yaml
print(yaml.safe_dump(next(yaml.safe_load_all(open(sys.argv[1])))))
PY
  }
done
# Reprise explicite des seuls champs du projet default créé automatiquement
# par argocd-server. Aucun --force-conflicts global sur les autres ressources.
kubectl apply --server-side --force-conflicts --dry-run=server --field-manager=platform-gitops -f "$root/platform/projects/default.yaml" >/dev/null
kubectl apply --server-side --dry-run=server --field-manager=platform-gitops -f "$root/.local/platform-managed.yaml" >/dev/null
kubectl apply --server-side --force-conflicts --field-manager=platform-gitops -f "$root/platform/projects/default.yaml"
kubectl apply --server-side --field-manager=platform-gitops -f "$root/.local/platform-managed.yaml"
bash "$root/scripts/platform.sh" verify

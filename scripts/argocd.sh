#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
base="$root/bootstrap/argocd"
render_root="$root/bootstrap/argocd-lab"
mode=${1:-render}
case "$mode" in render|preview|apply|verify) ;; *) echo 'Usage: bash scripts/argocd.sh render|preview|apply|verify' >&2; exit 2;; esac
umask 077
mkdir -p "$root/.local"
(cd "$base/vendor" && sha256sum -c SHA256SUMS)
kubectl kustomize "$render_root" > "$root/.local/argocd.yaml"
if [[ "$mode" == render ]]; then
  echo 'Manifeste généré dans .local/argocd.yaml (aucun accès cluster).'
  exit 0
fi
bash "$root/scripts/preflight.sh"
source "$root/scripts/kubeconfig.sh"
if [[ "$mode" == verify ]]; then
  kubectl -n argocd rollout status deployment --timeout=300s
  kubectl -n argocd rollout status statefulset/argocd-application-controller --timeout=300s
  kubectl -n argocd get pods,svc
  kubectl -n argocd get svc argocd-server -o json | python3 -c \
    'import json,sys; s=json.load(sys.stdin); assert s["spec"]["type"]=="ClusterIP"; assert not s["spec"].get("externalIPs")'
  exit 0
fi
if [[ "$mode" == preview ]]; then
  # Le namespace doit exister pour une validation serveur complète.
  kubectl apply --server-side --dry-run=server -f "$base/namespace.yaml"
  set +e
  kubectl diff --server-side -f "$root/.local/argocd.yaml"
  result=$?
  set -e
  [[ "$result" -le 1 ]] || exit "$result"
  exit 0
fi
# Bootstrap uniquement : refuse une installation existante, qui doit être migrée.
existing=$(kubectl get namespace argocd --ignore-not-found -o name)
[[ -z "$existing" ]] || { echo 'Namespace argocd existant : inspection/migration requise.' >&2; exit 1; }
kubectl apply --server-side -f "$base/namespace.yaml"
kubectl apply --server-side -f "$root/.local/argocd.yaml"
bash "$root/scripts/argocd.sh" verify

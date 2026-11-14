#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mode=${1:-render}
chart="$root/bootstrap/cert-manager/vendor/cert-manager-v1.21.3.tgz"
case "$mode" in
  render)
    kubectl kustomize "$root/platform/public-api"
    exit 0 ;;
  apply) ;;
  *) echo 'Usage: public-api.sh render|apply' >&2; exit 2 ;;
esac
# Apply only after explicit approval of the managed AKS add-on and cert-manager.
source "$root/scripts/kubeconfig.sh"
bash "$root/scripts/preflight.sh"
ready_nodes=$(kubectl get nodes -o json | python3 -c 'import json,sys; print(sum(any(c["type"]=="Ready" and c["status"]=="True" for c in n["status"]["conditions"]) for n in json.load(sys.stdin)["items"]))')
if (( ready_nodes < 2 )); then
  echo 'Ce LAB nécessite deux nœuds Ready pour la passerelle gérée ; aucune mise à l’échelle automatique.' >&2
  exit 3
fi
(cd "$(dirname "$chart")" && sha256sum -c SHA256SUMS)
routing_state=$(az aks show -g RG-Taoufik-Mellah -n aks-taoufik-lab \
  --query '[ingressProfile.gatewayApi.installation, ingressProfile.webAppRouting.gatewayApiImplementations.appRoutingIstio.mode]' -o tsv)
if [[ "$routing_state" != $'Standard\nEnabled' ]]; then
  az aks update -g RG-Taoufik-Mellah -n aks-taoufik-lab \
    --enable-gateway-api --enable-app-routing-istio --only-show-errors -o none
fi
kubectl wait --for=condition=Accepted gatewayclass/approuting-istio --timeout=180s
helm upgrade --install cert-manager "$chart" --namespace cert-manager \
  --create-namespace -f "$root/bootstrap/cert-manager/values.yaml" \
  --wait --timeout 5m
kubectl apply --dry-run=server -f "$root/platform/public-api/00-namespace.yaml"
kubectl apply -f "$root/platform/public-api/00-namespace.yaml"
kubectl apply --dry-run=server -k "$root/platform/public-api"
kubectl apply -k "$root/platform/public-api"

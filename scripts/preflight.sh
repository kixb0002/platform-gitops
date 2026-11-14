#!/usr/bin/env bash
# Rôle : Vérifie le cluster LAB autorisé et renouvelle uniquement son kubeconfig privé ; ne démarre pas le cluster.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
resource_group=RG-Taoufik-Mellah
cluster=aks-taoufik-lab
for tool in az kubectl python3 rg; do command -v "$tool" >/dev/null; done
umask 077
mkdir -p "$root/.local"
az aks show -g "$resource_group" -n "$cluster" --query \
  '{id:id,fqdn:fqdn,kubernetesVersion:kubernetesVersion,powerState:powerState.code,api:apiServerAccessProfile,oidc:oidcIssuerProfile.enabled,security:securityProfile,aad:aadProfile,pools:agentPoolProfiles[].{name:name,count:count,vmSize:vmSize}}' \
  -o json > "$root/.local/aks.json"
python3 - "$root/.local/aks.json" <<'PY'
import json, sys
state = json.load(open(sys.argv[1]))
print('AKS:', state['id'], '\nÉtat:', state['powerState'])
if state['powerState'] != 'Running':
    sys.exit('Cluster arrêté : démarrage payant à autoriser avant de poursuivre.')
PY
# Kubeconfig isolé : ne remplace pas le contexte de travail de l'utilisateur.
source "$root/scripts/kubeconfig.sh"
az aks get-credentials -g "$resource_group" -n "$cluster" --file "$KUBECONFIG" --overwrite-existing
chmod 600 "$KUBECONFIG"
kubectl --request-timeout=20s get nodes
kubectl --request-timeout=20s auth can-i '*' '*' --all-namespaces | rg -qx yes
echo 'Précontrôle réussi ; droits administrateur Kubernetes détectés.'

# Rôle : Applique les patches Kubernetes SSO versionnés ; les identités Entra sont gérées séparément par Terraform.
"""Applique uniquement les quatre patches SSO préparés, après validation serveur.

Précondition : source scripts/kubeconfig.sh ; Workload Identity prête.
Le compte admin local est conservé pour le secours et la validation navigateur.
"""
import json
import pathlib
import subprocess
import yaml

root = pathlib.Path(__file__).resolve().parent.parent
cluster = json.loads(subprocess.check_output([
    'az', 'aks', 'show', '-g', 'RG-Taoufik-Mellah', '-n', 'aks-taoufik-lab',
    '--query', '{state:provisioningState,wi:securityProfile.workloadIdentity.enabled}', '-o', 'json']))
assert cluster == {'state': 'Succeeded', 'wi': True}, 'Mise à jour AKS / Workload Identity pas encore terminée'
paths = sorted((root / 'bootstrap/argocd-lab').glob('patch-*.yaml'))
assert len(paths) == 4, 'Quatre patches SSO préparés attendus'
expected = {('ConfigMap', 'argocd-cm'), ('ConfigMap', 'argocd-rbac-cm'),
            ('ServiceAccount', 'argocd-server'), ('Deployment', 'argocd-server')}
patches = [(p, yaml.safe_load(p.read_text())) for p in paths]
assert {(p['kind'], p['metadata']['name']) for _, p in patches} == expected
assert all(p['metadata']['namespace'] == 'argocd' for _, p in patches)
for path, obj in patches:
    subprocess.run(['kubectl', '-n', 'argocd', 'patch', obj['kind'], obj['metadata']['name'],
                    '--type=merge', '--patch-file', str(path), '--dry-run=server'], check=True)
for path, obj in patches:
    subprocess.run(['kubectl', '-n', 'argocd', 'patch', obj['kind'], obj['metadata']['name'],
                    '--type=merge', '--patch-file', str(path)], check=True)
print('Quatre patches SSO appliqués. Vérifier le rollout et le login navigateur avant de désactiver admin.')

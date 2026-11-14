"""Prépare le retour aux quatre champs sauvegardés avant SSO.

Par défaut : prépare les patches locaux seulement. --apply valide puis applique.
Ne supprime aucune identité Entra et ne désactive pas Workload Identity sur AKS.
"""
import argparse
import json
import os
import pathlib
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
root = pathlib.Path(__file__).resolve().parent.parent
backup = pathlib.Path(os.environ.get('XDG_STATE_HOME', pathlib.Path.home() / '.local/state')) / 'taoufik-gitops/sso-backup'
if not backup.is_dir():
    backup = pathlib.Path(os.environ['KUBECONFIG']).parent / 'sso-backup'
out = root / '.local/sso-rollback'
out.mkdir(parents=True, exist_ok=True)
patches = []
for kind, name, keys in [
    ('ConfigMap', 'argocd-cm', ['url', 'oidc.config']),
    ('ConfigMap', 'argocd-rbac-cm', ['policy.default', 'policy.csv', 'scopes']),
    ('ServiceAccount', 'argocd-server', ['azure.workload.identity/client-id', 'azure.workload.identity/tenant-id']),
    ('Deployment', 'argocd-server', ['azure.workload.identity/use']),
]:
    before = json.loads((backup / f'{kind}-{name}.json').read_text())
    if kind == 'ConfigMap':
        patch = {'data': {key: before.get('data', {}).get(key) for key in keys}}
    elif kind == 'ServiceAccount':
        annotations = before['metadata'].get('annotations', {})
        patch = {'metadata': {'annotations': {key: annotations.get(key) for key in keys}}}
    else:
        labels = before['spec']['template']['metadata'].get('labels', {})
        patch = {'spec': {'template': {'metadata': {'labels': {key: labels.get(key) for key in keys}}}}}
    path = out / f'{kind}-{name}.json'
    path.write_text(json.dumps(patch))
    patches.append((kind, name, path))
if args.apply:
    for kind, name, path in patches:
        subprocess.run(['kubectl', '-n', 'argocd', 'patch', kind, name, '--type=merge',
                        '--patch-file', str(path), '--dry-run=server'], check=True)
    for kind, name, path in patches:
        subprocess.run(['kubectl', '-n', 'argocd', 'patch', kind, name, '--type=merge',
                        '--patch-file', str(path)], check=True)
else:
    print('Patches de retour préparés dans .local/sso-rollback ; aucune modification cluster.')

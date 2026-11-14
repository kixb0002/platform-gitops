# Rôle : Génère les patches SSO à partir des identifiants publics ; ne doit jamais générer de secret client.
"""Prépare l'overlay SSO sans secret, sans écriture Azure/Kubernetes.

Usage: python3 scripts/render-sso.py --tenant-id UUID --client-id UUID
       --admin-group-id UUID --url https://localhost:8080
"""
import argparse
import pathlib
import uuid
import yaml

parser = argparse.ArgumentParser(description=__doc__)
for name in ('tenant-id', 'client-id'):
    parser.add_argument('--' + name, type=lambda s: str(uuid.UUID(s)), required=True)
admins = parser.add_mutually_exclusive_group(required=True)
admins.add_argument('--admin-group-id', type=lambda s: str(uuid.UUID(s)))
admins.add_argument('--admin-user-id', type=lambda s: str(uuid.UUID(s)))
parser.add_argument('--url', default='https://localhost:8080')
args = parser.parse_args()
from urllib.parse import urlparse
url = urlparse(args.url)
if url.scheme != 'https' or not url.hostname or url.query or url.fragment or url.username or url.path not in ('', '/'):
    parser.error('URL HTTPS de base attendue, sans chemin, identifiants ni paramètres')
base_url = args.url.rstrip('/')
root = pathlib.Path(__file__).resolve().parent.parent
out = root / '.local' / 'sso'
out.mkdir(parents=True, exist_ok=True)
oidc = {'name': 'Microsoft Entra ID',
        'issuer': f'https://login.microsoftonline.com/{args.tenant_id}/v2.0',
        'clientID': args.client_id, 'azure': {'useWorkloadIdentity': True},
        'requestedIDTokenClaims': {'groups': {'essential': True}},
        'requestedScopes': ['openid', 'profile', 'email']}
if args.admin_user_id:
    oidc.pop('requestedIDTokenClaims')
admin_id = args.admin_group_id or args.admin_user_id
rbac_scope = 'groups' if args.admin_group_id else 'oid'
patches = [
    {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'argocd-cm', 'namespace': 'argocd'},
     'data': {'url': base_url, 'oidc.config': yaml.safe_dump(oidc, sort_keys=False)}},
    {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'argocd-rbac-cm', 'namespace': 'argocd'},
     'data': {'policy.default': '', 'scopes': f'[{rbac_scope}]',
              'policy.csv': f'g, {admin_id}, role:admin\n'}},
    {'apiVersion': 'v1', 'kind': 'ServiceAccount', 'metadata': {'name': 'argocd-server', 'namespace': 'argocd',
      'annotations': {'azure.workload.identity/client-id': args.client_id,
                      'azure.workload.identity/tenant-id': args.tenant_id}}},
    {'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': 'argocd-server', 'namespace': 'argocd'},
     'spec': {'template': {'metadata': {'labels': {'azure.workload.identity/use': 'true'}}}}},
]
for i, patch in enumerate(patches):
    (out / f'patch-{i}.yaml').write_text(yaml.safe_dump(patch, sort_keys=False))
(out / 'kustomization.yaml').write_text(yaml.safe_dump({
    'apiVersion': 'kustomize.config.k8s.io/v1beta1', 'kind': 'Kustomization',
    'resources': ['../../bootstrap/argocd'],
    'patches': [{'path': f'patch-{i}.yaml'} for i in range(len(patches))],
}, sort_keys=False))
print(f'Overlay préparé dans {out}; aucune application effectuée.')
print('Précondition : Workload Identity activée, application Entra et fédération configurées.')

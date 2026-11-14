# Rôle : Vérification : présence et cohérence du SSO Workload Identity dans le rendu Argo CD.
"""Contrôle la cohérence du SSO dans le rendu GitOps, sans accès au cluster."""
import sys
import uuid
import yaml

objects = {(o['kind'], o['metadata']['name']): o
           for o in yaml.safe_load_all(open(sys.argv[1]))}
config = objects['ConfigMap', 'argocd-cm']['data']
oidc = yaml.safe_load(config['oidc.config'])
assert config['url'] == 'https://localhost:8080'
assert oidc['azure']['useWorkloadIdentity'] is True
assert 'clientSecret' not in oidc
uuid.UUID(oidc['clientID'])
sa = objects['ServiceAccount', 'argocd-server']['metadata']['annotations']
assert sa['azure.workload.identity/client-id'] == oidc['clientID']
tenant = sa['azure.workload.identity/tenant-id']
uuid.UUID(tenant)
assert oidc['issuer'] == f'https://login.microsoftonline.com/{tenant}/v2.0'
deployment = objects['Deployment', 'argocd-server']
assert deployment['spec']['template']['metadata']['labels']['azure.workload.identity/use'] == 'true'
rbac = objects['ConfigMap', 'argocd-rbac-cm']['data']
assert rbac['policy.default'] == '' and rbac['scopes'] == '[oid]'
rules = [line.strip() for line in rbac['policy.csv'].splitlines() if line.strip()]
assert len(rules) == 1
kind, subject, role = [part.strip() for part in rules[0].split(',')]
assert kind == 'g' and role == 'role:admin'
uuid.UUID(subject)
print('SSO GitOps cohérent : issuer/client/ServiceAccount, fédération sans secret et RBAC mono-administrateur.')

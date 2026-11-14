"""Vérifie l'injection AKS et l'échange fédéré Entra sans journaliser de jeton.

Ne réalise pas le login interactif d'un utilisateur et n'appelle aucune API Azure
avec le jeton reçu. L'identité SSO ne doit recevoir aucun rôle Azure.
"""
import json
import pathlib
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import yaml

root = pathlib.Path(__file__).resolve().parent.parent
config_root = root / 'platform-gitops'
if not (config_root / 'bootstrap/argocd-lab').is_dir():
    config_root = root
config = yaml.safe_load((config_root / 'bootstrap/argocd-lab/patch-0.yaml').read_text())
oidc = yaml.safe_load(config['data']['oidc.config'])
client_id = oidc['clientID']
pods = json.loads(subprocess.check_output([
    'kubectl', '-n', 'argocd', 'get', 'pods', '-l',
    'app.kubernetes.io/name=argocd-server', '-o', 'json']))['items']
pod = next(p for p in pods if p['metadata']['labels'].get('azure.workload.identity/use') == 'true'
           and any(c['type'] == 'Ready' and c['status'] == 'True' for c in p['status'].get('conditions', [])))
container = next(c for c in pod['spec']['containers'] if c['name'] == 'argocd-server')
env = {e['name']: e.get('value') for e in container.get('env', [])}
assert env['AZURE_CLIENT_ID'] == client_id
assert oidc['issuer'] == f"https://login.microsoftonline.com/{env['AZURE_TENANT_ID']}/v2.0"
assert env['AZURE_FEDERATED_TOKEN_FILE'] == '/var/run/secrets/azure/tokens/azure-identity-token'
assert any(s.get('serviceAccountToken', {}).get('audience') == 'api://AzureADTokenExchange'
           for volume in pod['spec']['volumes'] for s in volume.get('projected', {}).get('sources', []))
print('verified: pod Ready, identité injectée et audience fédérée correcte', flush=True)
assertion = subprocess.check_output([
    'kubectl', '-n', 'argocd', 'exec', pod['metadata']['name'], '-c', 'argocd-server',
    '--', 'cat', env['AZURE_FEDERATED_TOKEN_FILE']]).decode().strip()
data = urllib.parse.urlencode({
    'client_id': client_id, 'scope': 'https://management.azure.com/.default',
    'grant_type': 'client_credentials',
    'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
    'client_assertion': assertion,
}).encode()
request = urllib.request.Request(
    f"https://login.microsoftonline.com/{env['AZURE_TENANT_ID']}/oauth2/v2.0/token", data=data)
try:
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
except urllib.error.HTTPError as error:
    result = json.load(error)
    # Ni description libre ni assertion/token dans les journaux.
    raise SystemExit(f"failed: échange Entra HTTP {error.code}, code={result.get('error')}, codes={result.get('error_codes')}")
assert result.get('access_token') and result.get('token_type', '').lower() == 'bearer'
print('verified: échange fédéré Entra HTTP 200, aucun secret client, jeton non affiché et non sauvegardé')

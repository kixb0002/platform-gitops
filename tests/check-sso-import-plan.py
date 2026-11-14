"""Refuse toute mutation cloud pendant l'adoption Terraform du SSO existant."""
import argparse
import json
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--expected-imports', type=int, choices=(0, 4), required=True)
args = parser.parse_args()
plan = json.load(sys.stdin)
expected = {
    'module.argocd_sso.azuread_application_registration.this',
    'module.argocd_sso.azuread_application_redirect_uris.web',
    'module.argocd_sso.azuread_service_principal.this',
    'module.argocd_sso.azuread_application_federated_identity_credential.aks',
}
changes = [r for r in plan.get('resource_changes', []) if r['mode'] == 'managed']
assert expected.issubset({r['address'] for r in changes}), 'Une ressource SSO attendue est absente du plan'
assert all(r['change']['actions'] == ['no-op'] for r in changes), 'Le plan contient une création, modification ou suppression distante'
imports = {r['address'] for r in changes if r['change'].get('importing')}
assert imports == (expected if args.expected_imports else set()), 'Imports inattendus ou manquants'
assert plan.get('applyable', True) or args.expected_imports == 0, 'Plan non applicable'
print(f'Plan contrôlé : {len(imports)} imports ; aucune création, modification ou suppression distante.')

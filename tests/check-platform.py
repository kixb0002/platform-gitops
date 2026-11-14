"""Contrôles des frontières de sécurité avant toute application."""
import sys
import yaml

objects = list(yaml.safe_load_all(open(sys.argv[1])))
projects = {o['metadata']['name']: o for o in objects if o['kind'] == 'AppProject'}
assert projects['default']['spec']['destinations'] == []
assert projects['default']['spec']['sourceRepos'] == []
for env in ('dev', 'staging', 'prod'):
    name = f'ecommerce-{env}'
    spec = projects[name]['spec']
    assert spec['sourceRepos'] == ['https://github.com/kixb0002/platform-gitops.git']
    assert spec['destinations'] == [{'server': 'https://kubernetes.default.svc', 'namespace': name}]
    assert spec['clusterResourceWhitelist'] == []
    allowed = {(r['group'], r['kind']) for r in spec['namespaceResourceWhitelist']}
    for forbidden in ('Secret', 'Role', 'RoleBinding', 'NetworkPolicy', 'ResourceQuota', 'LimitRange'):
        assert all(kind != forbidden for _, kind in allowed)
    assert all(not r.get('groups') and not r.get('jwtTokens') for r in spec['roles'])
    ns = next(o for o in objects if o['kind'] == 'Namespace' and o['metadata']['name'] == name)
    assert ns['metadata']['labels']['pod-security.kubernetes.io/enforce'] == 'restricted'
    quota = next(o for o in objects if o['kind'] == 'ResourceQuota' and o['metadata']['namespace'] == name)
    assert quota['spec']['hard']['services.loadbalancers'] == '0'
    assert quota['spec']['hard']['services.nodeports'] == '0'
    assert quota['spec']['hard']['persistentvolumeclaims'] == '0'
    policies = [o for o in objects if o['kind'] == 'NetworkPolicy' and o['metadata']['namespace'] == name]
    assert {p['metadata']['name'] for p in policies} == {'default-deny', 'allow-same-namespace', 'allow-cluster-dns'}
print(f'{len(objects)} objets : frontières projets, admission, quotas et réseau vérifiées localement.')

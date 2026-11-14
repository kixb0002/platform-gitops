"""Contraintes de sécurité et d'intégrité des manifests applicatifs rendus."""
import re
import sys
import yaml

objects = list(yaml.safe_load_all(open(sys.argv[1])))
for o in objects:
    assert o['metadata']['namespace'] in ('ecommerce-dev', 'ecommerce-staging', 'ecommerce-prod')
    if o['kind'] == 'Service':
        assert o['spec'].get('type', 'ClusterIP') == 'ClusterIP'
        assert not o['spec'].get('externalIPs')
    if o['kind'] == 'Deployment':
        pod = o['spec']['template']['spec']
        assert pod['automountServiceAccountToken'] is False
        assert pod['securityContext']['runAsNonRoot'] is True
        for c in pod['containers']:
            assert re.fullmatch(r'tmgitops237d8c7f.azurecr.io/ecommerce-api@sha256:[a-f0-9]{64}', c['image'])
            assert c['securityContext']['allowPrivilegeEscalation'] is False
            assert c['securityContext']['readOnlyRootFilesystem'] is True
            assert c['securityContext']['capabilities']['drop'] == ['ALL']
            assert c['resources']['requests'] and c['resources']['limits']
            assert c['readinessProbe'] and c['livenessProbe']
print('Image immutable, ressources, probes, isolation et service interne vérifiés.')

# Rôle : Vérification : tests réels d’admission/réseau ; lire le périmètre et nettoyer les objets temporaires.
"""Tests réels : admission PSA/quotas, DNS et refus du trafic latéral Cilium.

Utilise trois pods temporaires et nettoie uniquement les noms créés par ce test.
"""
import json
import subprocess
import uuid

suffix = uuid.uuid4().hex[:8]
created = []


def kubectl(*args, obj=None, check=True):
    return subprocess.run(['kubectl', '--request-timeout=30s', *args],
                          input=json.dumps(obj) if obj else None,
                          text=True, capture_output=True, check=check)


def pod(name, namespace, command):
    return {'apiVersion': 'v1', 'kind': 'Pod',
            'metadata': {'name': name, 'namespace': namespace},
            'spec': {'automountServiceAccountToken': False, 'restartPolicy': 'Never',
                     'securityContext': {'runAsNonRoot': True, 'runAsUser': 10001,
                                         'runAsGroup': 10001, 'fsGroup': 10001,
                                         'seccompProfile': {'type': 'RuntimeDefault'}},
                     'containers': [{'name': 'probe', 'image': 'busybox:1.37.0',
                                     'command': ['sh', '-c', command],
                                     'securityContext': {'allowPrivilegeEscalation': False,
                                                         'readOnlyRootFilesystem': True,
                                                         'capabilities': {'drop': ['ALL']}},
                                     'resources': {'requests': {'cpu': '10m', 'memory': '16Mi'},
                                                   'limits': {'cpu': '100m', 'memory': '64Mi'}},
                                     'volumeMounts': [{'name': 'tmp', 'mountPath': '/tmp'}]}],
                     'volumes': [{'name': 'tmp', 'emptyDir': {}}]}}


try:
    # Les rejets doivent provenir du contrôle testé, pas d'une erreur de YAML.
    bad = pod('psa-negative-' + suffix, 'ecommerce-dev', 'sleep 10')
    bad['spec']['containers'][0]['securityContext']['privileged'] = True
    bad['spec']['containers'][0]['securityContext']['allowPrivilegeEscalation'] = True
    result = kubectl('create', '--dry-run=server', '-f', '-', obj=bad, check=False)
    assert result.returncode and 'violates PodSecurity' in result.stderr, result.stderr
    print('verified: pod privilégié refusé par PSA', flush=True)
    service = {'apiVersion': 'v1', 'kind': 'Service',
               'metadata': {'name': 'lb-negative-' + suffix, 'namespace': 'ecommerce-dev'},
               'spec': {'type': 'LoadBalancer', 'ports': [{'port': 80}]}}
    result = kubectl('create', '--dry-run=server', '-f', '-', obj=service, check=False)
    assert result.returncode and 'exceeded quota' in result.stderr, result.stderr
    print('verified: LoadBalancer refusé par quota sans création Azure', flush=True)

    server = 'isolation-server-' + suffix
    clients = [('ecommerce-dev', 'isolation-local-' + suffix),
               ('ecommerce-staging', 'isolation-remote-' + suffix)]
    for namespace, name, command in [
        ('ecommerce-dev', server, 'mkdir -p /tmp/www; echo isolation-ok > /tmp/www/index.html; exec httpd -f -p 8080 -h /tmp/www'),
        *[(ns, name, 'sleep 300') for ns, name in clients],
    ]:
        kubectl('create', '-f', '-', obj=pod(name, namespace, command))
        created.append((namespace, name))
    for namespace, name in created:
        kubectl('-n', namespace, 'wait', '--for=condition=Ready', 'pod/' + name, '--timeout=120s')
    server_ip = kubectl('-n', 'ecommerce-dev', 'get', 'pod', server, '-o', 'jsonpath={.status.podIP}').stdout
    local = clients[0][1]
    kubectl('-n', 'ecommerce-dev', 'exec', local, '--', 'nslookup', 'kubernetes.default.svc.cluster.local')
    print('verified: DNS Kubernetes accessible', flush=True)
    # Le durcissement n’autorise plus tout le trafic local : ce serveur de test
    # n’est pas ecommerce-api et aucun egress client ne lui est accordé.
    result = kubectl('-n', 'ecommerce-dev', 'exec', local, '--', 'wget', '-T', '3',
                     '-qO-', f'http://{server_ip}:8080', check=False)
    assert result.returncode and 'timed out' in result.stderr.lower(), result.stderr
    print('verified: trafic latéral non déclaré dans Dev bloqué', flush=True)
    result = kubectl('-n', 'ecommerce-staging', 'exec', clients[1][1], '--',
                     'wget', '-T', '3', '-qO-', f'http://{server_ip}:8080', check=False)
    assert result.returncode and 'timed out' in result.stderr.lower(), result.stderr
    print('verified: trafic Staging vers Dev bloqué par NetworkPolicy', flush=True)
finally:
    for namespace, name in created:
        result = kubectl('-n', namespace, 'delete', 'pod', name, '--ignore-not-found', '--wait=false', check=False)
        if result.returncode:
            print('failed: nettoyage', namespace, name, result.stderr)

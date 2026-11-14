# État du LAB et preuves

Dernière opération : commentaires pédagogiques, guide de reprise et retrait du
test HTTPS public du 14 novembre 2026. Voir [le guide de reprise](reprendre-le-lab.md)
et [le schéma](parcours-lab.svg). Les namespaces nommés dev/staging/prod appartiennent
tous au même LAB et ne constituent pas trois clusters de production.

| Partie | État / limite |
|---|---|
| API | Catalogue et devis stateless, sans paiement, base de données ou données personnelles |
| Déploiement Dev | Argo CD depuis platform-gitops/main, digest immuable, Service ClusterIP |
| Image | Base Python Alpine figée, pip absent du runtime, utilisateur non root, filesystem read-only |
| CI applicative | Tests, audit, build, test du runtime, Trivy bloquant avant push ACR |
| Promotion | PR de digest Dev manuelle ; GitHub App de promotion automatique encore à configurer |
| ACR | Basic sans compte admin ; kubelet AcrPull et CI AcrPush au seul registre |
| SSO Argo CD | Entra mono-tenant, Workload Identity sans secret client ; admin par Object ID utilisateur |
| Admission | PSA restricted et quotas interdisant LoadBalancer/NodePort/PVC dans les namespaces applicatifs |
| Réseau | Default deny, DNS explicite, API TCP 8080 ; plus d’autorisation générale latérale |
| Accès Argo CD | ClusterIP, tunnel local et ingress limité au namespace argocd |
| Test HTTPS | Routes, Gateway, TLS, cert-manager, IP dédiée et rôle retirés ; add-ons désactivés |
| Terraform | AKS lu comme data source ; état Linux local sensible, jamais dans Git |
| Key Vault | Module désactivé ; aucun coffre ni chemin privé prétendu opérationnel |
| Production | Monitoring/alerting, sauvegarde/restauration, accès AKS Entra et API privée restent à traiter |

Le pool est revenu à un nœud Ready ; AKS est Succeeded et Dev Synced/Healthy,
vérifiés après retrait. La résolution publique de api est encore à retirer chez
Namecheap par l’utilisateur ; l’ancienne IP est déjà libérée.
Les ressources réseau techniques du cluster et son Load Balancer sortant partagé
ne sont pas supprimés. AKS et ACR conservent leurs frais habituels.

## Contrôles reproductibles

Depuis platform-gitops (ou la racine initiale gitops/) :

```bash
source scripts/kubeconfig.sh
bash scripts/preflight.sh
bash scripts/platform.sh render
bash scripts/argocd.sh render
python3 tests/integration-security.py
```

Le test d’intégration crée trois pods temporaires à noms uniques et les nettoie.
Il vérifie les rejets PSA et quota en dry-run, le DNS, le refus du trafic latéral
dans Dev et le refus Staging->Dev. Ces sondes ne représentent pas un test de
charge ou une validation d’isolation entre tenants hostiles.

L’accès HTTP fonctionnel se vérifie avec le tunnel du guide de reprise. Les
NetworkPolicies d’ingress ne donnent pas implicitement de droits egress aux
clients : toute nouvelle dépendance réseau doit être autorisée explicitement.
Les contrôles locaux sont distincts de l’observation du déploiement réel.

## Sources et commentaires

Les fichiers écrits pour le LAB expliquent leur rôle, les décisions de sécurité
et les frontières Terraform/GitOps/bootstrap. Les fichiers upstream vendor et
leurs SHA restent intacts. Les commentaires seuls n’exigent pas une nouvelle
image déployée : le code applicatif et les dépendances sont inchangés.
Les commentaires ont été contrôlés par parsing, rendus, tests API et validations
Terraform ; les dernières preuves de retrait sont dans docs/network-access-hardening.md.

## Limites et droits

Le groupe autorisé est RG-Taoufik-Mellah. L’utilisateur n’a pas de droits réseau
sur le groupe MC_* ; le rôle de l’expérience était limité à son IP propre et
est supprimé avec elle. Les scripts Entra historiques ne recréent pas d’identités.
AKS conserve son endpoint public d’administration et ses comptes locaux ; le
SSO Argo CD ne remplace pas une intégration Entra de l’accès Kubernetes.
Le compte admin local Argo CD reste présent. Les groupes Entra n’ont pas été
créés, faute de droits vérifiés. Les AppProjects n’empêchent pas un administrateur
Kubernetes direct de contourner leurs restrictions ; le contrôleur Argo CD garde
les droits cluster du bootstrap officiel.

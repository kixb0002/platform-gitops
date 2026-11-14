# Adoption du SSO existant dans Terraform et GitOps

Le 14 novembre 2026, reprise de la configuration SSO déjà fonctionnelle.
Objectif : conserver les mêmes identités et les mêmes réglages de connexion.

## Propriétaires des ressources

| Périmètre | Déclaration autoritative |
|---|---|
| Application Entra, redirect URI Web, service principal et fédération | Module Terraform `platform-infra/modules/argocd-sso` |
| Tenant, providers, paramètres LAB et rattachement des objets existants | `platform-infra/environments/lab/main.tf`, `sso.tf`, `sso-imports.tf` |
| ConfigMaps SSO/RBAC, annotations du ServiceAccount, label Workload Identity | Overlay `platform-gitops/bootstrap/argocd-lab` |
| Cluster AKS existant et activation Workload Identity | Prérequis existant lu par Terraform ; aucune prise en charge complète du cluster à cette étape |

Terraform ne gère aucun objet Kubernetes Argo CD. Les manifestes GitOps ne
créent aucune application Entra. Les rôles, IDs et URL déclarés ne sont pas
des mots de passe ; aucun secret client ni jeton n'est introduit dans Git.

## Import effectué

Le plan contrôlé a importé quatre adresses Terraform pour les trois objets
Entra existants ; les redirect URIs sont gérées comme sous-ressource distincte.
Résultat de l'apply : **4 imports, 0 création, 0 modification, 0 suppression**.
Le propriétaire existant du service principal est conservé explicitement.
Tous les objets Entra sont protégés par `prevent_destroy`.

Les blocs `import` sont conservés comme trace de l'adoption. Une fois les
ressources dans le state, ils ne les réimportent pas et ne les recréent pas.
Le champ historique de version des access tokens d'API, initialement null,
est conservé sans mutation ; la raison et la limite du provider sont documentées
dans le module. L'issuer SSO reste v2.0.

Le state est privé :
`/home/user/.local/state/taoufik-gitops/lab/terraform.tfstate`.
La copie préalable est `terraform.pre-sso-import.tfstate` dans ce même répertoire.
Ne pas restaurer cette ancienne copie après l'import pour tenter un rollback :
cela ferait perdre le suivi des objets existants, sans changer le cloud.
En cas d'erreur future, corriger les déclarations et revoir un plan ; ne pas
supprimer les objets pour simplifier leur réimport et ne pas utiliser destroy.

```bash
bash scripts/terraform-lab.sh init
bash scripts/terraform-lab.sh validate
bash scripts/terraform-lab.sh plan
```

La configuration Entra doit rester cohérente avec les client/tenant IDs et le
callback des manifestes GitOps. Le backend est encore local : un backend
partagé et sécurisé est nécessaire avant collaboration/automatisation Terraform.

## Configuration Kubernetes

Les patches copiés depuis la configuration active résident maintenant dans
`platform-gitops/bootstrap/argocd-lab/patch-0.yaml` à `patch-3.yaml`.
Ils ont été comparés aux champs actifs du cluster sans aucune réapplication.
Le rendu standard utilise désormais cet overlay, et non uniquement la base
upstream dépourvue du SSO.

```bash
bash scripts/argocd.sh render
python3 tests/check-sso.py .local/argocd.yaml
source scripts/kubeconfig.sh
python3 tests/verify-sso-federation.py
```

`scripts/provision-sso-lab.sh` est retiré : son exécution s'arrête sans action
et indique Terraform. Le générateur local reste un outil de préparation, pas
la source du LAB. `scripts/apply-sso-lab.py` lit maintenant les patches GitOps
versionnables. Il n'est pas nécessaire de le relancer pour cette adoption.

Les deux dépôts locaux sont préparés dans `.local/repos/platform-infra` et
`.local/repos/platform-gitops`. Leur publication GitHub et une éventuelle
réconciliation de la configuration Argo CD par Argo CD lui-même restent
distinctes. Aucune publication ni nouvelle application de self-management
n'est déclenchée par cette migration. L'admin local est conservé.

# Avancement de l'implémentation

Constats des 13 et 14 novembre 2026. Tous les environnements ci-dessous sont des espaces
LAB sur le cluster unique existant, y compris le namespace nommé `ecommerce-prod`.
Ils ne constituent pas trois clusters ni une isolation entre tenants hostiles.

| Élément | État | Preuve / limite |
|---|---|---|
| Argo CD 3.6.1 | verified | Sept pods Ready ; API et login initial vérifiés |
| Projets Dev/Staging/Prod | verified | Seul kixb0002/platform-gitops autorisé, destination exacte, aucun droit cluster |
| Projet default | verified | Sources et destinations vides ; aucune application dépendante |
| RBAC projets | verified | Rôles reader/deployer définis ; aucune attribution inventée |
| PSA restricted | verified | Pod privilégié refusé par admission serveur |
| Quotas de coût | verified | LoadBalancer refusé en dry-run ; NodePort et PVC interdits |
| Isolation Cilium | verified | DNS et trafic local passent ; Staging vers Dev expire |
| Ressources de test | verified | Trois pods supprimés ; namespaces Dev/Staging vides confirmés |
| SSO Entra | verified | Identités existantes importées dans Terraform ; fédération fonctionnelle après adoption |
| SSO déclaratif Kubernetes | verified | Overlay bootstrap/argocd-lab identique au cluster ; publication GitHub encore en attente |
| Login SSO navigateur | verified | Fonctionnement confirmé par l’utilisateur ; consentement et jeton non inspectés indépendamment |
| Modules ACR / Key Vault | verified | Terraform init et validate réussis, provider signé et figé |
| Création ACR / AcrPull | verified | Apply autorisé : 2 ajouts ; ACR Basic tmgitops237d8c7f sans admin |
| Key Vault | not run | Désactivé par défaut, chemin privé et permissions réseau à valider |
| CI de validation | verified | Workflows GitHub platform-infra et platform-gitops exécutés avec succès |
| Git et publication GitHub | verified | platform-infra et platform-gitops publiés sur main ; workflows de validation réussis |
| E-commerce | verified | API catalogue/devis, 4 tests, audit Python, image ACR et test AKS réussis |
| Application GitOps Dev | verified | ecommerce-dev Synced/Healthy, un pod Ready, Service ClusterIP ; santé/catalogue/devis testés |
| Workload Identity | verified | AKS activé, pod injecté, échange fédéré Entra HTTP 200 |
| Métriques / alertes | not run | Aucun Prometheus/Grafana/alerting prétendu opérationnel |
| HA / restauration | not run | Nœud unique ; aucune validation de résilience/backup |

## Exploitation des garde-fous

```bash
bash scripts/platform.sh render
bash scripts/platform.sh preview
bash scripts/platform.sh verify
source scripts/kubeconfig.sh
python3 tests/integration-security.py
```

Les trois namespaces disposent chacun d'un quota de requests de 500m CPU / 1Gi
et huit pods. Ces quotas plafonnent l'usage, sans réserver de capacité : la somme
des quotas peut dépasser ce qui reste sur le nœud LAB. Les PVC sont interdits
pour éviter les disques payants tant que stockage et sauvegarde ne sont pas cadrés.
Les politiques autorisent le trafic dans un même namespace et le DNS CoreDNS.
Tout autre flux, dont Internet, Key Vault ou une base externe, exige une règle
explicite lors de l'intégration de l'application. Les NetworkPolicies ne sont
pas modifiables par les projets applicatifs. Les namespaces système existants
et l'application du namespace `formation` ne sont pas modifiés.

Les AppProjects limitent les types de ressources, mais ne contrôlent pas tous
leurs champs : les futurs Services doivent rester ClusterIP et sans externalIPs.
Les droits Kubernetes directs d'un administrateur restent capables de contourner
les restrictions Argo CD. L'identité contrôleur Argo CD conserve les droits
cluster du bootstrap upstream ; sa réduction devra être validée séparément.

## Dépôts et promotion

Le dépôt autorisé est `https://github.com/kixb0002/platform-gitops.git`, public
initialement vide. `platform-infra` était également vide. Les deux dépôts sont
maintenant publiés sur main. Le dépôt
`ecommerce-app` reste à créer. Trois contenus autonomes sont prêts dans
`.local/repos/`. Pour un futur dépôt privé, obtenir l'accès via une
GitHub App ou un accès SSH en lecture seule, sans clé/token en Git. Ajouter
uniquement l'URL GitOps approuvée à `sourceRepos` de chaque projet. Les rôles
ne sont attribués qu'aux groupes Entra vérifiés, après SSO.

Le propriétaire applicatif pousse une PR. La CI teste et scanne le code puis
construit une image, s'authentifie à Azure via OIDC et pousse dans ACR. Elle
ouvre une PR dans le dépôt GitOps avec le digest immuable de l'image. Le rôle
Azure du build sera limité au registre ; la CI ne recevra aucun kubeconfig.
Une identité/permission GitHub distincte est nécessaire pour les PR inter-dépôts :
le GITHUB_TOKEN du dépôt applicatif n'accorde pas ce droit automatiquement.

Le responsable plateforme valide Dev puis Staging. Le responsable de mise en
production approuve la PR de promotion et une synchronisation manuelle de Prod.
Les protections de branche et les approbations GitHub restent à configurer et
tester ; elles ne sont pas garanties par une convention de répertoires. Aucun
auto-sync de production n'est activé. En cas d'échec, corriger/revenir sur la PR,
resynchroniser la révision attendue et confirmer image, santé et métriques.
Un rollback de code ne restaure pas automatiquement une base de données.

## Informations nécessaires pour poursuivre

- Dépôt ecommerce-app et identité CI de build/promotion inter-dépôts à finaliser.
- Validation du login SSO dans le navigateur avant retrait de l’admin local.
- Identité CI dédiée et GitHub App de promotion inter-dépôts à configurer.
- Décision réseau privée et capacité avant de prétendre à une cible production.

## CI livrée et plan Azure

`.github/workflows/validate.yaml` valide les rendus GitOps, les frontières de
sécurité, la syntaxe Bash et Terraform à chaque PR / push main. Les actions
sont figées par SHA vérifié ; aucune permission d'écriture ni session Azure
n'est accordée. Ce workflow correspond à la structure actuelle du workspace.
Lors de la séparation en trois dépôts, adapter les chemins et copier les scripts
nécessaires dans chaque dépôt. Ce workflow valide la plateforme ; le build et le scan de l'image sont
définis dans le workflow applicatif séparé. Aucun des workflows ne remplace
les protections de branche.

Le plan Terraform autorisé a été appliqué : **2 créations, 0 modification,
0 suppression**, ACR Basic `tmgitops237d8c7f` et rôle `AcrPull` du kubelet.
Key Vault est désactivé. Le plan suivant confirme `No changes`. Le state est
conservé dans `/home/user/.local/state/taoufik-gitops/lab/terraform.tfstate`.
Le tirage de l'image par digest sur AKS fonctionne sans imagePullSecret et son
API répond HTTP 200 ; le pod temporaire est supprimé. L'audit pip-audit ne
détecte aucune vulnérabilité Python connue à cette date ; le scan OS Trivy
est configuré en CI mais n'a pas encore été exécuté.

## SSO : configuré le 14 novembre 2026

Après accord explicite, application `argocd-taoufik`, service principal et
fédération créés ; Workload Identity activée sur l'AKS existant. Les quatre
patches ciblés sont appliqués, le serveur est Ready. L'échange fédéré Entra
réussit, la redirection Microsoft pointe vers le callback localhost:8080 et
les contrôles RBAC positifs/négatifs passent. Aucun secret client n'est créé.
Le compte administrateur local est conservé. Le login humain et le consentement
restent à confirmer dans le navigateur ; voir `docs/sso-entra.md`.

## Adoption IaC du SSO

Les quatre adresses Entra sont importées dans le state Terraform privé.
L'apply ne crée, ne modifie ni ne supprime aucun objet distant. Le propriétaire
existant du service principal est conservé explicitement. Le rendu GitOps du
LAB inclut les quatre patches SSO actifs et la CI vérifie leur cohérence.
Le script impératif de création Entra est désactivé. Voir `docs/sso-iac-migration.md`.

## Publication et premier déploiement GitOps

Les commits initiaux a01b514 (infra) et 2ce59c7 (GitOps) sont publiés sur main.
Les deux workflows de validation ont réussi :
- https://github.com/kixb0002/platform-infra/actions/runs/43617732321
- https://github.com/kixb0002/platform-gitops/actions/runs/43617738614

Après validation serveur, seule applications/dev.yaml a été créée dans Argo CD.
Argo CD a lu apps/ecommerce/overlays/dev et déployé le ServiceAccount, le
Deployment et le Service. État observé : Synced/Healthy, un pod Ready,
ClusterIP sans IP externe. Via le Service : santé HTTP 200, trois produits,
devis 12300 centimes EUR et quantité négative rejetée HTTP 400.

Accès local : source scripts/kubeconfig.sh puis
`kubectl -n ecommerce-dev port-forward --address 127.0.0.1 svc/ecommerce-api 8081:80`.
Catalogue : http://localhost:8081/api/products. Staging et Prod ne sont pas activés.
Le build initial reste manuel ; le pipeline applicatif OIDC/scan/promotion
inter-dépôts n'est pas encore opérationnel. Le SSO du serveur reste configuré
comme précédemment et n'est pas auto-géré par cette Application applicative.

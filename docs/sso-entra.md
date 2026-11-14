# SSO Entra Argo CD — LAB actif

Configuration effectuée le 14 novembre 2026 après accord explicite.

- `verified` : application mono-tenant `argocd-taoufik` et service principal créés.
- `verified` : fédération `aks-argocd-server`, subject
  `system:serviceaccount:argocd:argocd-server`, audience `api://AzureADTokenExchange`.
- `verified` : aucun secret client ni certificat client dans l'application Entra.
- `verified` : Workload Identity activée sur AKS ; opération Azure Succeeded.
- `verified` : identité injectée sur le pod Argo CD Ready ; échange fédéré Entra HTTP 200.
- `verified` : endpoint Argo CD publie la configuration ; redirection Microsoft
  avec client ID et callback exacts validée.
- `verified` : politique RBAC autorise l'administrateur attendu et refuse un sujet inconnu.
- `verified` (confirmation utilisateur) : connexion SSO dans le navigateur fonctionnelle.
- `not run` : inspection indépendante du consentement et du claim oid de cette session navigateur.

## Accès et contrôle navigateur

Ouvrir https://localhost:8080 et choisir la connexion **Microsoft Entra ID**.
Utiliser le compte Azure qui a servi à configurer ce LAB. Le callback enregistré
est exactement `https://localhost:8080/auth/callback` : conserver le port 8080.
Le certificat HTTPS initial reste auto-signé. Si le tunnel est arrêté :

```bash
cd /mnt/c/Users/taoufik.mellah/gitops
source scripts/kubeconfig.sh
kubectl -n argocd port-forward --address 127.0.0.1 svc/argocd-server 8080:443
```

Après login, vérifier dans User Info que la session provient d'Entra et que
l'utilisateur accède aux projets autorisés. Un consentement utilisateur ou
administrateur peut être requis par la politique du tenant ; cette étape n'a
pas été simulée. Ne pas partager de code OAuth, de mot de passe ou de jeton.

Le RBAC de ce LAB s'appuie sur le claim `oid` du seul utilisateur Azure courant
et sur un issuer mono-tenant. Le rôle par défaut est vide. Aucun rôle Azure n'a
été accordé à l'identité SSO. Les rôles projets reader/deployer restent séparés
et non attribués. Le tenant interdit la création self-service des groupes de
sécurité ; une future administration collective devra utiliser des groupes
vérifiés et approuvés, avec scopes RBAC adaptés.

## Reproductibilité et limites

Les objets Entra existants sont maintenant adoptés par Terraform dans
`platform-infra/modules/argocd-sso` et les blocs d'import du LAB. Les quatre
patches Kubernetes actifs sont déclarés dans
`platform-gitops/bootstrap/argocd-lab`, qui constitue la source du rendu LAB.
`scripts/provision-sso-lab.sh` est retiré et s'arrête sans modifier d'identité.
`scripts/apply-sso-lab.py` lit les fichiers GitOps et ne gère aucun objet Entra.
Les fichiers sont publiés sur GitHub dans platform-gitops. La configuration
SSO du serveur Argo CD n’est pas encore réconciliée par une Application dédiée.
Voir `docs/sso-iac-migration.md` pour l'import et les limites de périmètre.

```bash
source scripts/kubeconfig.sh
python3 tests/verify-sso-federation.py
```

Ce test lit l'assertion projetée en mémoire et vérifie un échange Entra ; il
n'affiche ni ne sauvegarde les jetons reçus. Il ne constitue pas un login humain
et n'utilise pas le jeton reçu pour appeler une API Azure.

## Retour arrière

L'admin local est conservé jusqu'à validation du parcours navigateur et d'un
accès de secours durable. Aucune suppression du secret initial n'est faite.
Les quatre objets avant modification sont sauvegardés sur stockage Linux privé
sous `/home/user/.local/state/taoufik-gitops/sso-backup/`, avec permissions
privées, et une copie temporaire sous `/tmp/gitops-aks-1000/sso-backup/`.

```bash
source scripts/kubeconfig.sh
python3 scripts/rollback-sso-lab.py
# Examiner .local/sso-rollback avant application si un retour est nécessaire.
python3 scripts/rollback-sso-lab.py --apply
kubectl -n argocd rollout status deployment/argocd-server --timeout=180s
```

Le retour restaure uniquement les champs SSO modifiés à partir de la sauvegarde,
après validation serveur. Il n'a pas été exécuté. Il ne supprime pas les identités
Entra et ne désactive pas Workload Identity sur le cluster.

Références :
- https://argo-cd.readthedocs.io/en/release-3.6/operator-manual/user-management/microsoft/
- https://argo-cd.readthedocs.io/en/release-3.6/operator-manual/rbac/
- https://learn.microsoft.com/en-us/entra/identity-platform/id-token-claims-reference

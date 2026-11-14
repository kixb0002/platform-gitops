# Overlay Argo CD du LAB

Configuration SSO active et reproductible du cluster `aks-taoufik-lab`.
Les quatre patches déclarent les ConfigMaps SSO/RBAC, les annotations du
ServiceAccount et le label Workload Identity du pod serveur.

```bash
kubectl kustomize platform-gitops/bootstrap/argocd-lab
```

Depuis la racine du dépôt GitOps autonome, utiliser
`kubectl kustomize bootstrap/argocd-lab`.

Les identifiants tenant/client/utilisateur sont des paramètres d'identité,
pas des mots de passe ; aucun secret client, jeton ou kubeconfig n'est inclus.
Le LAB utilise `oid` pour l'administrateur personnel. Avant un usage collectif,
remplacer ce mapping par des groupes approuvés et revoir les droits.

Terraform est propriétaire des objets Entra ; cet overlay est propriétaire de
la configuration Kubernetes SSO. Il ne crée aucune application Entra. L'admin
local reste activé comme secours. La publication GitHub et une éventuelle
réconciliation de cet overlay par Argo CD sont des étapes distinctes : aucun
auto-management du serveur Argo CD n'est activé implicitement.

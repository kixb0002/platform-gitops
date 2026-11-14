# Platform GitOps AKS LAB

Argo CD 3.6.1, trois AppProjects et trois espaces LAB sur aks-taoufik-lab.
Le répertoire bootstrap contient les manifestes officiels figés et leurs patches.
Le répertoire platform contient les garde-fous ; apps/ecommerce contient les
overlays Dev/Staging/Prod par digest. Les Applications sont dans applications/.

Dépôt publié : https://github.com/kixb0002/platform-gitops.git, branche main.
Sur le LAB existant, ecommerce-dev est maintenant déployé par Argo CD et vérifié
Synced/Healthy. Pour un nouveau bootstrap, appliquer seulement applications/dev.yaml.
Dev auto-sync sans prune, Staging et Prod manuels.
Ne pas appliquer les trois Applications simultanément par défaut.

Validation locale : bash scripts/argocd.sh render ; bash scripts/platform.sh render.
Accès cluster : source scripts/kubeconfig.sh, puis bash scripts/preflight.sh.
Voir docs/ pour les validations réelles et les limites restantes.
La configuration SSO active est déclarée dans bootstrap/argocd-lab. Les identités Entra
appartiennent au dépôt platform-infra (Terraform), pas aux scripts GitOps.
La publication est effectuée et l’application Dev est réconciliée depuis Git.
Le SSO du serveur Argo CD est déclaré mais son auto-management reste à finaliser.

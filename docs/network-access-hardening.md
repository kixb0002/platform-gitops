# Accès et réseau — état du 14 novembre 2026

## Changements appliqués et vérifiés

- Les politiques allow-same-namespace des trois environnements ne permettent
  plus une communication générale ingress/egress. Elles sélectionnent seulement
  ecommerce-api et autorisent l’entrée TCP 8080 depuis le même namespace.
- default-deny et allow-cluster-dns restent actifs. Une autorisation ingress
  n’autorise pas l’egress du client : tout futur client isolé doit recevoir sa
  propre règle egress précise. Aucun client interne n’est actuellement déployé.
- La règle argocd-server ne permet l’entrée que depuis les pods du namespace
  argocd, sur TCP 8080 et 8083. L’accès par kubectl port-forward reste fonctionnel.

Vérifié : API localhost 200, résolution DNS, Internet sortant bloqué depuis
l’API, autre namespace vers API bloqué, autre namespace vers Argo CD bloqué.
Avant modification, le même pod de contrôle recevait 200 sur /api/version Argo CD.
Après modification, le tunnel local reçoit toujours la version et les paramètres
SSO ; ecommerce-dev reste Synced/Healthy. La connexion interactive Entra n’a pas
été rejouée pendant cette opération.

## HTTPS en préparation, pas encore activé

Le Terraform public-access.tf (platform-infra) a créé après accord une IP Standard
statique pip-ecommerce-api-lab dans RG-Taoufik-Mellah, avec DNS Azure, et un rôle
Network Contributor pour l’identité du control plane AKS, limité à cette IP.
Aucun droit n’est demandé sur le groupe réseau géré MC_*.
La validation effective du provisionnement LoadBalancer reste à faire.

La passerelle prévue est l’implémentation Gateway API gérée AKS (approuting-istio),
pas ingress-nginx retiré. Il faudra activer l’add-on, configurer le certificat
avec renouvellement automatique, la redirection HTTP vers HTTPS et une règle
réseau ne permettant que la passerelle vers ecommerce-api:8080.
Le domaine choisi est api.lab-tk.click, DNS géré chez Namecheap.
L’IP créée est 51.103.104.29 ; le rôle réseau est limité à cette seule IP.
La passerelle et le certificat ne sont pas encore déployés.
Argo CD ne sera pas publié.

## Limites à traiter séparément

L’API Kubernetes est encore publique sans liste d’IP autorisées ; les comptes
locaux AKS et le compte local admin Argo CD restent actifs. Le SSO Argo CD est
limité à un utilisateur ; il n’est pas une intégration Entra de l’accès AKS.
Avant restriction d’IP : définir les IP d’administration stables et vérifier le
chemin de secours pour éviter de perdre l’accès. Avant désactivation des comptes
locaux : vérifier une session Entra et un accès de secours fonctionnels.
Les droits de création des groupes Entra ne sont pas disponibles actuellement.

## Retour arrière ciblé

Pour restaurer temporairement la règle e-commerce précédente, la politique
allow-same-namespace utilisait podSelector: {}, policyTypes: [Ingress, Egress],
ingress: [{from: [{podSelector: {}}]}], egress: [{to: [{podSelector: {}}]}].
Pour Argo CD, la règle précédente utilisait ingress: [{}]. Restaurer uniquement
la règle nécessaire après diagnostic, puis rétablir la restriction corrigée.

## HTTPS activé après accords

L’add-on Gateway API/App Routing et cert-manager v1.21.3 sont installés.
Le pool system est passé de 1 à 2 Standard_D2s_v5 après accord sur les frais.
https://api.lab-tk.click/api/products fonctionne avec chaîne TLS vérifiée.
Gateway Programmed, certificat Ready, HTTP->HTTPS 301, devis 12300 centimes.
Les restrictions précédentes restent vérifiées. Voir platform/public-api/README.md
pour les preuves, les limites et l’ordre du retrait après test.

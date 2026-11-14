# Expérience HTTPS Dev — retirée, configuration conservée

> Les URL ci-dessous documentent le test historique. Les routes et le certificat
> ont été supprimés ; reprendre normalement par le tunnel interne, voir
> [le guide de reprise](../../docs/reprendre-le-lab.md).

URL historique catalogue : https://api.lab-tk.click/api/products
URL historique devis : POST https://api.lab-tk.click/api/quotes

Le 14 novembre 2026, après accords explicites, le pool system du cluster
aks-taoufik-lab a été porté de 1 à 2 Standard_D2s_v5. Le nœud unique ne pouvait
pas accueillir le deuxième istiod (Insufficient cpu/memory). Les deux nœuds
sont Ready, avec deux pods istiod et deux proxies de passerelle prêts.
Cette capacité supplémentaire et son disque restent facturés tant que conservés.

## Configuration

- Gateway API/App Routing Istio géré AKS ; GatewayClass approuting-istio.
- Gateway ecommerce-public dans platform-ingress, IP 51.103.104.29.
- IP et rôle Network Contributor limités à cette IP : Terraform platform-infra.
- Domaine api.lab-tk.click : enregistrement A ajouté chez Namecheap par l’utilisateur.
- cert-manager v1.21.3 : chart officiel vendored et SHA256SUMS, configuration Helm.
- Issuer Let’s Encrypt local à platform-ingress ; certificat ECDSA avec rotation.
  Clés ACME/TLS dans des Secrets Kubernetes, jamais dans Git.
- HTTP 80 : redirection vers HTTPS, sauf challenges ACME temporaires exacts.
- HTTPS 443 : uniquement le préfixe /api vers le Service ClusterIP ecommerce-api
  de Dev. La racine / n’est pas une boutique web et ne possède pas de route.
- Règle réseau : namespace platform-ingress ET label du Gateway nommé, vers les
  pods app=ecommerce-api sur TCP 8080. Les autres namespaces restent bloqués.
- Le port de santé 15021 n’a pas de règle Load Balancer publique (annotation
  port_15021_no_lb_rule=true). Les futures validations ACME utilisent ClusterIP.
- Argo CD reste ClusterIP, accessible par tunnel local ; aucun Gateway pour lui.
  Staging/Prod ne sont pas publiés.

## Preuves de validation

Gateway Accepted/Programmed/ResolvedRefs=True ; HTTPRoute Accepted/ResolvedRefs=True.
Certificat Ready=True, échéance 2027-02-12T17:06:24Z, renouvellement planifié
2027-01-13T17:06:24Z. Le renouvellement est configuré ; un renouvellement futur
réel n’a pas encore été observé et doit être surveillé.
Catalogue HTTPS avec validation TLS : 3 produits. Devis : 12300 centimes.
HTTP->HTTPS : 301. Accès inter-namespace direct à l’API et Argo CD : bloqué.
API localhost saine et Internet sortant bloqué. Dev Synced/Healthy.

## Gestion et limites

Le script scripts/public-api.sh rend ou applique le bootstrap. Il vérifie deux
nœuds Ready et le SHA du chart, puis évite de réactiver un add-on déjà activé.
L’add-on, le nombre de nœuds, Helm et ces objets plateforme ne sont pas encore
gérés par Terraform/une Application Argo CD ; ils sont versionnés pour reprise.
Ne pas présenter le nombre de nœuds comme géré par Terraform : AKS reste une data
source. Les secrets doivent aussi être pris en compte dans la sauvegarde/reprise.
L’API ne contient que des données de démonstration sans authentification client.
HTTPS ne remplace pas authentification, quotas de requêtes, WAF ou validation de
production. L’API Kubernetes publique et les comptes locaux restent à traiter.

## Retrait après test, uniquement sur demande explicite

1. Retirer les deux HTTPRoute de ce répertoire pour couper les routes publiques.
2. Retirer le Gateway ; attendre la suppression du Service LoadBalancer et le
   détachement de l’IP. Ne pas supprimer le Load Balancer sortant partagé AKS.
3. Retirer le Certificate, l’Issuer, leurs Secrets dédiés et allow-public-gateway.
   Vérifier l’absence d’autres ressources avant de retirer platform-ingress.
4. Vérifier tous les certificats/issuers/gateways du cluster avant de désinstaller
   cert-manager et désactiver App Routing Istio puis Gateway API. Ne pas supprimer
   des CRD partagées par d’autres workloads. Les CRD cert-manager peuvent rester
   après désinstallation Helm ; leur suppression détruirait leurs objets.
5. Après retrait des pods ajoutés, vérifier capacité et budgets de disruption,
   puis revenir à un nœud via AKS. Valider le rollout et la santé Dev.
6. Retirer l’enregistrement api chez Namecheap avant de libérer l’IP pour éviter
   de laisser le domaine pointer vers une adresse potentiellement réattribuée.
7. Dans platform-infra, retirer explicitement prevent_destroy de cette seule IP,
   mettre enable_public_api=false, vérifier un plan ciblant seulement IP et rôle,
   puis appliquer après accord. Retirer uniquement le Gateway ne libère pas l’IP.
8. Vérifier API interne et tunnel Argo CD ; conserver AKS, ACR, Argo CD et Dev.

Le retrait a été demandé après le test. Les routes, le Gateway, le certificat,
les clés, cert-manager, ses CRD, l’IP dédiée et son rôle ont été supprimés.
Le pool est revenu à un nœud Ready ; Gateway API et App Routing sont Disabled.
Leurs classes et CRD inutilisées ont également été nettoyées. AKS et ACR conservent leurs frais
habituels ; la suppression du seul accès public ne les arrête pas.

Le DNS Namecheap est géré par l’utilisateur : supprimer api si l’enregistrement
pointe encore vers l’ancienne IP libérée. Ne pas utiliser l’ancienne IP lors
d’une future expérience ; Azure peut en attribuer une différente.

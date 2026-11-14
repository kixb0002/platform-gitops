# Accès HTTPS Dev — préparé, non déployé

Cible : aks-taoufik-lab, api.lab-tk.click, IP statique 51.103.104.29.
Namespace passerelle : platform-ingress ; GatewayClass gérée : approuting-istio.

Après accord, l’add-on sera activé sur le cluster existant. Il installera son control plane
Istio et gère les proxies de passerelle, sans injection de sidecar dans l’API.
Cette activation n’est pas encore réalisée : la revue automatique demande un
accord explicite distinct pour l’add-on et ses composants persistants.

cert-manager v1.21.3 est préparé comme chart officiel vendored, contrôlé par
SHA256SUMS. Il ajoute des CRD, contrôleurs et droits Kubernetes nécessaires à la
gestion des certificats. Ses clés ACME et TLS restent dans des Secrets Kubernetes,
jamais dans Git. Issuer namespace-scoped, aucun accès au compte Namecheap requis.

Le Gateway reçoit HTTP 80 et HTTPS 443 sur l’IP autorisée ; HTTP redirige vers
HTTPS, sauf la route ACME temporaire exacte pour la validation HTTP-01. Le certificat
Let’s Encrypt utilise ECDSA et rotation de clé. Le renouvellement est automatique,
mais doit être surveillé. Le service ecommerce-api reste ClusterIP. La route ne
publie que /api de Dev, avec hostname api.lab-tk.click. Argo CD reste privé.
La règle réseau n’admet que les pods du Gateway nommé dans platform-ingress vers
les pods app=ecommerce-api sur TCP 8080. Staging et Prod ne sont pas publiés.

Contrôles après accord et installation : Gateway Programmed, HTTPRoute Accepted
et ResolvedRefs, certificat Ready, DNS public, HTTP->HTTPS, chaîne TLS valide,
catalogue et devis via HTTPS, autres namespaces toujours bloqués, Argo CD sain.
Un rendu local réussi n’est pas une validation serveur ni un certificat émis.
Les CRD Gateway/cert-manager ne sont pas encore installées sur la cible.

La passerelle et cert-manager ne sont pas encore gérés par un Application Argo CD ;
le script de bootstrap est explicite. L’activation de l’add-on AKS n’est pas gérée
par le Terraform actuel (AKS est une data source). L’IP et le rôle restent Terraform.

L’API expose uniquement des données de démonstration sans authentification client.
Un accès HTTPS ne remplace pas l’authentification, le rate limiting, un WAF ou une
validation complète de production.

Arrêt d’exposition : retirer les HTTPRoute et le Gateway de ce répertoire, après
vérification du périmètre ; conserver les CRD et cert-manager tant que d’autres
certificats en dépendent. Ne pas détruire le cluster ou le groupe de ressources.

## Installation autorisée, en attente de capacité

L’activation Gateway API/App Routing a été lancée après accord explicite.
GatewayClass approuting-istio est Accepted. Un pod istiod tourne ; le deuxième
est Pending avec FailedScheduling Insufficient cpu / Insufficient memory.
Le pool system actuel contient un seul Standard_D2s_v5. La suite du script a
été arrêtée localement avant cert-manager, Gateway public et émission TLS.
L’opération Azure déjà lancée poursuit son exécution côté Azure.
L’application Dev reste Synced/Healthy et aucune nouvelle VM n’a été créée.
Le passage à deux nœuds demande un accord distinct sur VM et disque facturés.
Le script vérifie désormais deux nœuds Ready avant de poursuivre.

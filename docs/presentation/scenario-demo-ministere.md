# Scénario de démonstration — Présentation État / Ministère

## Objectif

Présenter GuinéeCare Hospital Suite comme une plateforme hospitalière moderne, souveraine, progressive et adaptée au contexte guinéen.

Durée recommandée : 20 à 30 minutes.

## Préparation technique

Depuis la racine du projet :

```bash
git pull
docker compose down -v
docker compose build --no-cache
docker compose up
```

Accès :

- Frontend : `http://localhost:5173`
- Backend Swagger : `http://localhost:8000/docs`
- Healthcheck : `http://localhost:8000/health`

Compte de démonstration :

```text
admin@guineecare.local / admin123
```

## Déroulé de démonstration

### 1. Introduction

Message clé :

> GuinéeCare est une solution numérique hospitalière conçue pour moderniser progressivement la gestion des établissements de santé, améliorer la traçabilité et renforcer la capacité de pilotage de l’État.

### 2. Connexion sécurisée

Montrer :

- page de connexion ;
- compte administrateur ;
- accès sécurisé.

Message clé :

> Chaque utilisateur accède à la plateforme selon son rôle et ses permissions.

### 3. Dashboard

Montrer :

- indicateurs établissements ;
- patients ;
- admissions ;
- produits ;
- examens ;
- factures.

Message clé :

> Le dashboard donne une première vision opérationnelle de l’activité hospitalière.

### 4. Gestion patient

Action : créer un nouveau patient.

Message clé :

> Le dossier patient devient centralisé et réutilisable dans les autres modules.

### 5. Admission

Action : créer une admission pour le patient.

Message clé :

> L’hôpital peut suivre l’entrée, l’orientation et la sortie du patient.

### 6. Urgences

Action : créer un passage urgence.

Message clé :

> Les urgences peuvent être priorisées, suivies et orientées.

### 7. Pharmacie

Action : créer un mouvement de stock.

Message clé :

> Les stocks critiques sont suivis pour réduire les ruptures et les pertes.

### 8. Laboratoire

Action : créer une demande laboratoire puis saisir un résultat.

Message clé :

> Les demandes et résultats laboratoire deviennent traçables et intégrés au parcours patient.

### 9. Facturation

Action : créer une facture puis enregistrer un paiement.

Message clé :

> La plateforme améliore la transparence des recettes et le suivi des paiements.

### 10. Audit

Action : ouvrir la page activité/audit.

Message clé :

> Les actions sensibles sont journalisées, ce qui renforce la gouvernance et la confiance.

## Questions à anticiper

### Est-ce déployable dans les hôpitaux publics ?

Oui, la solution est pensée pour un déploiement progressif : pilote, extension régionale, puis généralisation nationale.

### Les données peuvent-elles rester en Guinée ?

Oui, l’architecture peut être déployée sur une infrastructure souveraine ou dans un cloud choisi par l’État.

### Peut-on intégrer les systèmes existants ?

Oui, la roadmap prévoit les intégrations avec les systèmes nationaux, DHIS2/SNIS, mobile money, assurance santé et identifiant patient national.

### Peut-on commencer petit ?

Oui, le projet peut démarrer par un hôpital pilote avec les modules patients, admissions, urgences, pharmacie, laboratoire et facturation.

## Conclusion de présentation

GuinéeCare Hospital Suite peut devenir une plateforme nationale de modernisation hospitalière, avec un démarrage rapide en pilote et une évolution progressive vers une solution SaaS entreprise pour le système de santé guinéen.

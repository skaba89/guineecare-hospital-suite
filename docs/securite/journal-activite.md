# Journal d'activité métier

## Objectif

Tracer les actions importantes réalisées dans l'application afin de renforcer la sécurité, la conformité et la capacité d'analyse en cas d'incident.

## Table technique

Le module utilise la table `activity_entries`.

Champs principaux :

- `id`
- `actor_id`
- `action_name`
- `entity_type`
- `entity_id`
- `level`
- `notes`
- `created_at`

## Actions déjà journalisées

- Création patient : `patient.created`
- Création admission : `admission.created`
- Clôture admission : `admission.closed`

## Niveaux recommandés

- `NORMAL` : action courante.
- `IMPORTANT` : action métier importante.
- `SENSITIVE` : action sensible.
- `CRITICAL` : action critique.

## Prochaines actions à journaliser

- Connexion utilisateur.
- Échec de connexion.
- Création utilisateur.
- Modification rôle.
- Création paiement.
- Clôture caisse.
- Validation laboratoire.
- Export de données.

## Bonnes pratiques

- Ne pas stocker de données médicales détaillées dans le champ `notes`.
- Stocker seulement les identifiants techniques nécessaires.
- Garder le détail métier dans les tables sources.
- Restreindre l'accès au journal aux profils autorisés.

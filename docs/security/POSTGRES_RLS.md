# PostgreSQL Row-Level Security — baseline nationale

## Objectif

GuinéeCare applique deux niveaux complémentaires d'isolation des établissements :

1. filtrage applicatif SQLAlchemy (`tenant_query`, contrôles de permissions) ;
2. PostgreSQL Row-Level Security (RLS) pour empêcher qu'une requête oubliée ou incorrecte puisse lire ou écrire les données d'un autre établissement.

La règle de sécurité est **fail-closed** : une table protégée ne retourne aucune donnée tenantée tant que le contexte PostgreSQL de la requête n'a pas été posé.

## Contexte de sécurité

Après validation du JWT et relecture de l'utilisateur en base, le backend pose deux paramètres PostgreSQL transactionnels :

- `app.current_facility_id` : établissement de l'utilisateur ;
- `app.is_super_admin` : `true` uniquement pour un `SUPER_ADMIN` autorisé au niveau national.

Les paramètres sont alimentés depuis la ligne `users` relue en base. Les claims `facility_id` et `role` du JWT ne constituent donc pas, à eux seuls, la source d'autorisation RLS.

Le contexte est posé avec `set_config(..., true)`, donc limité à la transaction. Un listener SQLAlchemy `after_begin` le réapplique automatiquement après chaque `commit()` d'une requête.

## Tables protégées — phase P0-B

La migration `0031_postgres_rls_fail_closed` active automatiquement RLS sur toutes les tables existantes dont la colonne `facility_id` est `NOT NULL`.

Cette règle couvre les objets dont l'appartenance à un établissement est non ambiguë, notamment les dossiers patients et de nombreuses données cliniques/opérationnelles.

Pour chaque table concernée :

```sql
ALTER TABLE ... ENABLE ROW LEVEL SECURITY;
ALTER TABLE ... FORCE ROW LEVEL SECURITY;
```

et une policy `guineecare_facility_isolation` applique la même condition à `USING` et `WITH CHECK`.

Conséquences :

- sans contexte : aucune ligne tenantée n'est visible ;
- utilisateur établissement A : lecture/écriture uniquement sur A ;
- tentative d'INSERT/UPDATE vers B : rejet PostgreSQL ;
- `SUPER_ADMIN` : accès cross-tenant explicite ;
- le propriétaire de table est également soumis au RLS grâce à `FORCE ROW LEVEL SECURITY`.

## Rôle PostgreSQL de l'application

Le compte utilisé par l'API en production doit impérativement être un rôle dédié :

- `NOSUPERUSER` ;
- `NOBYPASSRLS` ;
- sans droits de création de rôle/base ;
- avec uniquement les permissions SQL nécessaires à l'application.

Le compte propriétaire/migration Alembic doit rester distinct du compte runtime de l'API.

## Pourquoi les tables `facility_id IS NULL` ne sont pas incluses automatiquement

Certaines tables ont une sémantique plus complexe :

- `users` : nécessaire avant établissement du contexte lors de l'authentification ;
- `refresh_tokens` : utilisé pendant les flux d'authentification/rotation ;
- `audit_logs` : certaines traces peuvent être globales ;
- `notifications` : une notification sans établissement reste liée à un destinataire, donc `facility_id IS NULL` ne signifie pas « visible par tous » ;
- autres référentiels ou données nationales pouvant avoir une portée globale.

Une policy générique du type `facility_id IS NULL OR facility_id = current_facility` serait dangereuse : elle pourrait transformer une ligne utilisateur/globale en donnée lisible par tous les établissements.

Ces tables font l'objet d'une seconde phase avec policies spécifiques à leur domaine (user_id, recipient_id, niveau national, etc.).

## Validation automatisée

Le workflow `.github/workflows/postgres-rls.yml` démarre un vrai PostgreSQL et :

1. applique toutes les migrations avec le rôle propriétaire ;
2. crée `guineecare_app` avec `NOSUPERUSER` et `NOBYPASSRLS` ;
3. vérifie que sans contexte les patients sont invisibles ;
4. vérifie qu'un utilisateur de l'établissement A ne voit que A ;
5. vérifie que le contexte est réappliqué après un `commit()` ;
6. vérifie qu'un INSERT cross-tenant est bloqué par `WITH CHECK` ;
7. vérifie que `SUPER_ADMIN` obtient explicitement la vue cross-tenant ;
8. vérifie dans `pg_class` que chaque table `facility_id NOT NULL` possède RLS + FORCE RLS.

## Règles pour les futurs modèles

Lorsqu'une nouvelle table métier est créée :

- utiliser `facility_id NOT NULL` si chaque ligne appartient obligatoirement à un établissement ;
- la migration RLS suivante doit garantir qu'elle est protégée ;
- si `facility_id` est nullable, documenter précisément la signification de `NULL` et créer une policy métier dédiée ;
- ne jamais accorder `SUPERUSER` ou `BYPASSRLS` au compte runtime ;
- conserver les contrôles applicatifs en plus du RLS.

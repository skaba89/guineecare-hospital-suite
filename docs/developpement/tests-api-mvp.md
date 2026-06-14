# Tests API MVP

## Objectif

Valider rapidement que le socle backend, PostgreSQL et les premières routes métier fonctionnent.

## Démarrage

```bash
docker compose up --build
```

API :

- http://localhost:8000/health
- http://localhost:8000/docs

## Seed MVP

Dans le conteneur backend ou en local :

```bash
python -m backend.scripts.seed_mvp
```

Si la commande est lancée depuis le dossier `backend`, utiliser :

```bash
python -m scripts.seed_mvp
```

## Tests manuels dans Swagger

### 1. Vérifier le service

```http
GET /health
```

Résultat attendu : status ok.

### 2. Lister les établissements

```http
GET /api/v1/facilities
```

Résultat attendu : liste des établissements.

### 3. Créer un établissement

```json
{
  "code": "HP-KANKAN",
  "name": "Hôpital Régional de Kankan",
  "category": "Hôpital régional",
  "region": "Kankan",
  "prefecture": "Kankan"
}
```

### 4. Créer un service

```json
{
  "facility_id": "ID_ETABLISSEMENT",
  "code": "MED",
  "name": "Médecine générale",
  "category": "clinical"
}
```

### 5. Créer un patient

```json
{
  "facility_id": "ID_ETABLISSEMENT",
  "patient_number": "GC-PAT-000002",
  "first_name": "Mariama",
  "last_name": "Diallo"
}
```

### 6. Créer une admission

```json
{
  "facility_id": "ID_ETABLISSEMENT",
  "patient_id": "ID_PATIENT",
  "department_id": "ID_SERVICE",
  "admission_type": "CONSULTATION"
}
```

### 7. Clôturer une admission

```http
POST /api/v1/admissions/{admission_id}/close
```

## Prochaine étape automatisation

- Ajouter Pytest.
- Ajouter une base de test.
- Ajouter des tests d'intégration pour facilities, departments, patients et admissions.
- Ajouter GitHub Actions lorsque le connecteur permettra le fichier workflow.

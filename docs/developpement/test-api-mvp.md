# Test API MVP

## Lancer les services

```bash
docker compose up --build
```

## Vérifier la santé API

```bash
curl http://localhost:8000/health
```

Résultat attendu :

```json
{"status":"ok","service":"guineecare-backend"}
```

## Charger les données de démonstration

```bash
docker compose exec backend python -m scripts.seed_mvp
```

## Tester les établissements

```bash
curl http://localhost:8000/api/v1/facilities
```

## Créer un établissement

```bash
curl -X POST http://localhost:8000/api/v1/facilities \
  -H "Content-Type: application/json" \
  -d '{"code":"HP-KANKAN","name":"Hopital Regional de Kankan","category":"regional","region":"Kankan","prefecture":"Kankan"}'
```

## Créer un patient

```bash
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Content-Type: application/json" \
  -d '{"facility_id":"FACILITY_ID","patient_number":"GC-PAT-000002","first_name":"Aminata","last_name":"Diallo"}'
```

## Créer une admission

```bash
curl -X POST http://localhost:8000/api/v1/admissions \
  -H "Content-Type: application/json" \
  -d '{"facility_id":"FACILITY_ID","patient_id":"PATIENT_ID","department_id":"DEPARTMENT_ID","admission_type":"consultation"}'
```

## Documentation Swagger

Ouvrir :

http://localhost:8000/docs

# Recette API MVP — GuinéeCare Hospital Suite

## Objectif

Tester le parcours API MVP après lancement local et seed de démonstration.

## 1. Démarrer le projet

```bash
docker compose up --build
```

Dans un autre terminal :

```bash
cd backend
python -m app.db.seed
```

## 2. Se connecter

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@guineecare.com","password":"admin123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

## 3. Vérifier les référentiels

```bash
curl http://localhost:8000/api/v1/facilities -H "Authorization: Bearer $TOKEN"
curl http://localhost:8000/api/v1/departments -H "Authorization: Bearer $TOKEN"
curl http://localhost:8000/api/v1/patients -H "Authorization: Bearer $TOKEN"
```

## 4. Tester les urgences

Créer un passage urgence :

```bash
curl -X POST http://localhost:8000/api/v1/emergency/visits \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"facility_id":"FACILITY_ID","patient_id":"PATIENT_ID","priority_level":"NORMAL","chief_complaint":"Fievre et fatigue"}'
```

Voir la file urgence :

```bash
curl http://localhost:8000/api/v1/emergency/queue -H "Authorization: Bearer $TOKEN"
```

## 5. Tester la pharmacie

Lister les produits :

```bash
curl http://localhost:8000/api/v1/pharmacy/products -H "Authorization: Bearer $TOKEN"
```

Lister le stock :

```bash
curl http://localhost:8000/api/v1/pharmacy/stock -H "Authorization: Bearer $TOKEN"
```

Créer une sortie stock :

```bash
curl -X POST http://localhost:8000/api/v1/pharmacy/stock/movements \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"facility_id":"FACILITY_ID","product_id":"PRODUCT_ID","movement_type":"OUT","quantity":10,"reason":"Dispensation test"}'
```

## 6. Tester le laboratoire

Lister les examens :

```bash
curl http://localhost:8000/api/v1/laboratory/tests -H "Authorization: Bearer $TOKEN"
```

Créer une demande :

```bash
curl -X POST http://localhost:8000/api/v1/laboratory/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"facility_id":"FACILITY_ID","patient_id":"PATIENT_ID","test_id":"TEST_ID","priority":"NORMAL"}'
```

Saisir un résultat :

```bash
curl -X POST http://localhost:8000/api/v1/laboratory/orders/ORDER_ID/results \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"facility_id":"FACILITY_ID","result_value":"Normal","interpretation":"RAS"}'
```

Valider un résultat :

```bash
curl -X POST http://localhost:8000/api/v1/laboratory/results/RESULT_ID/validate \
  -H "Authorization: Bearer $TOKEN"
```

## 7. Tester la facturation

Lister les tarifs :

```bash
curl http://localhost:8000/api/v1/billing/tariffs -H "Authorization: Bearer $TOKEN"
```

Créer une facture :

```bash
curl -X POST http://localhost:8000/api/v1/billing/invoices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"facility_id":"FACILITY_ID","patient_id":"PATIENT_ID","invoice_number":"INV-000001","description":"Consultation test","net_amount":50000}'
```

Encaisser un paiement :

```bash
curl -X POST http://localhost:8000/api/v1/billing/invoices/INVOICE_ID/payments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"facility_id":"FACILITY_ID","amount":50000,"payment_method":"CASH"}'
```

## Résultat attendu

- Les routes protégées refusent les appels sans token.
- Les routes acceptent les appels avec token admin.
- Les données seedées sont visibles.
- Les mouvements stock mettent à jour le stock.
- Les résultats laboratoire peuvent être validés.
- Les paiements mettent à jour la facture.

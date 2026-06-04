# Structure frontend — GuinéeCare Hospital Suite

## Objectif

Rendre le frontend plus maintenable en séparant les responsabilités : types, hooks, composants réutilisables, services API et pages métier.

## Structure actuelle

```text
frontend/src/
  App.tsx
  main.tsx
  styles.css
  types.ts

  services/
    api.ts
    authService.ts

  hooks/
    useLookupData.ts

  utils/
    options.ts

  components/
    ResourcePage.tsx
    ResourceTable.tsx
    SimpleForm.tsx
```

## Responsabilités

### `types.ts`

Contient les types partagés :

- `Row`
- `FormValues`
- `Option`
- `FieldConfig`
- `LookupData`
- `emptyLookups`

### `hooks/useLookupData.ts`

Charge les données nécessaires aux listes déroulantes :

- établissements ;
- patients ;
- services ;
- admissions ;
- produits ;
- examens laboratoire ;
- demandes laboratoire ;
- factures.

### `utils/options.ts`

Transforme les données API en options utilisables par les listes déroulantes.

### `components/SimpleForm.tsx`

Composant formulaire générique avec :

- champs texte ;
- champs numériques ;
- listes déroulantes ;
- message de succès ;
- message d'erreur.

### `components/ResourceTable.tsx`

Composant tableau avec :

- recherche globale ;
- filtre par statut ;
- tri par colonne ;
- compteur de résultats ;
- affichage responsive.

### `components/ResourcePage.tsx`

Composant page générique qui :

- charge les données depuis l'API ;
- affiche un formulaire optionnel ;
- affiche le tableau métier.

### `App.tsx`

Orchestre :

- login ;
- menu ;
- dashboard ;
- pages métier ;
- rafraîchissement global.

## Prochaine étape de refactoring

Créer des pages séparées :

```text
frontend/src/pages/
  DashboardPage.tsx
  PatientsPage.tsx
  AdmissionsPage.tsx
  EmergencyPage.tsx
  PharmacyPage.tsx
  LaboratoryPage.tsx
  BillingPage.tsx
```

Puis créer des formulaires métier séparés :

```text
frontend/src/forms/
  PatientForm.tsx
  AdmissionForm.tsx
  EmergencyForm.tsx
  PharmacyForms.tsx
  LaboratoryForms.tsx
  BillingForms.tsx
```

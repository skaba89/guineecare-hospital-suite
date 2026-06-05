# Structure frontend — GuinéeCare Hospital Suite

## Objectif

Rendre le frontend plus maintenable en séparant les responsabilités : layout, types, hooks, composants réutilisables, services API, formulaires métier et pages.

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

  layout/
    AppLayout.tsx
    Sidebar.tsx

  components/
    ResourcePage.tsx
    ResourceTable.tsx
    SimpleForm.tsx

  forms/
    PatientForm.tsx
    AdmissionForm.tsx
    EmergencyForm.tsx
    PharmacyForms.tsx
    LaboratoryForms.tsx
    BillingForms.tsx

  pages/
    DashboardPage.tsx
    LoginPage.tsx
    PatientsPage.tsx
    AdmissionsPage.tsx
    EmergencyPage.tsx
    PharmacyPage.tsx
    LabPage.tsx
    FinancePage.tsx
```

## Responsabilités

### `layout/AppLayout.tsx`

Structure générale après connexion :

- sidebar ;
- zone principale ;
- rendu des pages enfants.

### `layout/Sidebar.tsx`

Menu latéral :

- navigation entre pages ;
- état actif ;
- déconnexion.

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

### `forms/`

Contient les formulaires métier branchés aux endpoints API :

- création patient ;
- création admission ;
- passage urgence ;
- produit et mouvement pharmacie ;
- examen, demande et résultat laboratoire ;
- facture et paiement.

### `pages/`

Contient les pages métier qui composent `ResourcePage` et les formulaires associés.

### `App.tsx`

Orchestre seulement :

- l'état d'authentification ;
- la vérification de session existante ;
- le choix de page ;
- le rafraîchissement global ;
- le rendu du layout et des pages.

## Prochaine étape de refactoring

Ajouter un vrai router React :

```text
frontend/src/router/
  routes.tsx
```

Puis améliorer l'expérience utilisateur :

- validation de formulaire ;
- confirmations avant actions sensibles ;
- pagination ;
- états de chargement ;
- messages d'erreur plus explicites.

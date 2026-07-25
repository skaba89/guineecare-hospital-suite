# Fiche rapide — Recherche ICD-11 🔍

> Public : médecins, sages-femmes, infirmiers (rôles cliniques)
> Module(s) : Patients → Détail patient → Diagnostics
> Version : v2.9.2 — juillet 2026
> À imprimer recto-verso et à garder à portée de main au poste de travail.

---

## Quand utiliser la recherche ICD-11 ?

Quand vous ajoutez un **nouveau diagnostic** au dossier d'un patient, le champ "Diagnostic" propose désormais une **autocomplétion** sur les codes ICD-11 (classification OMS 2022).

## Comment rechercher

| Étape | Action |
|-------|--------|
| 1 | Ouvrir le dossier patient, onglet **Diagnostics** |
| 2 | Cliquer **Nouveau diagnostic** |
| 3 | Dans le champ "Diagnostic (recherche ICD-11)", taper : |
|   | • un **libellé** : "paludisme", "hypertension", "diabète" |
|   | • un **code** : "1F03", "BA00" |
|   | • en **français ou anglais** : "malaria", "asthma" |
| 4 | Après 300ms, une liste déroulante affiche les 10 premiers résultats |
| 5 | Naviguer avec ↑/↓ au clavier, ou cliquer |
| 6 | **Enter** ou **clic** pour sélectionner |
| 7 | Le code ICD-11 s'affiche en **badge bleu** sous le champ |

## Codes les plus utiles en Guinée

| Diagnostic | Code ICD-11 | Catégorie |
|------------|-------------|-----------|
| Paludisme à P. falciparum | 1F03 | Infectieux |
| Paludisme non précisé | 1F2Z | Infectieux |
| Tuberculose respiratoire | 1B11 | Infectieux |
| Ebola | 1E74 | Infectieux |
| Fièvre de Lassa | 1E73 | Infectieux |
| VIH | 1H0Z | Infectieux |
| Pneumonie | CA40 | Respiratoire |
| Asthme | CA03 | Respiratoire |
| Hypertension essentielle | BA00 | Cardiovasculaire |
| Insuffisance cardiaque | BB71 | Cardiovasculaire |
| Diabète type 2 | 5A1A | Endocrinien |
| Diabète type 1 | 5A11 | Endocrinien |
| Malnutrition sévère | 5A90 | Endocrinien |
| Grossesse extra-utérine | JA60 | Grossesse |
| Prééclampsie sévère | JB02 | Grossesse |
| Hémorragie post-partum | JC24 | Grossesse |
| AVC ischémique | 8B40 | Neurologique |
| Épilepsie | 8A20 | Neurologique |
| Dépression | 6A70 | Santé mentale |

## Et si le code n'existe pas ?

- ✅ Vérifier l'orthographe (le moteur est insensible à la casse)
- ✅ Essayer en anglais ("malaria" au lieu de "paludisme")
- ✅ Saisir un **libellé libre** : tapez simplement le texte sans sélectionner de suggestion. Le champ "Code" restera vide (ce qui est acceptable).

> 📝 Le catalogue embarqué contient ~80 codes. Pour la liste complète (55 000+ codes), une intégration API OMS officielle est prévue en V3.1 (2027).

---

> 📖 Documentation complète : `docs/formation/GUIDE_UTILISATEUR_v2.9.2.md` section 3
> 📞 Support : tech@guineecare.gn — poste 4012

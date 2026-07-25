# Fiche rapide — Vue scroll infini ♾️

> Public : tous les utilisateurs
> Module(s) : Patients
> Version : v2.9.2 — juillet 2026
> À imprimer recto-verso et à garder à portée de main au poste de travail.

---

## Activer la vue scroll infini

| Étape | Action |
|-------|--------|
| 1 | Aller sur la page **Patients** |
| 2 | Chercher le bouton **"Vue scroll infini"** (en haut à droite) |
| 3 | Cliquer dessus — la vue change immédiatement |
| 4 | La préférence est mémorisée — vous resterez en vue scroll infini aux prochaines visites |

## Comment ça marche ?

- ✅ **Scroll naturel** : la page suivante se charge automatiquement quand vous approchez du bas (200px avant)
- ✅ **Append-only** : les patients déjà chargés restent visibles
- ✅ **Recherche** : tapez dans le champ, la liste se filtre en direct (debounce 300ms)
- ✅ **Modal patient** : cliquez sur un patient pour voir un résumé rapide

## Différences avec la vue paginée

| Aspect | Vue paginée | Vue scroll infini |
|--------|-------------|-------------------|
| Navigation | Boutons Précédent/Suivant | Scroll de la souris |
| Recherche | Champ + bouton | Champ en direct |
| Chargement | Manuel (clic page suivante) | Automatique |
| Saut direct | Possible (numéro de page) | Non (scroll seul) |
| Idéal pour | Recherche précise | Consultation rapide |

## Quand utiliser quoi ?

- 🎯 **Vue paginée** : si vous cherchez un patient précis et que vous connaissez sa position dans la liste alphabétique
- 📜 **Vue scroll infini** : si vous parcourez les patients pour une revue globale (gardes, audits, statistiques)

## Indicateurs visuels

| Indicateur | Signification |
|------------|---------------|
| 🔄 "Chargement de plus de patients…" | Page suivante en cours de chargement |
| ✓ "Tous les patients chargés (N/total)" | Vous avez atteint la fin de la liste |
| 👥 Avatar avec initiales | Patient dans la liste |
| 📋 Clic sur un patient | Ouvre une modale avec résumé (âge, sexe, téléphone) |

## Revenir à la vue paginée

Cliquer sur le bouton **"Vue paginée"** (en haut à droite). La préférence est également mémorisée.

---

> 📖 Documentation complète : `docs/formation/GUIDE_UTILISATEUR_v2.9.2.md` section 4
> 📞 Support : tech@guineecare.gn — poste 4012

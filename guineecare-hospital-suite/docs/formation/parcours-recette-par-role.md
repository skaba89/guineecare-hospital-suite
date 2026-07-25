# Parcours de recette par rôle — GuinéeCare Hospital Suite

> Public : formateurs, super-utilisateurs, utilisateurs en auto-évaluation
> Usage : check-list de validation des compétences critiques par rôle
> Critère de réussite : 100 % des actions du parcours réalisées sans
> assistance en moins de 30 minutes chacune.

Chaque parcours ci-dessous liste les actions qu'un utilisateur doit
être capable de réaliser seul pour être considéré comme **opérationnel**
sur son périmètre. Le formateur valide chaque action pendant la
session de formation et signe la fiche de validation.

---

## Comment utiliser ce document

1. **Pendant la formation** : le formateur lit chaque action à voix
   haute, l'utilisateur la réalise sur l'environnement de formation.
   Le formateur coche la case et note le temps mis.
2. **En auto-évaluation** : l'utilisateur parcourt la liste seul, à
   son rythme, et note les actions qu'il n'a pas su réaliser pour en
   discuter au prochain point de formation.
3. **En recette de production** : avant la mise en service réelle,
   chaque utilisateur doit avoir validé 100 % de son parcours.

Le temps total estimé par parcours est de 30 à 60 minutes selon le
rôle.

---

## 1. Agent d'admission

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter avec son compte | Arrivée sur le tableau de bord en moins de 10 s |
| ☐ | Créer un nouveau patient (tous champs obligatoires) | Numéro `PAT-...` généré, patient visible dans la liste |
| ☐ | Rechercher un patient par nom | Le patient apparaît dans les résultats |
| ☐ | Rechercher un patient par numéro de dossier | Le bon patient est trouvé |
| ☐ | Ouvrir le DPI d'un patient | Tous les onglets s'affichent correctement |
| ☐ | Créer une admission programmée | Admission visible dans la liste des admissions |
| ☐ | Créer une admission urgente | Statut `urgent` correctement attribué |
| ☐ | Filtrer les admissions par statut | Seules les admissions du statut choisi s'affichent |
| ☐ | Clôturer une admission | Le statut passe à `closed` |
| ☐ | Consulter la file d'attente | Liste des patients en attente visible |
| ☐ | Appeler un patient depuis la file d'attente | Le patient passe en statut `in_consultation` |
| ☐ | Changer son mot de passe | Nouveau mot de passe accepté, reconnexion OK |
| ☐ | Envoyer un feedback | Le feedback apparaît dans la liste (vue admin) |

**Temps total estimé** : 35 minutes.

---

## 2. Médecin

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter et consulter le tableau de bord | KPI temps réel affichés |
| ☐ | Rechercher un patient par nom | Patient trouvé |
| ☐ | Ouvrir le DPI complet | Tous onglets accessibles |
| ☐ | Saisir une note clinique | Note enregistrée, visible dans l'historique |
| ☐ | Saisir des constantes (TA, T°, pouls, poids, taille) | Constantes affichées dans le graphique |
| ☐ | Ajouter un antécédent médical | Antécédent visible dans l'onglet correspondant |
| ☐ | Ajouter une allergie | Allergie visible et signalée en alerte |
| ☐ | Créer un diagnostic (CIM-10 libre) | Diagnostic enregistré |
| ☐ | Créer une prescription médicamenteuse | Prescription visible par le pharmacien |
| ☐ | Créer une demande de laboratoire | Demande visible par le technicien labo |
| ☐ | Créer une demande d'imagerie | Demande visible par la radiologie |
| ☐ | Programmer une intervention au bloc | Intervention visible dans le planning bloc |
| ☐ | Consulter les résultats de laboratoire d'un patient | Résultats validés accessibles |
| ☐ | Consulter les comptes rendus d'imagerie | CR accessibles et lisibles |
| ☐ | Valider une sortie d'hospitalisation | Sortie effective, lit libéré |
| ☐ | Consulter le journal d'audit de ses propres actions | Liste des actions récentes visible |

**Temps total estimé** : 50 minutes.

---

## 3. Infirmier

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter et consulter le tableau de bord | KPI lits occupés visible |
| ☐ | Ouvrir le bed-board de son service | Lits affichés avec leur état |
| ☐ | Identifier les patients par lit | Nom du patient affiché sur le lit occupé |
| ☐ | Ouvrir le DPI d'un patient hospitalisé | DPI accessible |
| ☐ | Saisir des constantes | Constantes horodatées et visibles dans le graphique |
| ☐ | Saisir un soin (pansement, injection, etc.) | Soin enregistré avec horodatage |
| ☐ | Administrer un médicament prescrit | Médicament marqué comme administré |
| ☐ | Consulter la liste des prescriptions en cours | Prescriptions du jour visibles |
| ☐ | Marquer une prescription comme administrée | Horodatage et utilisateur tracés |
| ☐ | Saisir une note de transmission | Note visible par l'équipe suivante |
| ☐ | Effectuer un triage d'urgence (niveaux 1-5) | Niveau de triage correctement attribué |
| ☐ | Orienter un patient vers un service | Orientation visible dans la file du service cible |
| ☐ | Consulter les notes cliniques du médecin | Notes accessibles et lisibles |
| ☐ | Signaler un incident qualité (chute, erreur méd) | Incident créé dans le module qualité |

**Temps total estimé** : 45 minutes.

---

## 4. Sage-femme

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter et consulter le tableau de bord maternité | Grossesses en suivi visibles |
| ☐ | Créer un dossier de grossesse | Dossier lié au bon patient |
| ☐ | Réaliser une consultation prénatale (CPoN) | Consultation enregistrée avec poids, TA, hauteur utérine |
| ☐ | Saisir un échographie obstétricale | Résultat échographique enregistré |
| ☐ | Enregistrer un accouchement | Date/heure, voie, complications renseignés |
| ☐ | Saisir les données du nouveau-né (poids, APGAR) | Données néonatales enregistrées |
| ☐ | Programmer une CPoN post-natale | Rendez-vous visible dans le planning |
| ☐ | Consulter l'historique des grossesses d'une patiente | Toutes les grossesses passées visibles |
| ☐ | Détecter une grossesse à risque (alertes auto) | Alertes visibles dans le dossier |
| ☐ | Référer une patiente vers un spécialiste | Référence tracée dans le dossier |
| ☐ | Consulter les résultats de labo de la patiente | Résultats visibles (sérologies, NFS, etc.) |
| ☐ | Signaler un incident maternel ou néonatal | Incident créé dans le module qualité |

**Temps total estimé** : 40 minutes.

---

## 5. Pharmacien

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter et consulter le tableau de bord pharmacie | Stock critique et alertes visibles |
| ☐ | Consulter le stock par produit | Quantités et seuils visibles |
| ☐ | Rechercher un produit par nom ou DCI | Produit trouvé rapidement |
| ☐ | Filtrer les produits en rupture de stock | Liste correcte |
| ☐ | Filtrer les produits en seuil d'alerte | Liste correcte |
| ☐ | Réceptionner une livraison | Stock incrémenté, mouvement tracé |
| ☐ | Créer un mouvement de stock manuel (ajustement) | Mouvement tracé avec motif |
| ☐ | Dispenser un médicament à un patient | Dispensation enregistrée, stock décrémenté |
| ☐ | Consulter l'historique de dispensation d'un patient | Toutes les dispensations visibles |
| ☐ | Vérifier une prescription avant dispensation | Interactions et allergies affichées |
| ☐ | Signaler une rupture de stock imminente | Alerte remontée à l'ADMIN |
| ☐ | Exporter l'inventaire de stock | Export téléchargé (CSV ou PDF) |

**Temps total estimé** : 35 minutes.

---

## 6. Technicien de laboratoire

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter et consulter la file d'attente labo | Demandes en attente visibles |
| ☐ | Consulter une demande de laboratoire | Détails (analyses, patient, prescripteur) visibles |
| ☐ | Créer un prélèvement | Prélèvement horodaté et lié à la demande |
| ☐ | Saisir un résultat d'analyse | Résultat enregistré avec valeurs et unités |
| ☐ | Valider un résultat | Statut `validated` et tracé |
| ☐ | Rejeter un prélèvement non conforme | Statut `rejected` avec motif |
| ☐ | Filtrer les demandes par statut | Filtre opérationnel |
| ☐ | Filtrer les demandes par analyse | Filtre opérationnel |
| ☐ | Consulter l'historique des résultats d'un patient | Tous les résultats visibles |
| ☐ | Imprimer un résultat validé | Impression correcte via navigateur |
| ☐ | Signaler une anomalie (échantillon hémolysé, etc.) | Anomalie tracée |

**Temps total estimé** : 30 minutes.

---

## 7. Manipulateur en radiologie

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter et consulter la file d'attente imagerie | Demandes en attente visibles |
| ☐ | Consulter une demande d'imagerie | Détails (type d'examen, patient, prescripteur) visibles |
| ☐ | Programmer une examination dans le planning | Créneau visible dans le planning |
| ☐ | Réaliser une examination et saisir un compte rendu | CR enregistré, statut `completed` |
| ☐ | Valider un compte rendu | Statut `validated` |
| ☐ | Filtrer les demandes par type d'examen | Filtre opérationnel |
| ☐ | Filtrer les demandes par statut | Filtre opérationnel |
| ☐ | Consulter l'historique des examens d'un patient | Tous les examens visibles |
| ☐ | Imprimer un compte rendu validé | Impression correcte |
| ☐ | Signaler une contre-indication (grossesse, allergie) | Alerte remontée au prescripteur |

**Temps total estimé** : 30 minutes.

---

## 8. Caissier

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter et consulter le tableau de bord caisse | Encaissements du jour visibles |
| ☐ | Créer une facture pour un patient | Facture générée avec lignes et total |
| ☐ | Ajouter une ligne à une facture existante | Ligne ajoutée, total recalculé |
| ☐ | Encaisser un paiement (espèces) | Paiement enregistré, reçu généré |
| ☐ | Encaisser un paiement (mobile money) | Paiement enregistré, référence tracée |
| ☐ | Consulter l'historique des paiements d'un patient | Tous les paiements visibles |
| ☐ | Imprimer un reçu | Impression correcte |
| ☐ | Clôturer la caisse en fin de journée | Total calculé et rapproché |
| ☐ | Filtrer les factures par statut (payée, impayée) | Filtre opérationnel |
| ☐ | Annuler une facture erronée | Annulation tracée avec motif |
| ☐ | Consulter les tarifs applicables | Tarifs visibles par catégorie |

**Temps total estimé** : 30 minutes.

---

## 9. Direction

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter et consulter le tableau de bord direction | KPI globaux visibles |
| ☐ | Consulter les indicateurs de fréquentation | Patients, admissions, lits occupés |
| ☐ | Consulter les indicateurs financiers | Encaissements, impayés, EV |
| ☐ | Consulter les indicateurs qualité | Incidents, satisfaction, conformité |
| ☐ | Filtrer les indicateurs par période | Filtre opérationnel |
| ☐ | Comparer les indicateurs entre services | Vue comparative accessible |
| ☐ | Consulter le journal d'audit global | Actions sensibles visibles |
| ☐ | Exporter un rapport mensuel | Export téléchargé (PDF ou CSV) |
| ☐ | Consulter les feedbacks utilisateurs de l'établissement | Liste filtrable par catégorie et statut |
| ☐ | Trier et résoudre un feedback | Statut changé, réponse enregistrée |

**Temps total estimé** : 30 minutes.

---

## 10. Administrateur

| ☐ | Action | Critère de réussite |
|---|--------|---------------------|
| ☐ | Se connecter en ADMIN | Tableau de bord admin visible |
| ☐ | Créer un nouvel utilisateur | Compte créé avec rôle et établissement corrects |
| ☐ | Modifier le rôle d'un utilisateur | Modification effective et tracée |
| ☐ | Activer / désactiver un utilisateur | Statut changé |
| ☐ | Débloquer un compte verrouillé | Compte immédiatement utilisable |
| ☐ | Réinitialiser le mot de passe d'un utilisateur | Mot de passe temporaire généré |
| ☐ | Créer un rôle personnalisé | Rôle créé avec permissions spécifiques |
| ☐ | Attribuer / retirer une permission à un rôle | Modification effective |
| ☐ | Consulter la matrice RBAC | Vue d'ensemble correcte |
| ☐ | Créer un nouvel établissement | Établissement visible dans la liste |
| ☐ | Créer un nouveau département | Département visible dans la liste |
| ☐ | Consulter le journal d'audit complet | Toutes les actions visibles |
| ☐ | Filtrer l'audit par utilisateur / action / date | Filtres opérationnels |
| ☐ | Exporter l'audit | Export téléchargé |
| ☐ | Lister les feedbacks de l'établissement | Liste filtrable visible |
| ☐ | Résoudre / clôturer un feedback | Statut changé avec réponse |
| ☐ | Consulter les métriques Prometheus | Page `/metrics` accessible (avec token) |
| ☐ | Vérifier l'état de santé de l'application | `/health` et `/health/ready` verts |
| ☐ | Lancer un backup manuel | Backup créé et listé |
| ☐ | Restaurer un backup de test | Restauration réussie en environnement test |

**Temps total estimé** : 60 minutes.

---

## Validation et signature

Une fois le parcours terminé, le formateur et l'utilisateur signent la
fiche de validation (papier) :

```
Parcours de recette validé pour : _________________________________
Rôle : ______________________   Établissement : __________________
Date : _____________________   Durée totale : ____________________
Formateur (nom + signature) : ____________________________________
Utilisateur (nom + signature) : ___________________________________
```

La fiche est conservée par la direction médicale et par l'équipe
projet. Une copie numérique est ajoutée au dossier de formation de
l'utilisateur.

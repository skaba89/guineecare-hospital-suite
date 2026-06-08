# Checklist avant rendez-vous de démonstration

## 1. Préparation technique

- Faire `git pull`.
- Lancer `docker compose down -v`.
- Lancer `docker compose build --no-cache`.
- Lancer `docker compose up`.
- Vérifier que PostgreSQL est healthy.
- Vérifier que le backend est healthy.
- Vérifier que le frontend est accessible.

## 2. URLs à vérifier

- Frontend : `http://localhost:5173`
- Backend : `http://localhost:8000/health`
- Swagger : `http://localhost:8000/docs`

## 3. Compte de démonstration

- Email : `admin@guineecare.local`
- Mot de passe : `admin123`

## 4. Données à préparer

- Un patient de démonstration.
- Une admission.
- Un passage urgence.
- Un produit pharmacie.
- Un mouvement de stock.
- Un examen laboratoire.
- Une facture.
- Un paiement.
- Quelques lignes d’audit.

## 5. Parcours de démonstration

1. Connexion.
2. Dashboard.
3. Patients.
4. Admissions.
5. Urgences.
6. Pharmacie.
7. Laboratoire.
8. Facturation.
9. Audit.
10. Conclusion institutionnelle.

## 6. Messages clés

- La solution peut démarrer par un pilote.
- Les données peuvent rester hébergées dans une infrastructure souveraine.
- La plateforme est progressive et extensible.
- L’objectif est d’améliorer la gestion, la traçabilité et le pilotage.
- Le projet peut devenir un socle national de modernisation hospitalière.

## 7. Points à éviter pendant la démo

- Ne pas entrer dans trop de détails techniques au début.
- Ne pas présenter le projet comme terminé à 100 %.
- Expliquer clairement qu’il s’agit d’un socle démontrable et évolutif.
- Ne pas promettre une généralisation immédiate sans phase pilote.

## 8. Conclusion à utiliser

GuinéeCare Hospital Suite permet de démontrer rapidement comment une plateforme hospitalière moderne peut améliorer l’organisation, la traçabilité, la transparence et le pilotage du système de santé. La prochaine étape recommandée est un pilote encadré dans un établissement de référence.

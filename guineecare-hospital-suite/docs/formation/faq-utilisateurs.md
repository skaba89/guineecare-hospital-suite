# FAQ — Foire aux questions utilisateurs

> Public : utilisateurs finaux de GuinéeCare Hospital Suite
> Dernière mise à jour : 2026-06-21 (v1.1.0)

Cette FAQ regroupe les questions les plus fréquentes posées pendant
les sessions de formation et via le canal feedback de l'application.
Elle est enrichie en continu à mesure que de nouvelles questions
remontent.

---

## Connexion et compte

### Q1. J'ai oublié mon mot de passe. Que faire ?

Contactez l'administrateur du CHU Donka (poste 4012, bureau direction
informatique, 8h-17h en semaine). Il vous remettra un mot de passe
temporaire que vous devrez changer à la première connexion. Pour des
raisons de sécurité, il n'existe pas de procédure d'auto-récupération
par email — les mots de passe ne sont jamais envoyés par email.

### Q2. Mon compte est bloqué après plusieurs échecs. Que faire ?

Après 5 tentatives de connexion échouées, le compte est verrouillé
pendant 15 minutes (protection contre le bruteforce). Attendez 15
minutes et réessayez. Si l'urgence ne permet pas d'attendre,
l'administrateur peut débloquer votre compte immédiatement
(menu **Utilisateurs** → sélectionnez votre compte → **Débloquer**).

### Q3. Puis-je changer mon email de connexion ?

L'email est votre identifiant unique et ne peut pas être changé par
l'utilisateur lui-même. Si votre email change (départ, mutation),
l'administrateur peut créer un nouveau compte avec le nouvel email et
désactiver l'ancien. L'historique des actions reste associé à
l'ancien compte pour la traçabilité.

### Q4. Puis-je me connecter depuis chez moi ?

Non. Par défaut, l'application n'est accessible que depuis le réseau
interne du CHU Donka. Un accès distant (VPN) est en cours d'étude pour
les gardes et astreintes — il sera strictement encadré et limité aux
médecins urgentistes et au personnel de direction. Tout accès distant
sera tracé dans le journal d'audit.

### Q5. Que se passe-t-il si je ferme mon navigateur sans me déconnecter ?

Votre session JWT expire automatiquement après 60 minutes
d'inactivité. Vous n'avez donc pas besoin de vous inquiéter : même si
vous fermez sans déconnecter, personne ne pourra reprendre votre
session en rouvrant le navigateur (le token est stocké en mémoire et
non dans un cookie persistant). Toutefois, par sécurité, utilisez
toujours le bouton **Déconnexion** en fin de journée.

---

## Patients et DPI

### Q6. Comment créer un patient quand je ne connais pas sa date de naissance ?

Le champ **Date de naissance** est obligatoire. Si le patient ne
connaît pas sa date exacte (cas fréquent pour les personnes âgées en
zone rurale), saisissez le 1er janvier d'une année approximative (par
exemple `1950-01-01` pour une personne que vous estimez avoir environ
75 ans). Cochez ensuite la case **Date approximative** (si disponible)
ou ajoutez une note dans le champ **Commentaires**. L'âge affiché
sera calculé à partir de cette date.

### Q7. Deux patients ont le même nom et le même prénom. Comment les différencier ?

Le système génère un **numéro de dossier unique** au format
`PAT-YYYYMMDDHHMMSS` pour chaque patient. Quand vous recherchez par
nom, plusieurs résultats peuvent apparaître. Vérifiez alors la date
de naissance, le sexe et l'adresse pour identifier le bon patient.
En cas de doute persistant, vérifiez avec le patient lui-même son
numéro de dossier (s'il l'a déjà reçu sur un document).

### Q8. J'ai créé un patient par erreur (doublon). Que faire ?

Vous ne pouvez pas supprimer un patient (la suppression est interdite
pour préserver l'historique médical et la traçabilité). Contactez
l'administrateur en lui précisant les deux numéros de dossier à
fusionner. Il existe une procédure de fusion qui déplace toutes les
données du doublon vers le patient principal puis marque le doublon
comme **fusionné** (invisible dans les recherches mais conservé en
base pour audit).

### Q9. Comment accéder au DPI d'un patient que j'ai consulté hier ?

Deux options :
1. Menu **Mon profil → Items récents** — affiche les 20 derniers
   patients (et autres ressources) que vous avez consultés.
2. Menu **Patients** → champ de recherche — tapez le nom ou le
   numéro de dossier.

### Q10. Les données d'un patient sont visibles par quels rôles ?

Le DPI est régi par le RBAC et l'isolation multi-tenant :

- Tous les soignants (médecins, infirmiers, sages-femmes) de votre
  propre établissement peuvent consulter le DPI complet du patient.
- Les pharmaciens, techniciens de laboratoire, manipulateurs radio et
  caissiers ont accès aux données nécessaires à leur fonction
  (prescriptions, résultats, factures).
- Le SUPER_ADMIN (équipe projet) voit tous les patients de tous les
  établissements — pour le pilotage national uniquement.
- Un soignant d'un autre établissement ne voit jamais vos patients.
- Toutes les consultations sont tracées dans le journal d'audit.

---

## Saisie et données

### Q11. J'ai saisi une constante erronée. Puis-je la corriger ?

Oui, tant que la mesure a été saisie dans les dernières 24 heures.
Ouvrez la mesure → **Modifier** → corrigez → **Enregistrer**.
L'ancienne valeur est conservée dans l'historique (audit log) avec
le motif de modification. Au-delà de 24 heures, la mesure ne peut
plus être modifiée — ajoutez une nouvelle mesure avec la valeur
correcte et une note expliquant la correction.

### Q12. Le système a planté pendant que je saisissais. Mes données sont perdues ?

Non, pour deux raisons :
1. Le formulaire de saisie enregistre automatiquement un brouillon
   toutes les 30 secondes dans le stockage local du navigateur. En
   rouvrant la même page, vous retrouvez votre brouillon.
2. Si vous aviez cliqué sur **Enregistrer** avant le plantage, les
   données sont en base et seront visibles au redémarrage.

En cas de doute, ne resaisissez pas immédiatement — vérifiez d'abord
que la saisie n'existe pas déjà (pour éviter un doublon).

### Q13. Puis-je saisir des données pour une date passée (par exemple rattraper une saisie manquée hier) ?

Oui. Dans la plupart des formulaires de saisie clinique (constantes,
notes, prescriptions), un champ **Date/Heure** permet de spécifier le
moment réel de l'événement. Le système enregistre deux dates : la
date effective (celle que vous saisissez) et la date de saisie
(automatique, pour traçabilité). L'audit log conserve les deux.

### Q14. Comment imprimer une ordonnance ou un compte rendu ?

La version v1.0.0 ne propose pas encore d'impression PDF native. En
attendant (prévu en v1.2), vous pouvez utiliser la fonction
**Imprimer** de votre navigateur (Ctrl+P) qui génère une mise en page
correcte grâce aux styles d'impression intégrés. Pour les
ordonnances, un modèle PDF dédié est en cours de développement.

---

## Permissions et RBAC

### Q15. Je ne vois pas un module auquel je devrais avoir accès. Que faire ?

Vérifiez d'abord avec votre chef de service que la permission est
effectivement attribuée à votre rôle. Si oui, contactez
l'administrateur (poste 4012) qui vérifiera votre compte et ajustera
les permissions si nécessaire. Ne demandez jamais à un collègue de
vous passer son compte pour accéder à un module — cela viole la
politique de sécurité et est tracé dans l'audit log.

### Q16. Puis-je demander une permission supplémentaire temporaire ?

Oui. L'administrateur peut accorder une permission additionnelle à
votre compte (par exemple, pour un remplacement ponctuel). Faites la
demande par écrit (email à l'administrateur en copie votre chef de
service) en précisant la permission, la durée et le motif.
L'attribution est tracée dans l'audit log.

### Q17. Pourquoi le SUPER_ADMIN voit-il tous les établissements ?

Le SUPER_ADMIN est réservé à l'équipe projet et au pilotage national
(Ministère de la Santé). Il voit les données agrégées de tous les
établissements pour produire les rapports nationaux et intervenir en
cas d'incident critique. Les accès individuels aux DPI patients sont
tracés et font l'objet d'une revue mensuelle.

---

## Performance et disponibilité

### Q18. L'application est lente. Est-ce normal ?

La performance dépend de la charge serveur et de votre connexion
réseau. En heures de pointe (8h-10h), des ralentissements sont
possibles. Si la lenteur persiste hors pointe :
1. Rafraîchissez la page (F5).
2. Videz le cache du navigateur (Ctrl+Shift+R).
3. Si toujours lent, envoyez un feedback de type bug en précisant
   l'heure, la page concernée et l'action tentée.

L'équipe projet surveille les performances via Prometheus et ajuste
les ressources si nécessaire.

### Q19. L'application est inaccessible. Que faire ?

Vérifiez d'abord :
1. Que vous êtes sur **https://** chu-donka.guineecare.gn (le `s` est
   obligatoire).
2. Que le poste est connecté au réseau interne.
3. Que vous pouvez ouvrir d'autres sites internes.

Si l'application reste inaccessible, c'est probablement un incident
serveur. Prévenez la hotline niveau 1 (numéro affiché en salle de
pause). En attendant la résolution, utilisez la procédure papier de
secours (cahier d'admission, fiches de constantes papier) fournie
dans chaque service.

### Q20. Le système peut-il fonctionner hors-ligne (en cas de coupure réseau) ?

La version v1.1.0 ne fonctionne pas hors-ligne : toute action nécessite
une connexion au serveur. Un mode hors-ligne est prévu en v1.3 pour
les modules critiques (admissions, constantes, ordonnances) — les
données seront stockées localement et synchronisées au retour du
réseau.

---

## Sécurité et confidentialité

### Q21. Qui peut voir mon activité dans l'application ?

Toutes vos actions sont enregistrées dans le **journal d'audit**.
L'accès à ce journal est restreint :

- Vous pouvez consulter votre propre activité (menu **Mon profil →
  Mon activité**).
- Les ADMIN de votre établissement peuvent consulter l'activité des
  utilisateurs de leur établissement.
- Le SUPER_ADMIN peut consulter toute l'activité.
- Les autres utilisateurs n'ont pas accès à votre activité
  individuelle.

L'audit log sert à la sécurité (détection d'usage abusif), à la
qualité (analyse des erreurs de saisie) et à la conformité
réglementaire (preuve de traçabilité).

### Q22. Que faire si je soupçonne une utilisation abusive de mon compte ?

Changez immédiatement votre mot de passe (menu **Mon profil → Changer
le mot de passe**). Si vous ne pouvez pas (parce que vous n'avez plus
accès), demandez à l'administrateur de verrouiller votre compte.
Signalez l'incident par email à l'administrateur en précisant les
heures auxquelles vous n'étiez pas connecté. L'audit log permettra
d'identifier les actions effectuées sous votre nom pendant cette
période.

### Q23. Les données médicales sont-elles chiffrées ?

Oui, à plusieurs niveaux :

- **En transit** : la connexion entre votre navigateur et le serveur
  est chiffrée en TLS 1.2 ou 1.3 (HTTPS obligatoire).
- **En base** : les mots de passe sont hachés avec bcrypt (jamais
  stockés en clair). Les autres données sont en clair dans la base,
  mais l'accès à la base est restreint à l'administrateur système et
  chiffré au niveau du disque (LUKS).
- **Sauvegardes** : les backups quotidiens sont chiffrés et stockés
  hors site.

### Q24. Combien de temps les données sont-elles conservées ?

Les données médicales sont conservées **20 ans** conformément à la
réglementation guinéenne sur les archives médicales (à parité avec la
convention OHADA). Les données d'audit sont conservées 5 ans. Les
tokens JWT révoqués (déconnexion) sont conservés jusqu'à leur date
d'expiration naturelle (60 minutes maximum), puis supprimés
automatiquement.

---

## Boucle feedback (v1.1.0)

### Q25. Comment savoir si mon feedback a été traité ?

Quand un administrateur traite votre retour, vous recevez une
notification dans l'application (icône cloche). La notification
contient le statut (résolu, wontfix, triagé) et le message de
réponse. Vous pouvez aussi consulter l'historique de vos feedbacks
via **Mon profil → Mes retours**.

### Q26. Mon feedback a été classé « wontfix ». Pourquoi ?

Le statut « wontfix » est utilisé quand la demande ne rentre pas dans
le périmètre du projet ou entre en conflit avec d'autres choix
d'architecture. Le message de réponse de l'administrateur doit vous
expliquer la raison. Vous pouvez répondre (en soumettant un nouveau
feedback de type « question ») si vous souhaitez approfondir.

### Q27. Puis-je voir les feedbacks des autres utilisateurs ?

Non. Les feedbacks des autres utilisateurs ne sont visibles que par
eux-mêmes et par les administrateurs (ADMIN de l'établissement +
SUPER_ADMIN). Cette confidentialité encourage la sincérité des
retours. Les éléments d'intérêt général tirés des feedbacks sont
partagés dans les notes de mise à jour mensuelles.

---

## Pour aller plus loin

- [`quickstart-utilisateur.md`](quickstart-utilisateur.md) — prise en
  main en 10 minutes.
- [`parcours-recette-par-role.md`](parcours-recette-par-role.md) —
  liste des actions critiques par rôle.
- [`fiches-rapides/`](fiches-rapides/) — fiches A4 par rôle à imprimer.
- [`conduite-du-changement.md`](conduite-du-changement.md) — dispositif
  complet de formation et d'accompagnement.

# GuinéeCare Hospital Suite — Dossier de présentation

## À l'attention de Monsieur le Ministre de la Santé de la République de Guinée

**Date** : Juin 2026
**Version** : 1.7.1
**Statut** : Prêt pour pilote CHU Donka

---

## 1. Vision

La Guinée dispose aujourd'hui d'un système de santé encore largement
papier. Les dossiers patients se perdent, les statistiques sont
approximatives, la facturation est opaque, et le Ministère n'a pas de
visibilité temps réel sur l'activité des établissements.

**GuinéeCare** est une plateforme hospitalière numérique complète,
conçue pour le contexte guinéen, qui remplace le papier par un système
informatisé moderne. Elle couvre tout le parcours de soins : de
l'admission du patient à la facturation, en passant par les urgences,
le laboratoire, l'imagerie, la pharmacie, et le bloc opératoire.

---

## 2. Bénéfices attendus

### Pour le patient
- **Dossier médical unique** : son historique est consultable dans
  tous les établissements de la République.
- **Réduction des erreurs** : allergies et antécédents visibles à
  chaque consultation.
- **Facturation transparente** : reçu détaillé pour chaque acte.

### Pour le soignant
- **Gain de temps** : fini la recherche de dossiers papier.
- **Sécurité** : alertes automatiques sur résultats labo critiques.
- **Mobilité** : application mobile pour les gardes (scan QR patient).

### Pour le directeur d'établissement
- **Pilotage temps réel** : occupation des lits, file d'urgences,
  recettes du jour.
- **Qualité** : 10 indicateurs OMS/HAS suivis automatiquement avec
  alertes de dépassement de seuils.
- **Traçabilité** : audit log de chaque action (qui, quand, quoi).

### Pour le Ministère
- **Visibilité nationale** : agrégats multi-établissements en temps
  réel.
- **Reporting automatisé** : plus de saisie manuelle de statistiques.
- **Interopérabilité** : standard international HL7 FHIR R4 pour
  échanger avec les laboratoires externes et autres SIH.
- **Souveraineté** : code propriétaire guinéen, hébergé en Guinée.

---

## 3. Modules fonctionnels

| Module | Description | Statut |
|--------|-------------|--------|
| **Dossier Patient** | DPI complet, recherche, création, champs médicaux | ✅ Opérationnel |
| **Admissions** | Admissions programmées et urgentes | ✅ Opérationnel |
| **Urgences** | File d'attente, triage 5 niveaux, orientation | ✅ Opérationnel |
| **Hospitalisation** | Lits, séjours, bed-board par établissement | ✅ Opérationnel |
| **Maternité** | Grossesses, accouchements, CPoN | ✅ Opérationnel |
| **Laboratoire** | Demandes, résultats, validation, alertes critiques | ✅ Opérationnel |
| **Imagerie** | Demandes, comptes rendus, PDF | ✅ Opérationnel |
| **Bloc opératoire** | Programmation, comptes rendus opératoires | ✅ Opérationnel |
| **Pharmacie** | Stock, dispensation, mouvements | ✅ Opérationnel |
| **Facturation** | Factures, paiements, reçus PDF | ✅ Opérationnel |
| **RH v2** | Plannings, gardes, congés, astreintes, remplacements | ✅ Opérationnel |
| **Qualité** | 10 indicateurs OMS/HAS, seuils, alertes automatiques | ✅ Opérationnel |
| **Reporting national** | Agrégats multi-établissements, alertes épidémiques | ✅ Opérationnel |
| **Notifications SMS** | Intégration Orange/MTN/Moov (pré-requis credentials) | ⏳ Code prêt |
| **App mobile Android** | Scan QR, biométrie, offline, notifications push | ⏳ Code prêt |
| **Interopérabilité FHIR** | Patient, Encounter, Observation, MedicationRequest | ✅ Opérationnel |
| **Bilinguisme FR/EN** | Interface traduisible en un clic | ✅ Opérationnel |

---

## 4. Architecture technique

```
┌─────────────────────────────────────────────┐
│              Utilisateurs                    │
│  Navigateur Web   │   App Mobile Android     │
└────────┬──────────┴──────────┬───────────────┘
         │                     │
         ▼                     ▼
┌─────────────────────────────────────────────┐
│           Nginx (HTTPS, reverse proxy)       │
└────────────────────┬────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌─────────────────┐    ┌──────────────────────┐
│  Frontend React │    │  Backend FastAPI      │
│  (Vite + TS)    │    │  (Python 3.12)        │
│                 │    │  30+ modules REST     │
│  25+ pages      │    │  JWT + RBAC + RLS     │
│  WebSocket live │    │  WebSocket temps réel │
│  PWA offline    │    │  FHIR R4              │
└─────────────────┘    └──────────┬───────────┘
                                  │
                       ┌──────────┴───────────┐
                       ▼                      ▼
              ┌────────────────┐    ┌────────────────┐
              │  PostgreSQL 16 │    │  Redis 7       │
              │  (multi-tenant)│    │  (cache + WS)  │
              └────────────────┘    └────────────────┘
```

**Stack** : FastAPI, React 18, PostgreSQL, Redis, Docker, Python 3.12,
TypeScript, SQLAlchemy 2.0, Alembic, Tailwind CSS.

**Sécurité** : Authentification JWT, 8 rôles RBAC, isolation
multi-tenant par établissement (Row-Level Security), audit log
de chaque action, rate limiting, chiffrement des credentials SMS.

---

## 5. Différenciation vs SIH commerciaux

| Critère | SIH commercial (ex: Hopital Manager) | GuinéeCare |
|---------|---------------------------------------|------------|
| **Coût licences** | 50-100M GNF/an | 0 (code propriétaire guinéen) |
| **Hébergement** | Serveur en Europe | Serveur en Guinée |
| **Adaptation locale** | Générique, non adapté | Conçu pour le contexte guinéen |
| **Multi-établissements** | Supplément payant | Inclus (20 établissements pré-configurés) |
| **Bilinguisme FR/EN** | Rare | Inclus |
| **SMS opérateurs locaux** | Non | Orange/MTN/Moov intégrés |
| **Indicateurs OMS/HAS** | Non | 10 indicateurs pré-configurés |
| **Interopérabilité FHIR** | Option payante | Inclus |
| **Support** | Hotline internationale | Équipe locale, formation sur site |
| **Évolution** | Selon l'éditeur | Selon les besoins du Ministère |

---

## 6. Plan de déploiement

### Phase 1 — Pilote CHU Donka (2 mois)

| Mois | Action |
|------|--------|
| M1 S1 | Déploiement serveur + migration données papier |
| M1 S2 | Formation 20 agents (médecins, infirmiers, admin) |
| M1 S3-S4 | Utilisation parallèle papier + numérique |
| M2 S1-S2 | Abandon progressif du papier |
| M2 S3-S4 | Évaluation, ajustements, recueil de feedback |

**Budget pilote** : ~15 millions GNF (serveur + formation + support)

### Phase 2 — Déploiement régional (6 mois)

- 8 HGR (Hôpitaux Régionaux) : Kindia, Boké, Mamou, Labé, Kankan,
  N'Zérékoré, Faranah + 1 CSI pilote par région
- 2 établissements par mois = 8 mois pour la couverture régionale
- Formation décentralisée (formateurs formés au CHU Donka)

**Budget régional** : ~50 millions GNF

### Phase 3 — Couverture nationale (12 mois)

- 20 CSI de Conakry + cliniques privées agréées
- Data warehouse national pour le Ministère
- Télémédecine pour les zones rurales

**Budget national** : ~100 millions GNF

---

## 7. Indicateurs de succès du pilote

| Indicateur | Cible 6 mois | Mesure |
|------------|-------------|--------|
| Dossiers patients numérisés | ≥ 5 000 | Compteur DPI |
| Admissions saisies dans le système | ≥ 80% des admissions | % vs total |
| Temps moyen d'admission | < 5 min | Horodatage |
| Résultats labo saisis électroniquement | ≥ 90% | % vs total |
| Factures électroniques | ≥ 95% | % vs total |
| Satisfaction soignants | ≥ 7/10 | Enquête |
| Disponibilité système | ≥ 99% | Monitoring |

---

## 8. Évolutions futures (v2.0+)

| Évolution | Bénéfice | Délai |
|-----------|----------|-------|
| **Data warehouse national** | Requêtes ad hoc pour le Ministère | 6 mois |
| **Télémédecine** | Désenclavement des zones rurales | 8 mois |
| **IA aide au diagnostic** | Détection TB sur radio thorax | 10 mois |
| **Multi-entrepôts pharmacie** | Traçabilité GS1, péremptions | 4 mois |
| **Migration Kubernetes** | Haute disponibilité, blue-green | 6 mois |

---

## 9. Demande au Ministère

1. **Lettre d'engagement** pour le pilote CHU Donka (2 mois)
2. **Désignation d'un référent** au Ministère pour le suivi
3. **Autorisation** de contacter Orange/MTN/Moov pour les credentials SMS
4. **Budget pilote** : 15 millions GNF (serveur + formation + support)
5. **Accès** aux statistiques actuelles du CHU Donka pour comparaison

---

## Contact

**Équipe technique GuinéeCare**
Email : tech@guineecare.gn
Dépôt : github.com/skaba89/guineecare-hospital-suite

---

*Ce dossier a été préparé pour la présentation au Ministre de la Santé
de la République de Guinée. La plateforme GuinéeCare est prête pour
le pilote au CHU Donka.*

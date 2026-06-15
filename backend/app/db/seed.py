"""
Comprehensive seed data for GuinéeCare Hospital Suite.
Realistic data modelled after Guinea's healthcare system with:
- Multiple facilities (CHU, HGR, CSI, clinics, pharmacies) across all regions
- Staff with Guinean names and real specialties
- Patients with full demographics, national IDs, insurance
- End-to-end clinical workflows (admission → consultation → lab → imaging → surgery → billing)
- Emergency visits with triage and orientation
- Maternity records (prenatal, delivery, postnatal)
- Pharmacy stock with movements
- Quality indicators and incident reports
- National reporting data
"""

import json
from datetime import datetime, timedelta
from random import choice, randint, seed as rseed

from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.modules.activity.models import ActivityEntry
from app.modules.admissions.models import Admission
from app.modules.billing.models import Invoice, Payment, TariffItem
from app.modules.clinical.models import ClinicalNote, Diagnosis, PatientMeasurement
from app.modules.departments.models import Department
from app.modules.emergency.models import EmergencyVisit
from app.modules.facilities.models import Facility
from app.modules.hospitalization.models import Bed, HospitalStay, Room
from app.modules.imaging.models import ImagingOrder, ImagingResult
from app.modules.laboratory.models import LabOrder, LabResult, LabTest
from app.modules.maternity.models import (
    DeliveryRecord,
    MaternityConsultation,
    MaternityRecord,
)
from app.modules.patients.models import Patient
from app.modules.personnel.models import OnCallSchedule, StaffMember
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock, StockMovement
from app.modules.quality.models import IncidentReport, QualityIndicator, QualityMeasurement
from app.modules.reporting.models import EpidemicAlert, HealthStatistic, NationalReport
from app.modules.surgery.models import (
    OperatingRoom,
    SurgeryReport,
    SurgerySchedule,
    SurgeryTeamMember,
)
from app.modules.users.models import User

# Deterministic random
rseed(42)

# ─────────────────────────────────────────────
# Reference data
# ─────────────────────────────────────────────

FACILITIES_DATA = [
    # (code, name, category, region, prefecture)
    ("CHU-DONKA", "CHU Donka", "CHU", "Conakry", "Conakry"),
    ("CHU-IGNACE-DEEN", "CHU Ignace Deen", "CHU", "Conakry", "Conakry"),
    ("CHU-ANGRE", "CHU de l'Institut Cardiologique d'Almamy Samory Touré", "CHU", "Conakry", "Conakry"),
    ("HGR-KINDIA", "HGR de Kindia", "HGR", "Kindia", "Kindia"),
    ("HGR-BOKE", "HGR de Boké", "HGR", "Boké", "Boké"),
    ("HGR-MAMOU", "HGR de Mamou", "HGR", "Mamou", "Mamou"),
    ("HGR-LABE", "HGR de Labé", "HGR", "Labé", "Labé"),
    ("HGR-KANKAN", "HGR de Kankan", "HGR", "Kankan", "Kankan"),
    ("HGR-NZEREKORE", "HGR de N'Zérékoré", "HGR", "N'Zérékoré", "N'Zérékoré"),
    ("HGR-FARANAH", "HGR de Faranah", "HGR", "Faranah", "Faranah"),
    ("CSI-MATAM", "CSI de Matam", "CSI", "Conakry", "Conakry"),
    ("CSI-RATOMA", "CSI de Ratoma", "CSI", "Conakry", "Ratoma"),
    ("CSI-DIXINN", "CSI de Dixinn", "CSI", "Conakry", "Dixinn"),
    ("CSI-KALOUM", "CSI de Kaloum", "CSI", "Conakry", "Kaloum"),
    ("CLINIQUE-PASTEUR", "Clinique Pasteur", "PRIVE", "Conakry", "Conakry"),
    ("CLINIQUE-ESPERANCE", "Clinique l'Espérance", "PRIVE", "Conakry", "Conakry"),
    ("PHARMA-CENTRALE", "Pharmacie Centrale de Guinée", "PHARMACIE", "Conakry", "Conakry"),
    ("PHARMA-KIPPE", "Pharmacie du Kippé", "PHARMACIE", "Conakry", "Conakry"),
    ("PHARMA-KINDIA", "Pharmacie de Kindia", "PHARMACIE", "Kindia", "Kindia"),
    ("PHARMA-KANKAN", "Pharmacie de Kankan", "PHARMACIE", "Kankan", "Kankan"),
]

DEPARTMENTS_DATA = {
    "CHU": [
        ("URG", "Urgences", "CLINICAL"),
        ("MED", "Médecine interne", "CLINICAL"),
        ("CHIR", "Chirurgie générale", "CLINICAL"),
        ("MAT", "Maternité", "CLINICAL"),
        ("PED", "Pédiatrie", "CLINICAL"),
        ("CARD", "Cardiologie", "CLINICAL"),
        ("NEPH", "Néphrologie", "CLINICAL"),
        ("NEURO", "Neurologie", "CLINICAL"),
        ("ORL", "ORL", "CLINICAL"),
        ("OPHT", "Ophtalmologie", "CLINICAL"),
        ("DERM", "Dermatologie", "CLINICAL"),
        ("PNEUM", "Pneumologie", "CLINICAL"),
        ("GASTRO", "Gastro-entérologie", "CLINICAL"),
        ("REANIM", "Réanimation", "CLINICAL"),
        ("LAB", "Laboratoire", "TECHNICAL"),
        ("IMAGERIE", "Imagerie médicale", "TECHNICAL"),
        ("BLOC", "Bloc opératoire", "TECHNICAL"),
        ("PHA", "Pharmacie", "SUPPORT"),
        ("CAI", "Caisse / Facturation", "ADMIN"),
        ("ADM", "Administration", "ADMIN"),
        ("QUAL", "Qualité", "ADMIN"),
    ],
    "HGR": [
        ("URG", "Urgences", "CLINICAL"),
        ("MED", "Médecine générale", "CLINICAL"),
        ("CHIR", "Chirurgie", "CLINICAL"),
        ("MAT", "Maternité", "CLINICAL"),
        ("PED", "Pédiatrie", "CLINICAL"),
        ("LAB", "Laboratoire", "TECHNICAL"),
        ("IMAGERIE", "Imagerie", "TECHNICAL"),
        ("PHA", "Pharmacie", "SUPPORT"),
        ("CAI", "Caisse", "ADMIN"),
        ("ADM", "Administration", "ADMIN"),
    ],
    "CSI": [
        ("MED", "Consultations", "CLINICAL"),
        ("MAT", "Maternité", "CLINICAL"),
        ("LAB", "Laboratoire", "TECHNICAL"),
        ("PHA", "Pharmacie", "SUPPORT"),
        ("CAI", "Caisse", "ADMIN"),
    ],
    "PRIVE": [
        ("MED", "Consultations", "CLINICAL"),
        ("CHIR", "Chirurgie", "CLINICAL"),
        ("MAT", "Maternité", "CLINICAL"),
        ("LAB", "Laboratoire", "TECHNICAL"),
        ("IMAGERIE", "Imagerie", "TECHNICAL"),
        ("BLOC", "Bloc opératoire", "TECHNICAL"),
        ("PHA", "Pharmacie", "SUPPORT"),
        ("CAI", "Caisse", "ADMIN"),
    ],
    "PHARMACIE": [
        ("DISP", "Dispensation", "SUPPORT"),
        ("STOCK", "Gestion stock", "SUPPORT"),
        ("CAI", "Caisse", "ADMIN"),
    ],
}

USERS_DATA = [
    # (email, first_name, last_name, role, facility_code)
    ("admin@guineecare.com", "Admin", "GuinéeCare", "SUPER_ADMIN", "CHU-DONKA"),
    ("dr.diallo@chu-donka.gn", "Amadou", "Diallo", "DOCTOR", "CHU-DONKA"),
    ("dr.bah@chu-donka.gn", "Mamadou", "Bah", "DOCTOR", "CHU-DONKA"),
    ("dr.sow@chu-donka.gn", "Aïssatou", "Sow", "DOCTOR", "CHU-DONKA"),
    ("dr.keita@chu-donka.gn", "Ibrahima", "Keita", "DOCTOR", "CHU-DONKA"),
    ("dr.toure@chu-donka.gn", "Mariame", "Touré", "DOCTOR", "CHU-DONKA"),
    ("dr.conde@chu-donka.gn", "Alpha", "Condé", "DOCTOR", "CHU-DONKA"),
    ("dr.coulibaly@chu-ignace.gn", "Fatoumata", "Coulibaly", "DOCTOR", "CHU-IGNACE-DEEN"),
    ("dr.camara@chu-ignace.gn", "Sekou", "Camara", "DOCTOR", "CHU-IGNACE-DEEN"),
    ("dr.diallo2@chu-ignace.gn", "Ousmane", "Diallo", "DOCTOR", "CHU-IGNACE-DEEN"),
    ("dr.sylla@hgr-kindia.gn", "Kadiatou", "Sylla", "DOCTOR", "HGR-KINDIA"),
    ("dr.kaba@hgr-kindia.gn", "Mamadou", "Kaba", "DOCTOR", "HGR-KINDIA"),
    ("dr.barry@hgr-labe.gn", "Thierno", "Barry", "DOCTOR", "HGR-LABE"),
    ("dr.diallo3@hgr-kankan.gn", "Lounceny", "Diallo", "DOCTOR", "HGR-KANKAN"),
    ("dr.gbou@hgr-nzerekore.gn", "Gbou", "Loua", "DOCTOR", "HGR-NZEREKORE"),
    ("sf.bangoura@chu-donka.gn", "Marie", "Bangoura", "MIDWIFE", "CHU-DONKA"),
    ("sf.doumbouya@chu-donka.gn", "Aminata", "Doumbouya", "MIDWIFE", "CHU-DONKA"),
    ("sf.cisse@chu-ignace.gn", "Fatoumata", "Cissé", "MIDWIFE", "CHU-IGNACE-DEEN"),
    ("sf.baldé@hgr-kindia.gn", "Hawa", "Baldé", "MIDWIFE", "HGR-KINDIA"),
    ("inf.konde@chu-donka.gn", "Joseph", "Kondé", "NURSE", "CHU-DONKA"),
    ("inf.sano@chu-donka.gn", "Augustin", "Sano", "NURSE", "CHU-DONKA"),
    ("inf.fofana@chu-donka.gn", "M'mah", "Fofana", "NURSE", "CHU-DONKA"),
    ("inf.doum@chu-ignace.gn", "Saa", "Doumbouya", "NURSE", "CHU-IGNACE-DEEN"),
    ("inf.leno@hgr-kindia.gn", "Pierre", "Léno", "NURSE", "HGR-KINDIA"),
    ("pharma.dubois@chu-donka.gn", "Jean", "Dubois", "PHARMACIST", "CHU-DONKA"),
    ("pharma.kante@chu-ignace.gn", "Koumba", "Kanté", "PHARMACIST", "CHU-IGNACE-DEEN"),
    ("pharma.dore@pharma-centrale.gn", "Mamadou", "Doré", "PHARMACIST", "PHARMA-CENTRALE"),
    ("lab.sakouv@chu-donka.gn", "Céline", "Sakouvogui", "LAB_TECH", "CHU-DONKA"),
    ("lab.kom@chu-ignace.gn", "Thierno", "Kom", "LAB_TECH", "CHU-IGNACE-DEEN"),
    ("caisse.koli@chu-donka.gn", "Aïcha", "Koli", "CASHIER", "CHU-DONKA"),
    ("caisse.tamba@chu-ignace.gn", "Mamadou", "Tamba", "CASHIER", "CHU-IGNACE-DEEN"),
    ("admin.donka@chu-donka.gn", "Ibrahima", "Kalil", "ADMIN", "CHU-DONKA"),
    ("admin.ignace@chu-ignace.gn", "Fatou", "Bantama", "ADMIN", "CHU-IGNACE-DEEN"),
    ("dr.traore@clinique-pasteur.gn", "Boubacar", "Traoré", "DOCTOR", "CLINIQUE-PASTEUR"),
    ("dr.ndiaye@clinique-esperance.gn", "Moussa", "Ndiaye", "DOCTOR", "CLINIQUE-ESPERANCE"),
    ("dr.yansane@hgr-boke.gn", "Fodé", "Yansané", "DOCTOR", "HGR-BOKE"),
    ("dr.dem@hgr-mamou.gn", "Samba", "Dem", "DOCTOR", "HGR-MAMOU"),
    ("dr.sagna@hgr-faranah.gn", "Boubacar", "Sagna", "DOCTOR", "HGR-FARANAH"),
]

# Guinean patient names
PATIENT_FIRST_NAMES_M = [
    "Mamadou", "Ibrahima", "Alpha", "Ousmane", "Sekou", "Moussa", "Lounceny",
    "Thierno", "Boubacar", "Fodé", "Amadou", "Abdoulaye", "Samba", "Djibril",
    "Mamady", "Kerfalla", "Mory", "Youssouf", "Abdou", "Elhadj", "Malal",
    "Tamba", "Momo", "Almamy", "Khalil", "Boubacar", "Souleymane", "Ibrahim",
]
PATIENT_FIRST_NAMES_F = [
    "Aïssatou", "Fatoumata", "Mariame", "Kadiatou", "Hawa", "M'mah", "Aminata",
    "Fatou", "Djenabou", "Koumba", "Mariama", "Safiatou", "Nabintou", "Sira",
    "Aïcha", "Djénéba", "Bintou", "Fanta", "Youssouf", "Assétou", "Awa",
    "Bineta", "Oumou", "Ramata", "Adama", "Satigui", "Djénéba", "Fanta",
]
PATIENT_LAST_NAMES = [
    "Camara", "Diallo", "Bah", "Sow", "Keita", "Touré", "Condé", "Coulibaly",
    "Sylla", "Kaba", "Barry", "Doumbouya", "Bangoura", "Cissé", "Fofana",
    "Kanté", "Baldé", "Traoré", "Ndiaye", "Yansané", "Sakouvogui", "Doum",
    "Tamba", "Koli", "Léno", "Sano", "Kondé", "Doré", "Dem", "Sagna",
    "Gbou", "Loua", "Kom", "Bantama", "Kalil", "Doubiya", "Koïta", "Souaré",
    "Dioubaté", "Sanoh", "Kourouma", "Loupé", "Bérété", "Chérif", "Diakité",
    "Fané", "Gassama", "Haba", "Indjai",
]

REGIONS = ["Conakry", "Kindia", "Boké", "Mamou", "Labé", "Kankan", "N'Zérékoré", "Faranah"]
PREFECTURES_CONAKRY = ["Kaloum", "Dixinn", "Ratoma", "Matam"]

# Common diagnoses in Guinea (CIM-10 codes)
COMMON_DIAGNOSES = [
    ("A00.0", "Choléra", "PRINCIPAL"),
    ("A01.0", "Fièvre typhoïde", "PRINCIPAL"),
    ("A06.0", "Amibiase", "PRINCIPAL"),
    ("B50.0", "Paludisme à Plasmodium falciparum", "PRINCIPAL"),
    ("B54", "Paludisme, sans précision", "PRINCIPAL"),
    ("J18.9", "Pneumonie", "PRINCIPAL"),
    ("J06.9", "Infection respiratoire aiguë", "PRINCIPAL"),
    ("K29.5", "Gastrite", "PRINCIPAL"),
    ("K35.0", "Appendicite aiguë", "PRINCIPAL"),
    ("N10", "Néphrite aiguë", "PRINCIPAL"),
    ("I10", "Hypertension artérielle", "PRINCIPAL"),
    ("E11.9", "Diabète type 2", "PRINCIPAL"),
    ("I21.9", "Infarctus du myocarde", "PRINCIPAL"),
    ("I63.9", "AVC", "PRINCIPAL"),
    ("J45.0", "Asthme", "PRINCIPAL"),
    ("L23.9", "Dermite de contact", "PRINCIPAL"),
    ("M54.5", "Lombalgie", "PRINCIPAL"),
    ("N20.0", "Calcul rénal", "PRINCIPAL"),
    ("O62.0", "Dystocie", "PRINCIPAL"),
    ("O46.0", "Hémorragie ante-partum", "PRINCIPAL"),
    ("O80.0", "Accouchement normal", "PRINCIPAL"),
    ("S72.0", "Fracture du col du fémur", "PRINCIPAL"),
    ("S82.8", "Fracture de la cheville", "PRINCIPAL"),
    ("S06.0", "Traumatisme crânien", "PRINCIPAL"),
    ("T78.2", "Choc anaphylactique", "PRINCIPAL"),
    ("A09", "Diarrhée aiguë", "PRINCIPAL"),
    ("B37.0", "Candidose", "SECONDARY"),
    ("E46", "Malnutrition", "SECONDARY"),
    ("Z23", "Vaccination", "SECONDARY"),
    ("J00", "Rhinite aiguë", "SECONDARY"),
]

PHARMACY_PRODUCTS_DATA = [
    # (code, name, category, form, dosage, quantity, min_threshold)
    ("PARA-500", "Paracétamol 500 mg", "ANTALGIQUE", "comprimé", "500 mg", 5000, 500),
    ("PARA-SIRO", "Paracétamol sirop 125 mg/5ml", "ANTALGIQUE", "sirop", "125 mg/5ml", 2000, 200),
    ("IBU-400", "Ibuprofène 400 mg", "ANTI-INFLAMMATOIRE", "comprimé", "400 mg", 3000, 300),
    ("AMOX-500", "Amoxicilline 500 mg", "ANTIBIOTIQUE", "gélule", "500 mg", 4000, 400),
    ("AMOX-SUSP", "Amoxicilline suspension 125 mg/5ml", "ANTIBIOTIQUE", "suspension", "125 mg/5ml", 1500, 150),
    ("COTRIM", "Cotrimoxazole 480 mg", "ANTIBIOTIQUE", "comprimé", "480 mg", 3000, 300),
    ("METRO-500", "Métronidazole 500 mg", "ANTIBIOTIQUE", "comprimé", "500 mg", 2000, 200),
    ("CIPRO-500", "Ciprofloxacine 500 mg", "ANTIBIOTIQUE", "comprimé", "500 mg", 1500, 150),
    ("AZITHRO-500", "Azithromycine 500 mg", "ANTIBIOTIQUE", "comprimé", "500 mg", 1000, 100),
    ("DOXY-100", "Doxycycline 100 mg", "ANTIBIOTIQUE", "gélule", "100 mg", 2000, 200),
    ("QUININE-500", "Quinine 500 mg", "ANTIPALUDÉEN", "comprimé", "500 mg", 5000, 500),
    ("ARTHESUN", "Artésunate 50 mg", "ANTIPALUDÉEN", "comprimé", "50 mg", 3000, 300),
    ("COARTEM", "Coartem (Artéméther+Luméfantrine)", "ANTIPALUDÉEN", "comprimé", "20/120 mg", 4000, 400),
    ("ORS", "Sels de réhydratation orale", "RÉHYDRATATION", "sachet", "20.5g/L", 8000, 800),
    ("METO-5", "Metoclopramide 5 mg/ml", "ANTIÉMÉTIQUE", "ampoule", "5 mg/ml", 1000, 100),
    ("OMEPRA-20", "Oméprazole 20 mg", "ANTIULCÉREUX", "gélule", "20 mg", 2000, 200),
    ("DICLO-50", "Diclofenac 50 mg", "ANTI-INFLAMMATOIRE", "comprimé", "50 mg", 2000, 200),
    ("MORPH-10", "Morphine 10 mg/ml", "ANTALGIQUE", "ampoule", "10 mg/ml", 200, 20),
    ("DIAZ-10", "Diazépam 10 mg", "ANXIOLYTIQUE", "comprimé", "10 mg", 500, 50),
    ("PHENOBAR", "Phénobarbital 100 mg", "ANTICONVULSANT", "comprimé", "100 mg", 300, 30),
    ("INSULIN-100", "Insuline 100 UI/ml", "ANTIDIABÉTIQUE", "flacon", "100 UI/ml", 200, 20),
    ("METFORM-500", "Metformine 500 mg", "ANTIDIABÉTIQUE", "comprimé", "500 mg", 2000, 200),
    ("AMLO-5", "Amlodipine 5 mg", "ANTIHYPERTENSEUR", "comprimé", "5 mg", 1500, 150),
    ("CAPTOPRIL-25", "Captopril 25 mg", "ANTIHYPERTENSEUR", "comprimé", "25 mg", 1000, 100),
    ("FURO-40", "Furosémide 40 mg", "DIURÉTIQUE", "comprimé", "40 mg", 800, 80),
    ("DIGOX-025", "Digoxine 0.25 mg", "CARDIAQUE", "comprimé", "0.25 mg", 200, 20),
    ("SALB-2", "Salbutamol 2 mg", "BRONCHODILATATEUR", "sirop", "2 mg/5ml", 500, 50),
    ("PRED-5", "Prednisone 5 mg", "CORTICOÏDE", "comprimé", "5 mg", 1000, 100),
    ("HYDRO-5", "Hydrocortisone 5 mg", "CORTICOÏDE", "crème", "5 mg/g", 500, 50),
    ("FER-200", "Sulfate de fer 200 mg", "ANTIANÉMIQUE", "comprimé", "200 mg", 3000, 300),
    ("FOLIC-5", "Acide folique 5 mg", "ANTIANÉMIQUE", "comprimé", "5 mg", 2000, 200),
    ("VITA-100000", "Vitamine A 100 000 UI", "VITAMINE", "gélule", "100 000 UI", 2000, 200),
    ("BENZ-PEN", "Benzylpénicilline 1 MUI", "ANTIBIOTIQUE", "flacon", "1 MUI", 500, 50),
    ("GENTA-80", "Gentamicine 80 mg/2ml", "ANTIBIOTIQUE", "ampoule", "80 mg/2ml", 400, 40),
    ("LIDO-2", "Lidocaïne 2%", "ANESTHÉSIQUE", "flacon", "2%", 300, 30),
    ("KETAM-50", "Kétamine 50 mg/ml", "ANESTHÉSIQUE", "flacon", "50 mg/ml", 100, 10),
    ("OXY-10", "Ocytocine 10 UI/ml", "UTÉROTONIQUE", "ampoule", "10 UI/ml", 500, 50),
    ("MISOP-200", "Misoprostol 200 µg", "UTÉROTONIQUE", "comprimé", "200 µg", 300, 30),
    ("ERGY-MAG", "Sulfate de magnésium 50%", "ANTICONVULSANT", "ampoule", "50%", 200, 20),
    ("RINGER-500", "Ringer Lactate 500 ml", "PERFUSION", "poche", "500 ml", 1000, 100),
    ("NACL-500", "Sérum physiologique 0.9% 500 ml", "PERFUSION", "poche", "500 ml", 1500, 150),
    ("GLUC5-500", "Glucose 5% 500 ml", "PERFUSION", "poche", "500 ml", 1000, 100),
    ("GLUC10-500", "Glucose 10% 500 ml", "PERFUSION", "poche", "500 ml", 500, 50),
    ("GLUC30-500", "Glucose 30% 500 ml", "PERFUSION", "poche", "500 ml", 100, 10),
]

LAB_TESTS_DATA = [
    # (code, name, category, sample_type)
    ("NFS", "Numération formule sanguine", "HÉMATOLOGIE", "sang"),
    ("HGB", "Hémoglobine", "HÉMATOLOGIE", "sang"),
    ("HCT", "Hématocrite", "HÉMATOLOGIE", "sang"),
    ("PLQ", "Plaquettes", "HÉMATOLOGIE", "sang"),
    ("GLY", "Glycémie", "BIOCHIMIE", "sang"),
    ("UREE", "Urée", "BIOCHIMIE", "sang"),
    ("CREAT", "Créatinine", "BIOCHIMIE", "sang"),
    ("ALAT", "ALAT (SGPT)", "BIOCHIMIE", "sang"),
    ("ASAT", "ASAT (SGOT)", "BIOCHIMIE", "sang"),
    ("BILIT", "Bilirubine totale", "BIOCHIMIE", "sang"),
    ("BILID", "Bilirubine directe", "BIOCHIMIE", "sang"),
    ("TP", "Taux de prothrombine", "HÉMOSTASE", "sang"),
    ("TCA", "TCA", "HÉMOSTASE", "sang"),
    ("GE", "Goutte épaisse", "PARASITOLOGIE", "sang"),
    ("TDR-PALU", "TDR Paludisme", "PARASITOLOGIE", "sang"),
    ("CRP", "CRP", "BIOCHIMIE", "sang"),
    ("VS", "Vitesse de sédimentation", "HÉMATOLOGIE", "sang"),
    ("GROUP", "Groupe sanguin", "HÉMATOLOGIE", "sang"),
    ("RHSUS", "Rhésus", "HÉMATOLOGIE", "sang"),
    ("Urinaire", "Examen cytobactériologique des urines", "BACTÉRIOLOGIE", "urine"),
    ("ECBU", "ECBU", "BACTÉRIOLOGIE", "urine"),
    ("SELLES", "Coproculture", "BACTÉRIOLOGIE", "selles"),
    ("HIV", "Sérologie VIH", "SÉROLOGIE", "sang"),
    ("HBV", "Sérologie Hépatite B", "SÉROLOGIE", "sang"),
    ("HCV", "Sérologie Hépatite C", "SÉROLOGIE", "sang"),
    ("VDRL", "VDRL (Syphilis)", "SÉROLOGIE", "sang"),
    ("WIDAL", "Widal (Fièvre typhoïde)", "SÉROLOGIE", "sang"),
    ("GS", "Gramme/6h", "BIOCHIMIE", "urine"),
    ("ALB", "Albumine", "BIOCHIMIE", "urine"),
    ("LACT", "Lactates", "BIOCHIMIE", "sang"),
    ("IONO", "Ionogramme (Na, K, Cl)", "BIOCHIMIE", "sang"),
    ("GAZ", "Gaz du sang", "BIOCHIMIE", "sang artériel"),
]

TARIFF_ITEMS_DATA = [
    # (code, name, category, unit_price GNF)
    ("CONS-GEN", "Consultation médecine générale", "CONSULTATION", 50000),
    ("CONS-SPEC", "Consultation spécialiste", "CONSULTATION", 75000),
    ("CONS-URG", "Consultation urgence", "URGENCE", 75000),
    ("VISITE", "Visite de suivi", "CONSULTATION", 25000),
    ("CERT-MED", "Certificat médical", "ADMINISTRATIF", 30000),
    ("ARRET-TRAV", "Arrêt de travail", "ADMINISTRATIF", 25000),
    ("LAB-NFS", "NFS", "LABORATOIRE", 35000),
    ("LAB-GLY", "Glycémie", "LABORATOIRE", 20000),
    ("LAB-CREAT", "Créatinine", "LABORATOIRE", 25000),
    ("LAB-UREE", "Urée", "LABORATOIRE", 20000),
    ("LAB-GE", "Goutte épaisse", "LABORATOIRE", 15000),
    ("LAB-TDR", "TDR Paludisme", "LABORATOIRE", 15000),
    ("LAB-ECBU", "ECBU", "LABORATOIRE", 25000),
    ("LAB-GROUP", "Groupe sanguin + Rhésus", "LABORATOIRE", 20000),
    ("LAB-SERO-HIV", "Sérologie VIH", "LABORATOIRE", 30000),
    ("LAB-SERO-HBV", "Sérologie Hépatite B", "LABORATOIRE", 30000),
    ("LAB-IONO", "Ionogramme", "LABORATOIRE", 40000),
    ("IMG-RX-THX", "Radiographie thorax", "IMAGERIE", 50000),
    ("IMG-RX-ABD", "Radiographie abdomen", "IMAGERIE", 50000),
    ("IMG-RX-OS", "Radiographie os", "IMAGERIE", 50000),
    ("IMG-ECHO", "Échographie", "IMAGERIE", 75000),
    ("IMG-SCANNER", "Scanner", "IMAGERIE", 500000),
    ("IMG-IRM", "IRM", "IMAGERIE", 800000),
    ("CHIR-APPEN", "Appendicectomie", "CHIRURGIE", 2000000),
    ("CHIR-HERNIE", "Cure de hernie", "CHIRURGIE", 1500000),
    ("CHIR-CESAR", "Césarienne", "CHIRURGIE", 2500000),
    ("CHIR-LAP", "Laparotomie", "CHIRURGIE", 3000000),
    ("CHIR-OSTEO", "Ostéosynthèse", "CHIRURGIE", 2500000),
    ("HOSP-JOUR", "Hospitalisation / jour", "HOSPITALISATION", 75000),
    ("HOSP-REANIM", "Réanimation / jour", "HOSPITALISATION", 200000),
    ("ACC-NORM", "Accouchement normal", "MATERNITÉ", 500000),
    ("ACC-CESAR", "Césarienne (forfait)", "MATERNITÉ", 2500000),
    ("CPN", "Consultation prénatale", "MATERNITÉ", 25000),
]

QUALITY_INDICATORS_DATA = [
    # (code, name, category, description, unit, target_value, frequency)
    ("IPS", "Indicateur de Performance et de Sécurité", "SAFETY", "Score global de performance et sécurité", "score", "≥80", "MONTHLY"),
    ("TMR24", "Taux de mortalité à 24h", "CLINICAL_OUTCOME", "Mortalité dans les 24h après admission", "%", "<2", "MONTHLY"),
    ("SAT_PAT", "Satisfaction patient", "PATIENT_EXPERIENCE", "Taux de satisfaction des patients", "%", "≥85", "QUARTERLY"),
    ("TAUX_OCC", "Taux d'occupation des lits", "EFFICIENCY", "Pourcentage d'occupation des lits", "%", "70-85", "MONTHLY"),
    ("DMS", "Durée moyenne de séjour", "EFFICIENCY", "Nombre moyen de jours d'hospitalisation", "jours", "≤5", "MONTHLY"),
    ("INOSO", "Taux d'infections nosocomiales", "SAFETY", "Infections acquises à l'hôpital", "%", "<5", "QUARTERLY"),
    ("ERR_MED", "Taux d'erreurs médicamenteuses", "SAFETY", "Erreurs de médication signalées", "taux", "<1", "MONTHLY"),
    ("CHUTE", "Taux de chutes", "SAFETY", "Chutes de patients hospitalisés", "taux", "<2", "MONTHLY"),
    ("DELAI_URG", "Délai prise en charge urgence", "EFFICIENCY", "Temps d'attente aux urgences", "minutes", "<30", "MONTHLY"),
    ("TRANSFUS", "Conformité transfusion", "SAFETY", "Respect procédures transfusion", "%", "100", "QUARTERLY"),
    ("DOSSIER", "Complétude des dossiers", "EFFICIENCY", "Dossiers patients complets", "%", "≥90", "MONTHLY"),
    ("VACC", "Couverture vaccinale", "CLINICAL_OUTCOME", "Taux de vaccination", "%", "≥95", "QUARTERLY"),
]

PASSWORDS = {
    "SUPER_ADMIN": "admin123",
    "ADMIN": "admin123",
    "DOCTOR": "doctor123",
    "NURSE": "nurse123",
    "PHARMACIST": "pharma123",
    "LAB_TECH": "labtech123",
    "CASHIER": "caisse123",
    "MIDWIFE": "sagefemme123",
}


def _now():
    return datetime.utcnow()


def _days_ago(n):
    return _now() - timedelta(days=n)


def _hours_ago(n):
    return _now() - timedelta(hours=n)


def run_seed():
    init_db()
    db = SessionLocal()
    try:
        _run_seed_inner(db)
    except Exception as e:
        db.rollback()
        print(f"❌ Seed error: {e}")
        import traceback
        traceback.print_exc()
        # Don't re-raise — app should still start
    finally:
        db.close()


def _run_seed_inner(db):
    # ═══════════════════════════════════════
    # 1. FACILITIES
    # ═══════════════════════════════════════
    facilities = {}
    for code, name, category, region, prefecture in FACILITIES_DATA:
        f = db.query(Facility).filter(Facility.code == code).first()
        if not f:
            f = Facility(
                code=code,
                name=name,
                category=category,
                region=region,
                prefecture=prefecture,
                status="ACTIVE",
            )
            db.add(f)
            db.flush()
        facilities[code] = f

    # ═══════════════════════════════════════
    # 2. DEPARTMENTS per facility
    # ═══════════════════════════════════════
    departments = {}
    for code, facility in facilities.items():
        dept_list = DEPARTMENTS_DATA.get(facility.category, DEPARTMENTS_DATA["CSI"])
        for dept_code, dept_name, dept_cat in dept_list:
            d = db.query(Department).filter(
                Department.facility_id == facility.id,
                Department.code == dept_code,
            ).first()
            if not d:
                d = Department(
                    facility_id=facility.id,
                    code=dept_code,
                    name=dept_name,
                    category=dept_cat,
                    status="ACTIVE",
                )
                db.add(d)
                db.flush()
            departments[(code, dept_code)] = d

    # ═══════════════════════════════════════
    # 3. USERS
    # ═══════════════════════════════════════
    users = {}
    for email, first_name, last_name, role, facility_code in USERS_DATA:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            pw = PASSWORDS.get(role, "guineecare123")
            u = User(
                facility_id=facilities[facility_code].id,
                email=email,
                password_hash=hash_password(pw),
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_active=True,
            )
            db.add(u)
            db.flush()
        users[email] = u

    # ═══════════════════════════════════════
    # 4. STAFF MEMBERS
    # ═══════════════════════════════════════
    staff = {}
    prof_map = {
        "DOCTOR": ("MEDECIN", None),
        "NURSE": ("INFIRMIER", None),
        "MIDWIFE": ("SAGE_FEMME", None),
        "PHARMACIST": ("PHARMACIEN", None),
        "LAB_TECH": ("LABORANTIN", None),
        "CASHIER": ("ADMINISTRATIF", "Caisse"),
        "ADMIN": ("ADMINISTRATIF", "Direction"),
    }
    specialty_map = {
        "dr.diallo@chu-donka.gn": "Médecine interne",
        "dr.bah@chu-donka.gn": "Chirurgie générale",
        "dr.sow@chu-donka.gn": "Cardiologie",
        "dr.keita@chu-donka.gn": "Pédiatrie",
        "dr.toure@chu-donka.gn": "Gynécologie-obstétrique",
        "dr.conde@chu-donka.gn": "Neurologie",
        "dr.coulibaly@chu-ignace.gn": "Chirurgie générale",
        "dr.camara@chu-ignace.gn": "Médecine interne",
        "dr.diallo2@chu-ignace.gn": "ORL",
        "dr.sylla@hgr-kindia.gn": "Médecine générale",
        "dr.kaba@hgr-kindia.gn": "Chirurgie",
        "dr.barry@hgr-labe.gn": "Médecine générale",
        "dr.diallo3@hgr-kankan.gn": "Médecine générale",
        "dr.gbou@hgr-nzerekore.gn": "Médecine générale",
        "dr.traore@clinique-pasteur.gn": "Chirurgie générale",
        "dr.ndiaye@clinique-esperance.gn": "Médecine interne",
        "dr.yansane@hgr-boke.gn": "Médecine générale",
        "dr.dem@hgr-mamou.gn": "Médecine générale",
        "dr.sagna@hgr-faranah.gn": "Médecine générale",
    }
    staff_counter = 0
    for email, user in users.items():
        if user.role == "SUPER_ADMIN":
            continue
        emp_num = f"GC-EMP-{staff_counter:05d}"
        existing = db.query(StaffMember).filter(StaffMember.employee_number == emp_num).first()
        if existing:
            staff[email] = existing
            continue
        prof_info = prof_map.get(user.role, ("AUTRE", None))
        spec = specialty_map.get(email, prof_info[1])
        # Find department based on role
        dept_id = None
        dept_code_map = {
            "DOCTOR": "MED",
            "MIDWIFE": "MAT",
            "PHARMACIST": "PHA",
            "LAB_TECH": "LAB",
            "CASHIER": "CAI",
            "ADMIN": "ADM",
            "NURSE": "MED",
        }
        target_dept_code = dept_code_map.get(user.role, "MED")
        for fc, fac in facilities.items():
            if fac.id == user.facility_id:
                dept = departments.get((fc, target_dept_code))
                if dept:
                    dept_id = dept.id
                break

        sm = StaffMember(
            facility_id=user.facility_id,
            user_id=user.id,
            employee_number=emp_num,
            first_name=user.first_name,
            last_name=user.last_name,
            profession=prof_info[0],
            specialty=spec,
            department_id=dept_id,
            phone=f"+224 6{randint(10,99)} {randint(10,99)} {randint(10,99)} {randint(10,99)}",
            email=user.email,
            hire_date=_days_ago(randint(365, 3650)),
            status="ACTIVE",
        )
        db.add(sm)
        db.flush()
        staff[email] = sm
        staff_counter += 1

    # ═══════════════════════════════════════
    # 5. PATIENTS — 50 patients across facilities
    # ═══════════════════════════════════════
    patients = []
    facility_codes_list = list(facilities.keys())
    for i in range(1, 51):
        pat_num = f"GC-PAT-{i:06d}"
        existing = db.query(Patient).filter(Patient.patient_number == pat_num).first()
        if existing:
            patients.append(existing)
            continue

        is_male = i % 2 == 0
        if is_male:
            first = choice(PATIENT_FIRST_NAMES_M)
        else:
            first = choice(PATIENT_FIRST_NAMES_F)
        last = choice(PATIENT_LAST_NAMES)

        # Distribute across facilities
        fc = facility_codes_list[i % len(facility_codes_list)]
        fac = facilities[fc]

        # Age distribution
        age = randint(1, 85)
        dob = _days_ago(age * 365 + randint(0, 364))
        gender = "M" if is_male else "F"

        # Address
        if fac.region == "Conakry":
            address = f"{randint(1,500)} Quartier {choice(PREFECTURES_CONAKRY)}, Conakry"
        else:
            address = f"Ville de {fac.prefecture}, Région de {fac.region}"

        # Insurance
        has_insurance = randint(1, 10) > 6
        insurance = None
        if has_insurance:
            insurance = f"INAM-GN-{randint(100000, 999999)}"

        # National ID
        national_id = f"GN-{randint(100000000, 999999999)}"

        p = Patient(
            facility_id=fac.id,
            patient_number=pat_num,
            first_name=first,
            last_name=last,
            date_of_birth=dob.date() if hasattr(dob, 'date') else dob,
            gender=gender,
            phone=f"+224 6{randint(10,99)} {randint(10,99)} {randint(10,99)} {randint(10,99)}",
            address=address,
            national_id=national_id,
            insurance_number=insurance,
            emergency_contact_name=f"{choice(PATIENT_LAST_NAMES)} {choice(PATIENT_FIRST_NAMES_M + PATIENT_FIRST_NAMES_F)}",
            emergency_contact_phone=f"+224 6{randint(10,99)} {randint(10,99)} {randint(10,99)} {randint(10,99)}",
            status="ACTIVE",
        )
        db.add(p)
        db.flush()
        patients.append(p)

    # ═══════════════════════════════════════
    # 6. ROOMS & BEDS for main facilities
    # ═══════════════════════════════════════
    rooms = {}
    beds = {}
    for fc in ["CHU-DONKA", "CHU-IGNACE-DEEN", "HGR-KINDIA", "HGR-KANKAN", "HGR-LABE", "CLINIQUE-PASTEUR"]:
        fac = facilities[fc]
        room_types = {
            "MED": ("MED", [("INDIVIDUELLE", 4), ("DOUBLE", 6), ("COLLECTIVE", 4)]),
            "CHIR": ("CHIR", [("INDIVIDUELLE", 2), ("DOUBLE", 4), ("COLLECTIVE", 3)]),
            "MAT": ("MAT", [("INDIVIDUELLE", 3), ("DOUBLE", 4), ("COLLECTIVE", 2)]),
            "PED": ("PED", [("DOUBLE", 3), ("COLLECTIVE", 3)]),
            "REANIM": ("REANIM", [("INDIVIDUELLE", 4), ("ICU", 4)]),
        }
        for dept_code, (prefix, types) in room_types.items():
            dept = departments.get((fc, dept_code))
            if not dept:
                continue
            for room_type, count in types:
                for r_idx in range(1, count + 1):
                    room_code = f"{prefix}-{room_type[:3].upper()}-{r_idx:02d}"
                    room_name = f"Chambre {room_code}"
                    existing_room = db.query(Room).filter(
                        Room.facility_id == fac.id,
                        Room.code == room_code,
                    ).first()
                    if not existing_room:
                        existing_room = Room(
                            facility_id=fac.id,
                            department_id=dept.id,
                            code=room_code,
                            name=room_name,
                            room_type=room_type.upper(),
                            status="ACTIVE",
                        )
                        db.add(existing_room)
                        db.flush()
                    rooms[(fc, room_code)] = existing_room

                    # Add beds per room
                    bed_count = 1 if room_type == "INDIVIDUELLE" else (2 if room_type == "DOUBLE" else randint(4, 8))
                    if room_type == "ICU":
                        bed_count = 4
                    for b_idx in range(1, bed_count + 1):
                        bed_number = f"{room_code}-L{b_idx}"
                        existing_bed = db.query(Bed).filter(
                            Bed.facility_id == fac.id,
                            Bed.room_id == existing_room.id,
                            Bed.bed_number == bed_number,
                        ).first()
                        if not existing_bed:
                            existing_bed = Bed(
                                facility_id=fac.id,
                                room_id=existing_room.id,
                                bed_number=bed_number,
                                bed_status="AVAILABLE",
                            )
                            db.add(existing_bed)
                            db.flush()
                        beds[(fc, bed_number)] = existing_bed

    # ═══════════════════════════════════════
    # 7. OPERATING ROOMS
    # ═══════════════════════════════════════
    op_rooms = {}
    for fc, room_defs in [
        ("CHU-DONKA", [("BLOC-01", "Salle 1 - Chirurgie générale", "GENERAL"), ("BLOC-02", "Salle 2 - Orthopédie", "ORTHOPEDIC"), ("BLOC-03", "Salle 3 - Urgences", "GENERAL"), ("BLOC-04", "Salle 4 - Cardiaque", "CARDIAC")]),
        ("CHU-IGNACE-DEEN", [("BLOC-01", "Salle 1", "GENERAL"), ("BLOC-02", "Salle 2 - Pédiatrique", "PEDIATRIC")]),
        ("HGR-KINDIA", [("BLOC-01", "Salle 1", "GENERAL")]),
        ("HGR-KANKAN", [("BLOC-01", "Salle 1", "GENERAL")]),
        ("CLINIQUE-PASTEUR", [("BLOC-01", "Salle 1", "GENERAL")]),
    ]:
        fac = facilities[fc]
        for code, name, rtype in room_defs:
            existing_or = db.query(OperatingRoom).filter(
                OperatingRoom.facility_id == fac.id,
                OperatingRoom.code == code,
            ).first()
            if not existing_or:
                existing_or = OperatingRoom(
                    facility_id=fac.id,
                    code=code,
                    name=name,
                    room_type=rtype,
                    status="AVAILABLE",
                )
                db.add(existing_or)
                db.flush()
            op_rooms[(fc, code)] = existing_or

    # ═══════════════════════════════════════
    # 8. ADMISSIONS — 30 admissions with various statuses
    # ═══════════════════════════════════════
    admissions = []
    admission_types = ["CONSULTATION", "URGENCE", "HOSPITALISATION", "PROGRAMMÉ", "MATERNITÉ"]
    doctor_emails = [e for e, u in users.items() if u.role == "DOCTOR"]
    for i in range(30):
        pat = patients[i % len(patients)]
        fc = None
        for fcode, fac in facilities.items():
            if fac.id == pat.facility_id:
                fc = fcode
                break
        if not fc:
            fc = "CHU-DONKA"

        # Find department for this facility
        dept_options = [dk for dk in departments.keys() if dk[0] == fc]
        dept = departments[choice(dept_options)] if dept_options else None

        adm_type = choice(admission_types)
        is_open = randint(1, 10) > 4
        days_back = randint(1, 90)

        a = Admission(
            facility_id=pat.facility_id,
            patient_id=pat.id,
            department_id=dept.id if dept else None,
            admission_type=adm_type,
            status="OPEN" if is_open else "CLOSED",
            admitted_at=_days_ago(days_back),
            closed_at=None if is_open else _days_ago(max(1, days_back - randint(1, 14))),
        )
        db.add(a)
        db.flush()
        admissions.append(a)

    # ═══════════════════════════════════════
    # 9. EMERGENCY VISITS — 20 visits
    # ═══════════════════════════════════════
    emergency_statuses = ["WAITING", "BEING_SEEN", "ORIENTED", "DISCHARGED", "HOSPITALIZED", "TRANSFERRED"]
    priority_levels = ["CRITICAL", "URGENT", "NORMAL", "LOW"]
    chief_complaints = [
        "Douleurs abdominales aiguës", "Fièvre élevée depuis 3 jours", "Céphalées intenses avec vomissements",
        "Dyspnée", "Traumatisme membre inférieur", "Hémorragie post-partum", "Crise convulsive",
        "Douleur thoracique", "Brûlure 2ème degré", "Intoxication alimentaire",
        "Paludisme grave", "Diarrhée profuse avec déshydratation", "Fracture ouverte",
        "Accouchement imminent", "Choc anaphylactique", "Morsure de serpent",
        "Crise drépanocytaire", "Insuffisance rénale aiguë", "Pneumopathie sévère",
        "Hémorragie digestive",
    ]
    orientations = ["MÉDECINE", "CHIRURGIE", "RÉANIMATION", "MATERNITÉ", "PÉDIATRIE", "DOMICILE", "TRANSFERT"]
    for i in range(20):
        pat = patients[i % len(patients)]
        fc = None
        for fcode, fac in facilities.items():
            if fac.id == pat.facility_id:
                fc = fcode
                break
        if not fc:
            fc = "CHU-DONKA"

        adm = admissions[i] if i < len(admissions) else None
        priority = choice(priority_levels)
        status = emergency_statuses[min(i, len(emergency_statuses) - 1)]
        doctor = users.get(choice(doctor_emails))

        hours_back = randint(1, 168)  # last 7 days
        arrived = _hours_ago(hours_back)
        seen = arrived + timedelta(minutes=randint(15, 120)) if status != "WAITING" else None
        discharged = seen + timedelta(hours=randint(1, 24)) if status in ("DISCHARGED", "HOSPITALIZED", "TRANSFERRED") else None

        ev = EmergencyVisit(
            facility_id=pat.facility_id,
            patient_id=pat.id,
            admission_id=adm.id if adm else None,
            priority_level=priority,
            chief_complaint=chief_complaints[i % len(chief_complaints)],
            status=status,
            orientation=choice(orientations) if status in ("ORIENTED", "DISCHARGED", "HOSPITALIZED") else None,
            attending_doctor_id=doctor.id if doctor else None,
            vital_signs=json.dumps({
                "temperature": f"{randint(36, 40)}.{randint(0,9)}°C",
                "blood_pressure": f"{randint(90,180)}/{randint(60,100)} mmHg",
                "heart_rate": f"{randint(60,130)} bpm",
                "oxygen_sat": f"{randint(85,100)}%",
                "weight": f"{randint(40,110)} kg",
            }),
            treatment_notes=f"Traitement initié aux urgences. Surveillance clinique." if status != "WAITING" else None,
            discharge_summary="Patient stabilisé et orienté." if status in ("DISCHARGED",) else None,
            discharge_destination=choice(["HOME", "HOSPITALIZATION", "TRANSFER"]) if status in ("DISCHARGED", "HOSPITALIZED") else None,
            seen_at=seen,
            discharged_at=discharged,
            arrived_at=arrived,
            updated_at=_now(),
        )
        db.add(ev)
    db.flush()

    # ═══════════════════════════════════════
    # 10. HOSPITAL STAYS — 15 active stays
    # ═══════════════════════════════════════
    hospital_stays = []
    available_beds = [b for b in beds.values() if b.bed_status == "AVAILABLE"]
    for i in range(min(15, len(admissions), len(available_beds))):
        adm = admissions[i]
        bed = available_beds[i]
        stay_reasons = [
            "Paludisme grave", "Appendicite aiguë", "Pneumopathie", "Insuffisance cardiaque",
            "Accouchement compliqué", "Fracture fémur", "Hémorragie digestive", "Crise drépanocytaire",
            "AVC", "Diabète déséquilibré", "Néphrite aiguë", "Choc septique",
            "Intoxication médicamenteuse", "Césarienne", "Traumatisme crânien",
        ]
        is_active = randint(1, 10) > 3
        hs = HospitalStay(
            facility_id=adm.facility_id,
            patient_id=adm.patient_id,
            admission_id=adm.id,
            bed_id=bed.id,
            reason=stay_reasons[i % len(stay_reasons)],
            status="ACTIVE" if is_active else "DISCHARGED",
            admitted_at=adm.admitted_at,
            discharged_at=None if is_active else _days_ago(randint(1, 14)),
        )
        db.add(hs)
        db.flush()
        hospital_stays.append(hs)

        # Mark bed as occupied
        if is_active:
            bed.bed_status = "OCCUPIED"
            db.flush()

    # ═══════════════════════════════════════
    # 11. PHARMACY PRODUCTS & STOCK
    # ═══════════════════════════════════════
    products = {}
    pharmacy_facilities = [fc for fc, f in facilities.items() if f.category in ("CHU", "HGR", "PRIVE", "PHARMACIE")]
    for fc in pharmacy_facilities:
        fac = facilities[fc]
        for code, name, category, form, dosage, qty, threshold in PHARMACY_PRODUCTS_DATA:
            # Smaller stock for HGR and pharmacies
            if fac.category == "PHARMACIE":
                qty_mult = 3
            elif fac.category == "HGR":
                qty_mult = 0.5
            else:
                qty_mult = 1

            p = db.query(PharmacyProduct).filter(
                PharmacyProduct.facility_id == fac.id,
                PharmacyProduct.code == code,
            ).first()
            if not p:
                p = PharmacyProduct(
                    facility_id=fac.id,
                    code=code,
                    name=name,
                    category=category,
                    form=form,
                    dosage=dosage,
                    status="ACTIVE",
                )
                db.add(p)
                db.flush()
            products[(fc, code)] = p

            stock = db.query(PharmacyStock).filter(
                PharmacyStock.facility_id == fac.id,
                PharmacyStock.product_id == p.id,
            ).first()
            if not stock:
                db.add(PharmacyStock(
                    facility_id=fac.id,
                    product_id=p.id,
                    quantity_available=int(qty * qty_mult),
                    min_threshold=threshold,
                ))

    # Stock movements
    movement_types = ["ENTRY", "EXIT", "ADJUSTMENT", "RETURN"]
    for fc in ["CHU-DONKA", "CHU-IGNACE-DEEN", "PHARMA-CENTRALE", "HGR-KINDIA"]:
        fac = facilities[fc]
        prods = db.query(PharmacyProduct).filter(PharmacyProduct.facility_id == fac.id).all()
        for j, prod in enumerate(prods[:10]):
            for k in range(randint(2, 5)):
                sm = StockMovement(
                    facility_id=fac.id,
                    product_id=prod.id,
                    movement_type=choice(movement_types),
                    quantity=randint(10, 500),
                    reason=choice(["Réapprovisionnement", "Dispensation patient", "Ajustement inventaire", "Retour fournisseur", "Transfert inter-service"]),
                    performed_by=list(users.values())[0].id if users else None,
                    performed_at=_days_ago(randint(1, 60)),
                )
                db.add(sm)
    db.flush()

    # ═══════════════════════════════════════
    # 12. LAB TESTS, ORDERS & RESULTS
    # ═══════════════════════════════════════
    lab_tests = {}
    for fc in ["CHU-DONKA", "CHU-IGNACE-DEEN", "HGR-KINDIA", "HGR-KANKAN", "HGR-LABE"]:
        fac = facilities[fc]
        for code, name, category, sample in LAB_TESTS_DATA:
            lt = db.query(LabTest).filter(
                LabTest.facility_id == fac.id,
                LabTest.code == code,
            ).first()
            if not lt:
                lt = LabTest(
                    facility_id=fac.id,
                    code=code,
                    name=name,
                    category=category,
                    sample_type=sample,
                    status="ACTIVE",
                )
                db.add(lt)
                db.flush()
            lab_tests[(fc, code)] = lt

    # Lab orders for first 20 patients
    lab_tech_emails = [e for e, u in users.items() if u.role == "LAB_TECH"]
    for i in range(20):
        pat = patients[i % len(patients)]
        fc = None
        for fcode, fac in facilities.items():
            if fac.id == pat.facility_id:
                fc = fcode
                break
        if not fc or fc not in facilities:
            fc = "CHU-DONKA"

        test_keys = [k for k in lab_tests.keys() if k[0] == fc]
        if not test_keys:
            test_keys = list(lab_tests.keys())[:5]
        test_key = choice(test_keys)
        lt = lab_tests[test_key]
        doctor = users.get(choice(doctor_emails))

        priority = choice(["NORMAL", "URGENT"])
        order_status = choice(["ORDERED", "IN_PROGRESS", "COMPLETED"])

        lo = LabOrder(
            facility_id=pat.facility_id,
            patient_id=pat.id,
            admission_id=admissions[i].id if i < len(admissions) else None,
            test_id=lt.id,
            priority=priority,
            status=order_status,
            ordered_by=doctor.id if doctor else None,
            ordered_at=_days_ago(randint(1, 30)),
        )
        db.add(lo)
        db.flush()

        # Add result for completed orders
        if order_status == "COMPLETED":
            result_map = {
                "NFS": ("GB: 8.5 G/L, GR: 4.8 T/L, Hb: 14.2 g/dL, Ht: 42%, Plq: 250 G/L", "NFS normale"),
                "HGB": ("14.2 g/dL", "Hémoglobine normale"),
                "GLY": (f"{randint(70,250)} mg/dL", "Glycémie" + (" normale" if randint(1,2)==1 else " élevée - diabète suspecté")),
                "GE": ("Positive - Plasmodium falciparum", "Paludisme confirmé"),
                "TDR-PALU": ("Positif", "Paludisme à P. falciparum"),
                "CREAT": (f"{randint(5,25)} mg/L", "Créatinine" + (" normale" if randint(1,3)>1 else " élevée - insuffisance rénale")),
                "UREE": (f"{randint(0.1,0.8):.1f} g/L", "Urée normale"),
                "GROUP": (choice(["O+", "A+", "B+", "AB+", "O-", "A-"]), "Groupe déterminé"),
                "CRP": (f"{randint(1,100)} mg/L", "CRP" + (" normale" if randint(1,3)>1 else " élevée - syndrome inflammatoire")),
                "ECBU": ("E. coli 10^5 UFC/ml", "Infection urinaire à E. coli"),
                "HIV": (choice(["Négatif", "Positif"]), "Sérologie VIH"),
                "HBV": (choice(["Négatif", "Positif - Ag HBs"]), "Sérologie Hépatite B"),
            }
            result_data = result_map.get(test_key[1], (f"{randint(10,200)} unités", "Résultat en cours d'interprétation"))
            lab_tech = users.get(choice(lab_tech_emails)) if lab_tech_emails else None

            lr = LabResult(
                facility_id=pat.facility_id,
                order_id=lo.id,
                result_value=result_data[0],
                interpretation=result_data[1],
                status="VALIDATED" if randint(1, 3) > 1 else "DRAFT",
                entered_by=lab_tech.id if lab_tech else None,
                validated_by=lab_tech.id if lab_tech and randint(1, 3) > 1 else None,
                entered_at=_days_ago(randint(1, 20)),
                validated_at=_days_ago(randint(0, 15)) if randint(1, 3) > 1 else None,
            )
            db.add(lr)
    db.flush()

    # ═══════════════════════════════════════
    # 13. IMAGING ORDERS & RESULTS
    # ═══════════════════════════════════════
    imaging_data = [
        ("RADIOGRAPHIE", "Thorax", "Toux persistante, fièvre", "ROUTINE"),
        ("RADIOGRAPHIE", "Abdomen sans préparation", "Douleurs abdominales", "URGENT"),
        ("RADIOGRAPHIE", "Bassin de face", "Traumatisme du bassin", "URGENT"),
        ("ÉCHOGRAPHIE", "Abdomen", "Douleurs hypocondre droit", "ROUTINE"),
        ("ÉCHOGRAPHIE", "Pelvienne", "Grossesse - suivi", "ROUTINE"),
        ("ÉCHOGRAPHIE", "Obstétricale", "CPN - évaluation croissance", "ROUTINE"),
        ("SCANNER", "Cérébral", "Céphalées avec signes de focalité", "EMERGENCY"),
        ("SCANNER", "Thoraco-abdominal", "Traumatisme polyviscéral", "EMERGENCY"),
        ("RADIOGRAPHIE", "Rachis lombaire", "Lombalgie chronique", "ROUTINE"),
        ("ÉCHOGRAPHIE", "Cardiaque", "Dyspnée, souffle cardiaque", "URGENT"),
    ]
    for i, (exam_type, body_region, clinical_info, urgency) in enumerate(imaging_data):
        pat = patients[i % len(patients)]
        fc = None
        for fcode, fac in facilities.items():
            if fac.id == pat.facility_id:
                fc = fcode
                break
        if not fc:
            fc = "CHU-DONKA"
        doctor = users.get(choice(doctor_emails))
        img_status = choice(["PENDING", "IN_PROGRESS", "COMPLETED"])

        io = ImagingOrder(
            facility_id=pat.facility_id,
            patient_id=pat.id,
            requesting_doctor_id=doctor.id if doctor else None,
            exam_type=exam_type,
            body_region=body_region,
            clinical_info=clinical_info,
            urgency=urgency,
            status=img_status,
            ordered_at=_days_ago(randint(1, 30)),
            performed_at=_days_ago(randint(0, 20)) if img_status != "PENDING" else None,
            reported_at=_days_ago(randint(0, 15)) if img_status == "COMPLETED" else None,
        )
        db.add(io)
        db.flush()

        if img_status == "COMPLETED":
            findings_map = {
                "Thorax": "Syndrome alvéolo-interstitiel bilatéral. Pas d'épanchement pleural.",
                "Abdomen sans préparation": "Pas de pneumopéritoine. Niveaux hydro-aériques évocateurs d'occlusion.",
                "Bassin de face": "Fracture du cotyle droit sans déplacement.",
                "Abdomen": "Lithiase vésiculaire. Vésicule distendue. Pas de signe de cholécystite aiguë.",
                "Pelvienne": "Masse annexielle droite de 5 cm, d'allure kystique.",
                "Obstétricale": "Grossesse monofoetale en présentation céphalique. BIP normal. Liquide amniotique normal.",
                "Cérébral": "Hypodensité sylvienne gauche - AVC ischémique récent.",
                "Thoraco-abdominal": "Épanchement pleural droit. Lésion hépatique suspecte segment VI.",
                "Rachis lombaire": "Discopathie L4-L5 avec protrusion discale. Pas de hernie compressive.",
                "Cardiaque": "FEVG conservée à 60%. IM minime. Pas d'hypertrophie ventriculaire.",
            }
            ir = ImagingResult(
                facility_id=pat.facility_id,
                order_id=io.id,
                patient_id=pat.id,
                radiologist_id=doctor.id if doctor else None,
                findings=findings_map.get(body_region, "Examen réalisé. Constatations en cours de rédaction."),
                conclusion="Compte rendu validé par le radiologue." if randint(1,3)>1 else "En attente de validation.",
                recommendation="Contrôle recommandé dans 3 mois." if randint(1,2)==1 else None,
                status="VALIDATED" if randint(1, 3) > 1 else "DRAFT",
                validated_at=_days_ago(randint(0, 10)) if randint(1, 3) > 1 else None,
            )
            db.add(ir)
    db.flush()

    # ═══════════════════════════════════════
    # 14. CLINICAL NOTES, MEASUREMENTS, DIAGNOSES
    # ═══════════════════════════════════════
    for i in range(25):
        pat = patients[i % len(patients)]
        adm = admissions[i] if i < len(admissions) else None
        doctor = users.get(choice(doctor_emails))

        # Clinical note
        note_types = ["OBSERVATION", "CONSULTATION", "PRESCRIPTION", "NOTE"]
        notes_content = [
            "Patient admis pour paludisme grave. Traitement: Coartem + quinine IV. Surveillance clinique rapprochée.",
            "Consultation de suivi. Amélioration des symptômes sous traitement. Poursuivre le même schéma thérapeutique.",
            "Prescription: Amoxicilline 1g x3/jour pendant 7 jours, Paracétamol 1g si douleur/fièvre, Oméprazole 20mg/jour.",
            "Bilan biologique demandé: NFS, CRP, Glycémie, Créatinine. Résultats attendus pour adaptation thérapeutique.",
            "Patient stable sur le plan hémodynamique. Apyrétique depuis 48h. Reprise du transit. Sortie envisagée.",
            "Examen clinique: PA 120/80, FC 78, T° 37.2°C. Auscultation cardiaque: pas de souffle. Abdomen souple.",
            "Avis cardiologique demandé pour suspicion d'insuffisance cardiaque. ECG réalisé: AC/FA à 90/min.",
            "Réévaluation du traitement antihypertenseur. Amlodipine 10mg + Captopril 50mg. Objectif PA < 140/90.",
            "Douleur contrôlée par palier 2. Pas d'effet indésirable. Poursuivre surveillance rénale.",
            "Patient vu en consultation prénatale. Grossesse évolutive. Bébé en bonne santé. Prochain RDV dans 1 mois.",
        ]
        cn = ClinicalNote(
            facility_id=pat.facility_id,
            patient_id=pat.id,
            admission_id=adm.id if adm else None,
            note_type=choice(note_types),
            content=choice(notes_content),
            created_by=doctor.id if doctor else None,
            created_at=_days_ago(randint(1, 30)),
        )
        db.add(cn)

        # Measurements
        measurements = [
            ("TEMPERATURE", f"{randint(36,40)}.{randint(0,9)}", "°C"),
            ("BLOOD_PRESSURE", f"{randint(90,180)}/{randint(60,100)}", "mmHg"),
            ("HEART_RATE", f"{randint(55,130)}", "bpm"),
            ("WEIGHT", f"{randint(40,120)}", "kg"),
            ("OXYGEN_SAT", f"{randint(88,100)}", "%"),
        ]
        for m_type, val, unit in measurements:
            pm = PatientMeasurement(
                facility_id=pat.facility_id,
                patient_id=pat.id,
                admission_id=adm.id if adm else None,
                measurement_type=m_type,
                value=val,
                unit=unit,
                recorded_by=users.get(choice([e for e in users if users[e].role in ("NURSE", "DOCTOR")] or list(users.keys()))).id if users else None,
                recorded_at=_days_ago(randint(1, 14)),
            )
            db.add(pm)

        # Diagnoses (for first 15 patients)
        if i < 15:
            diag = COMMON_DIAGNOSES[i % len(COMMON_DIAGNOSES)]
            d = Diagnosis(
                facility_id=pat.facility_id,
                patient_id=pat.id,
                admission_id=adm.id if adm else None,
                diagnosis_code=diag[0],
                diagnosis_label=diag[1],
                diagnosis_type=diag[2],
                status=choice(["ACTIVE", "RESOLVED", "CHRONIC"]),
                created_by=doctor.id if doctor else None,
                created_at=_days_ago(randint(1, 30)),
            )
            db.add(d)
    db.flush()

    # ═══════════════════════════════════════
    # 15. MATERNITY RECORDS
    # ═══════════════════════════════════════
    female_patients = [p for p in patients if p.gender == "F"]
    midwife_emails = [e for e, u in users.items() if u.role == "MIDWIFE"]
    maternity_records = []

    # Prenatal records for 8 patients
    for i in range(min(8, len(female_patients))):
        pat = female_patients[i]
        fc = None
        for fcode, fac in facilities.items():
            if fac.id == pat.facility_id:
                fc = fcode
                break
        if not fc:
            fc = "CHU-DONKA"

        blood_types = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
        risk_levels = ["LOW", "MEDIUM", "HIGH"]

        mr = MaternityRecord(
            facility_id=pat.facility_id,
            patient_id=pat.id,
            gravidity=str(randint(1, 7)),
            parity=str(randint(0, 5)),
            last_menstrual_period=_days_ago(randint(60, 250)),
            expected_due_date=_days_ago(randint(-90, 30)),
            blood_type=choice(blood_types[:6]),
            Rh_factor=choice(["Positif", "Négatif"]),
            allergies=choice(["Aucune", "Pénicilline", "Sulfamides", "Aucune", "Aucune"]),
            risk_level=choice(risk_levels),
            status=choice(["ACTIVE", "DELIVERED", "ACTIVE", "ACTIVE"]),
            created_by=users.get(midwife_emails[0]).id if midwife_emails else None,
            created_at=_days_ago(randint(30, 180)),
        )
        db.add(mr)
        db.flush()
        maternity_records.append(mr)

        # Add 2-4 prenatal consultations per record
        for j in range(randint(2, 4)):
            mc = MaternityConsultation(
                facility_id=pat.facility_id,
                record_id=mr.id,
                consultation_type=choice(["PRENATAL", "PRENATAL", "FOLLOW_UP"]),
                gestational_age_weeks=float(randint(12, 38)),
                weight_kg=float(randint(50, 95)),
                blood_pressure=f"{randint(100,140)}/{randint(60,90)}",
                fetal_heart_rate=float(randint(120, 160)),
                fundal_height_cm=float(randint(20, 36)),
                notes="Grossesse évolutive. Pas de signe d'alerte." if randint(1,3)>1 else "Surveillance renforcée recommandée.",
                consulted_by=users.get(choice(midwife_emails)).id if midwife_emails else None,
                consulted_at=_days_ago(randint(7, 120)),
            )
            db.add(mc)

    # Delivery records for 3 patients
    for i in range(min(3, len(maternity_records))):
        mr = maternity_records[i]
        midwife = users.get(choice(midwife_emails)) if midwife_emails else None
        delivery_types = ["VAGINAL", "CESAREAN", "ASSISTED"]
        dt = delivery_types[i % len(delivery_types)]
        dr = DeliveryRecord(
            facility_id=mr.facility_id,
            record_id=mr.id,
            delivery_type=dt,
            delivery_date=_days_ago(randint(5, 60)),
            gestational_age_weeks=float(randint(37, 42)),
            complications=None if dt == "VAGINAL" else "Dystocie - indication de césarienne",
            baby_gender=choice(["M", "F"]),
            baby_weight_kg=float(randint(2500, 4200)) / 1000,
            baby_apgar_1=str(randint(6, 10)),
            baby_apgar_5=str(randint(8, 10)),
            baby_health_status="BON" if randint(1,5)>1 else "SURVEILLANCE",
            performed_by=midwife.id if midwife else None,
            notes="Accouchement sans complication." if dt == "VAGINAL" else "Césarienne réalisée en urgence. Bébé en bonne santé.",
        )
        db.add(dr)
    db.flush()

    # ═══════════════════════════════════════
    # 16. SURGERY SCHEDULES & REPORTS
    # ═══════════════════════════════════════
    surgery_data = [
        ("Appendicectomie", "CHIR-APPEN", "NOT_APPLICABLE", "PLANNED"),
        ("Cure de hernie inguinale", "CHIR-HERNIE", "LEFT", "PLANNED"),
        ("Césarienne", "CHIR-CESAR", "NOT_APPLICABLE", "URGENT"),
        ("Ostéosynthèse fracture tibia", "CHIR-OSTEO", "RIGHT", "PLANNED"),
        ("Laparotomie exploratrice", "CHIR-LAP", "NOT_APPLICABLE", "EMERGENCY"),
        ("Thyroidectomie totale", "CHIR-THYR", "NOT_APPLICABLE", "PLANNED"),
        ("Cholécystectomie", "CHIR-CHOLE", "NOT_APPLICABLE", "PLANNED"),
        ("Prostatectomie", "CHIR-PROST", "NOT_APPLICABLE", "PLANNED"),
    ]
    surgery_schedules = []
    for i, (proc_name, proc_code, laterality, urgency) in enumerate(surgery_data):
        pat = patients[i % len(patients)]
        fc = None
        for fcode, fac in facilities.items():
            if fac.id == pat.facility_id:
                fc = fcode
                break
        if not fc:
            fc = "CHU-DONKA"

        # Find OR and surgeon
        or_key = [k for k in op_rooms.keys() if k[0] == fc]
        opr = op_rooms[or_key[0]] if or_key else None
        surgeon = users.get(choice(doctor_emails))
        anesth = users.get(choice(doctor_emails))

        sched_status = choice(["SCHEDULED", "IN_PROGRESS", "COMPLETED", "COMPLETED", "POSTPONED"])
        sched_date = _days_ago(randint(0, 14))

        ss = SurgerySchedule(
            facility_id=pat.facility_id,
            patient_id=pat.id,
            operating_room_id=opr.id if opr else None,
            surgeon_id=surgeon.id if surgeon else None,
            anesthesiologist_id=anesth.id if anesth and anesth.id != (surgeon.id if surgeon else None) else None,
            procedure_name=proc_name,
            procedure_code=proc_code,
            laterality=laterality,
            urgency=urgency,
            status=sched_status,
            scheduled_date=sched_date,
            started_at=sched_date if sched_status != "SCHEDULED" else None,
            ended_at=sched_date + timedelta(hours=randint(1, 4)) if sched_status == "COMPLETED" else None,
            notes=f"Intervention programmée. Bilan pré-opératoire réalisé." if urgency == "PLANNED" else "Intervention en urgence.",
        )
        db.add(ss)
        db.flush()
        surgery_schedules.append(ss)

        # Surgery team
        roles = ["SURGEON", "ANESTHESIOLOGIST", "NURSE_INSTRUMENTIST", "NURSE_ANESTHETIST", "AIDE_OPERATOR", "CIRCULATING_NURSE"]
        for role in roles[:randint(3, 5)]:
            stm = SurgeryTeamMember(
                schedule_id=ss.id,
                user_id=surgeon.id if role == "SURGEON" and surgeon else (anesth.id if role == "ANESTHESIOLOGIST" and anesth else list(users.values())[0].id if users else None),
                role=role,
            )
            db.add(stm)

        # Surgery report for completed
        if sched_status == "COMPLETED":
            sr = SurgeryReport(
                facility_id=pat.facility_id,
                schedule_id=ss.id,
                patient_id=pat.id,
                surgeon_id=surgeon.id if surgeon else None,
                operative_findings=f"Constatations per-opératoires: {proc_name} réalisée sans complication majeure.",
                procedure_performed=proc_name + " - geste réalisé conformément au programme opératoire.",
                complications="Aucune complication per-opératoire." if randint(1, 4) > 1 else "Saignement per-opératoire contrôlé.",
                specimens="Pièce opératoire envoyée en anatomopathologie." if randint(1, 3) > 1 else None,
                blood_loss=f"{randint(50, 500)} ml",
                anesthesia_type=choice(["GÉNÉRALE", "RACHIANESTHÉSIE", "LOCORÉGIONALE"]),
                status="VALIDATED" if randint(1, 3) > 1 else "DRAFT",
                validated_at=_days_ago(randint(0, 7)) if randint(1, 3) > 1 else None,
            )
            db.add(sr)
    db.flush()

    # ═══════════════════════════════════════
    # 17. BILLING — Tariffs, Invoices, Payments
    # ═══════════════════════════════════════
    for fc in ["CHU-DONKA", "CHU-IGNACE-DEEN", "HGR-KINDIA", "HGR-KANKAN", "HGR-LABE", "CLINIQUE-PASTEUR", "CLINIQUE-ESPERANCE"]:
        fac = facilities[fc]
        # Price adjustment for private clinics
        price_mult = 2.0 if fac.category == "PRIVE" else 1.0
        for code, name, category, unit_price in TARIFF_ITEMS_DATA:
            ti = db.query(TariffItem).filter(
                TariffItem.facility_id == fac.id,
                TariffItem.code == code,
            ).first()
            if not ti:
                ti = TariffItem(
                    facility_id=fac.id,
                    code=code,
                    name=name,
                    category=category,
                    unit_price=int(unit_price * price_mult),
                    status="ACTIVE",
                )
                db.add(ti)
    db.flush()

    # Invoices for 20 patients
    cashier_emails = [e for e, u in users.items() if u.role == "CASHIER"]
    for i in range(20):
        pat = patients[i % len(patients)]
        adm = admissions[i] if i < len(admissions) else None

        # Random invoice amount
        net = choice([25000, 50000, 75000, 100000, 150000, 200000, 350000, 500000, 750000, 1500000, 2500000])
        paid = int(net * choice([1.0, 1.0, 1.0, 0.5, 0.75, 0.3]))  # some partial payments
        inv_status = "PAID" if paid >= net else ("PARTIAL" if paid > 0 else "DRAFT")

        inv = Invoice(
            facility_id=pat.facility_id,
            patient_id=pat.id,
            admission_id=adm.id if adm else None,
            invoice_number=f"GC-FAC-{_now().year}-{i+1:05d}",
            description=choice(["Consultation + examens", "Hospitalisation + chirurgie", "Accouchement", "Examens laboratoire", "Urgences + imagerie", "Consultation prénatale + accouchement", "Bilan complet"]),
            net_amount=net,
            paid_amount=paid,
            balance_due=net - paid,
            status=inv_status,
            created_at=_days_ago(randint(1, 30)),
        )
        db.add(inv)
        db.flush()

        # Payment for paid invoices
        if paid > 0:
            p = Payment(
                facility_id=pat.facility_id,
                invoice_id=inv.id,
                amount=paid,
                payment_method=choice(["CASH", "MOBILE_MONEY", "VIREMENT", "CARTE"]),
                status="COMPLETED",
                received_by=users.get(choice(cashier_emails)).id if cashier_emails and users.get(choice(cashier_emails)) else None,
                received_at=_days_ago(randint(0, 25)),
            )
            db.add(p)
    db.flush()

    # ═══════════════════════════════════════
    # 18. QUALITY INDICATORS & INCIDENTS
    # ═══════════════════════════════════════
    for fc in ["CHU-DONKA", "CHU-IGNACE-DEEN", "HGR-KINDIA", "HGR-KANKAN"]:
        fac = facilities[fc]
        qi_records = {}
        for code, name, category, desc, unit, target, freq in QUALITY_INDICATORS_DATA:
            qi = db.query(QualityIndicator).filter(
                QualityIndicator.facility_id == fac.id,
                QualityIndicator.code == code,
            ).first()
            if not qi:
                qi = QualityIndicator(
                    facility_id=fac.id,
                    code=code,
                    name=name,
                    category=category,
                    description=desc,
                    unit=unit,
                    target_value=target,
                    frequency=freq,
                )
                db.add(qi)
                db.flush()
            qi_records[code] = qi

        # Quality measurements for last 6 months
        for code, qi in qi_records.items():
            for month in range(6):
                period_start = datetime(2026, month + 1, 1)
                period_end = datetime(2026, month + 1, 28) if month < 11 else datetime(2026, 12, 31)

                val_map = {
                    "IPS": str(randint(65, 95)),
                    "TMR24": f"{randint(1,5)}.{randint(0,9)}",
                    "SAT_PAT": str(randint(70, 98)),
                    "TAUX_OCC": str(randint(55, 95)),
                    "DMS": str(randint(3, 10)),
                    "INOSO": f"{randint(1,8)}.{randint(0,9)}",
                    "ERR_MED": f"{randint(0,3)}.{randint(0,9)}",
                    "CHUTE": f"{randint(0,4)}.{randint(0,9)}",
                    "DELAI_URG": str(randint(15, 60)),
                    "TRANSFUS": str(randint(85, 100)),
                    "DOSSIER": str(randint(70, 99)),
                    "VACC": str(randint(75, 99)),
                }

                qm = QualityMeasurement(
                    facility_id=fac.id,
                    indicator_id=qi.id,
                    period_start=period_start,
                    period_end=period_end,
                    value=val_map.get(code, str(randint(50, 100))),
                    numerator=str(randint(50, 200)),
                    denominator=str(randint(100, 300)),
                    notes="Données SNIS mensuelles",
                    recorded_by=list(users.values())[0].id if users else None,
                )
                db.add(qm)

    # Incident reports
    incidents = [
        ("CHUTE", "MODERATE", "Patient âgé chute au service de médecine", "Barrières de lit installées", "Absence de barrières de lit", "Installation de barrières sur tous les lits"),
        ("MEDICATION_ERROR", "MINOR", "Erreur de dosage de paracétamol en pédiatrie", "Dose corrigée immédiatement", "Confusion concentration sirop/adulte", "Étiquetage différencié et double vérification"),
        ("NOSOCOMIAL_INFECTION", "MAJOR", "Infection du site opératoire post-appendicectomie", "Antibiothérapie adaptée, isolement", "Non-respect protocole asepsie", "Formation équipe bloc, audit pratiques"),
        ("EQUIPMENT_FAILURE", "MODERATE", "Panne du générateur lors d'une intervention", "Transfert patient en salle 2", "Maintenance préventive non effectuée", "Plan de maintenance renforcé"),
        ("FALL", "MINOR", "Chute dans les toilettes du service maternité", "Examen clinique - pas de lésion", "Sol mouillé, absence de barre d'appui", "Installation de barres d'appui, signalétique"),
        ("MEDICATION_ERROR", "CRITICAL", "Administration de potassium à la place de sérum physiologique", "Arrêt immédiat, prise en charge réanimation", "Erreur d'étiquetage flacon", "Procédure de double vérification systématique"),
        ("NOSOCOMIAL_INFECTION", "MODERATE", "Cas de COVID-19 nosocomial en chirurgie", "Isolement du patient, dépistage contacts", "Visiteurs non dépistés", "Renforcement des mesures barrières"),
    ]
    for i, (inc_type, severity, desc, actions, root, corrective) in enumerate(incidents):
        pat = patients[i % len(patients)] if i < len(patients) else None
        fc = None
        if pat:
            for fcode, fac in facilities.items():
                if fac.id == pat.facility_id:
                    fc = fcode
                    break
        if not fc:
            fc = "CHU-DONKA"

        ir = IncidentReport(
            facility_id=facilities[fc].id,
            reported_by=list(users.values())[0].id if users else None,
            patient_id=pat.id if pat else None,
            incident_date=_days_ago(randint(1, 60)),
            incident_type=inc_type,
            severity=severity,
            description=desc,
            immediate_actions=actions,
            root_cause=root,
            corrective_actions=corrective,
            status=choice(["REPORTED", "UNDER_INVESTIGATION", "RESOLVED", "CLOSED"]),
        )
        db.add(ir)
    db.flush()

    # ═══════════════════════════════════════
    # 19. REPORTING — National Reports & Epidemic Alerts
    # ═══════════════════════════════════════
    for fc in ["CHU-DONKA", "CHU-IGNACE-DEEN", "HGR-KINDIA", "HGR-KANKAN", "HGR-LABE", "HGR-BOKE", "HGR-MAMOU", "HGR-NZEREKORE", "HGR-FARANAH"]:
        fac = facilities[fc]
        # Monthly national report
        nr = NationalReport(
            facility_id=fac.id,
            report_type="MONTHLY",
            period_start=datetime(2026, 5, 1),
            period_end=datetime(2026, 5, 31),
            total_admissions=str(randint(200, 1500)),
            total_discharges=str(randint(180, 1400)),
            total_deaths=str(randint(5, 45)),
            total_births=str(randint(50, 400)),
            total_surgeries=str(randint(30, 200)),
            total_emergency_visits=str(randint(300, 2000)),
            bed_occupancy_rate=f"{randint(55, 95)}%",
            average_stay_days=f"{randint(3, 8)}",
            disease_distribution=json.dumps({
                "paludisme": randint(80, 400),
                "diarrhée": randint(50, 200),
                "infection_respiratoire": randint(40, 300),
                "hypertension": randint(30, 150),
                "diabète": randint(20, 100),
                "grossesse": randint(40, 200),
            }),
            status=choice(["DRAFT", "SUBMITTED", "VALIDATED"]),
            submitted_by=list(users.values())[0].id if users else None,
            submitted_at=_days_ago(randint(1, 10)),
        )
        db.add(nr)

        # Health statistics
        stat_categories = [
            ("CONSULTATION", "Nombre total consultations", str(randint(500, 3000))),
            ("HOSPITALIZATION", "Taux d'occupation lits", f"{randint(55, 95)}%"),
            ("MATERNITY", "Nombre accouchements", str(randint(50, 400))),
            ("MATERNITY", "Mortalité maternelle", str(randint(0, 5))),
            ("SURGERY", "Nombre interventions", str(randint(30, 200))),
            ("EMERGENCY", "Passages urgences", str(randint(300, 2000))),
            ("PHARMACY", "Ordonnances dispensées", str(randint(400, 2500))),
            ("CONSULTATION", "Vaccinations", str(randint(100, 800))),
        ]
        for cat, metric, value in stat_categories:
            hs = HealthStatistic(
                facility_id=fac.id,
                category=cat,
                metric_name=metric,
                metric_value=value,
                period_start=datetime(2026, 5, 1),
                period_end=datetime(2026, 5, 31),
                unit="count" if "Nombre" in metric else ("rate" if "Taux" in metric else "percentage"),
                source=choice(["SNIS", "DHIS2", "MANUAL"]),
            )
            db.add(hs)

    # Epidemic alerts
    alerts = [
        ("Choléra", "12", "WARNING", "Conakry", "Apparition de cas groupés dans la commune de Matam", "Chloration de l'eau, sensibilisation communautaire"),
        ("Paludisme", "45", "ALERT", "Kindia", "Augmentation des cas de paludisme grave", "Distribution de moustiquaires imprégnées, TDR systématique"),
        ("Fièvre de Lassa", "3", "EMERGENCY", "N'Zérékoré", "Cas suspects de fièvre de Lassa en zone forestière", "Isolement des cas, investigation sur le terrain"),
        ("Rougeole", "8", "WARNING", "Kankan", "Cas de rougeole signalés en milieu scolaire", "Campagne de vaccination de riposte"),
        ("COVID-19", "5", "WATCH", "Conakry", "Resurgence de cas COVID-19", "Renforcement dépistage, port du masque"),
    ]
    for disease, count, level, region, desc, measures in alerts:
        ea = EpidemicAlert(
            facility_id=facilities["CHU-DONKA"].id,
            disease_name=disease,
            case_count=count,
            threshold_exceeded="YES",
            alert_level=level,
            region=region,
            description=desc,
            measures_taken=measures,
            status=choice(["ACTIVE", "ACTIVE", "UNDER_CONTROL"]),
            reported_by=list(users.values())[0].id if users else None,
            created_at=_days_ago(randint(1, 30)),
        )
        db.add(ea)
    db.flush()

    # ═══════════════════════════════════════
    # 20. ON-CALL SCHEDULES (garde)
    # ═══════════════════════════════════════
    for fc in ["CHU-DONKA", "CHU-IGNACE-DEEN", "HGR-KINDIA"]:
        fac = facilities[fc]
        staff_list = [s for s in staff.values() if s.facility_id == fac.id]
        if not staff_list:
            continue
        for day in range(1, 16):  # Next 15 days
            on_call_date = _now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day)
            for shift in ["DAY", "NIGHT"]:
                s = choice(staff_list)
                ocs = OnCallSchedule(
                    facility_id=fac.id,
                    department_id=s.department_id,
                    staff_id=s.id,
                    on_call_date=on_call_date,
                    shift_type=shift,
                    notes=f"Garde {shift.lower()} - {s.first_name} {s.last_name}",
                    created_by=list(users.values())[0].id if users else None,
                )
                db.add(ocs)
    db.flush()

    # ═══════════════════════════════════════
    # 21. ACTIVITY LOG ENTRIES
    # ═══════════════════════════════════════
    activity_actions = [
        ("LOGIN", "users", None, "NORMAL", "Connexion utilisateur"),
        ("PATIENT_CREATED", "patients", None, "NORMAL", "Création dossier patient"),
        ("ADMISSION_CREATED", "admissions", None, "NORMAL", "Nouvelle admission"),
        ("PRESCRIPTION_CREATED", "clinical", None, "NORMAL", "Prescription médicale"),
        ("LAB_ORDER_CREATED", "laboratory", None, "NORMAL", "Demande d'examen labo"),
        ("EMERGENCY_TRIAGE", "emergency", None, "URGENT", "Triage urgence réalisé"),
        ("INVOICE_CREATED", "billing", None, "NORMAL", "Facture émise"),
        ("PAYMENT_RECEIVED", "billing", None, "NORMAL", "Paiement encaissé"),
        ("SURGERY_SCHEDULED", "surgery", None, "NORMAL", "Intervention programmée"),
        ("INCIDENT_REPORTED", "quality", None, "WARNING", "Événement indésirable signalé"),
    ]
    for i in range(50):
        action = choice(activity_actions)
        user_list = list(users.values())
        ae = ActivityEntry(
            actor_id=choice(user_list).id,
            action_name=action[0],
            entity_type=action[1],
            entity_id=choice(patients).id if action[1] in ("patients", "clinical", "laboratory", "emergency") else None,
            level=action[3],
            notes=action[4],
            created_at=_days_ago(randint(0, 7)),
        )
        db.add(ae)

    db.commit()
    print("✅ Seed completed successfully with comprehensive Guinea data!")
    print(f"   - {len(facilities)} établissements")
    print(f"   - {len(users)} utilisateurs")
    print(f"   - {len(patients)} patients")
    print(f"   - {len(admissions)} admissions")
    print(f"   - {len(beds)} lits")
    print(f"   - {len(products)} produits pharmaceutiques")
    print(f"   - {len(lab_tests)} examens de laboratoire")


if __name__ == "__main__":
    run_seed()

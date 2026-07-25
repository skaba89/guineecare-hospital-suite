"""ICD-11 — Lookup des codes diagnostiques OMS — v2.9.2

L'ICD-11 (International Classification of Diseases 11th Revision) est la
classification officielle de l'OMS depuis 2022. En Guinée, le SNIS utilise
encore majoritairement la CIM-10, mais la transition vers ICD-11 est en cours.

Ce module fournit :
- Un catalogue embarqué des ~80 codes ICD-11 les plus utilisés en médecine
  hospitalière guinéenne (paludisme, hypertension, diabète, grossesse, etc.)
- Un endpoint de recherche GET /icd11/search?q=...
- Un endpoint GET /icd11/{code} pour récupérer le détail d'un code

Pour une liste complète (55 000+ codes), il faudrait brancher l'API officielle
ICD-11 (https://icd.who.int/icdapi) — non fait ici pour éviter une dépendance
externe et un token API à gérer.
"""
from __future__ import annotations

# Catalogue embarqué — sélection des codes ICD-11 les plus pertinents
# pour la pratique hospitalière guinéenne.
# Source : ICD-11 Foundation (https://icd.who.int/browse11)
# Format : (code, label FR, label EN, category)
ICD11_CATALOG: list[tuple[str, str, str, str]] = [
    # Maladies transmissibles
    ("1A00", "Choléra", "Cholera", "Infectious"),
    ("1A30", "Fièvre typhoïde", "Typhoid fever", "Infectious"),
    ("1A40", "Septicémie streptococcique", "Streptococcal sepsis", "Infectious"),
    ("1B11", "Tuberculose respiratoire", "Respiratory tuberculosis", "Infectious"),
    ("1B1Z", "Tuberculose, non précisée", "Tuberculosis, unspecified", "Infectious"),
    ("1C1Z", "Méningite bactérienne, non précisée", "Bacterial meningitis, unspecified", "Infectious"),
    ("1F03", "Paludisme à Plasmodium falciparum", "Malaria due to Plasmodium falciparum", "Infectious"),
    ("1F2Z", "Paludisme, non précisé", "Malaria, unspecified", "Infectious"),
    ("1E50", "Dengue", "Dengue", "Infectious"),
    ("1E70", "Fièvre jaune", "Yellow fever", "Infectious"),
    ("1E73", "Fièvre de Lassa", "Lassa fever", "Infectious"),
    ("1E74", "Maladie à virus Ebola", "Ebola virus disease", "Infectious"),
    ("1H0Z", "HIV à l'origine de maladies, non précisé", "HIV disease resulting in unspecified disease", "Infectious"),
    ("CA40", "Pneumonie à Streptococcus pneumoniae", "Pneumonia due to Streptococcus pneumoniae", "Respiratory"),
    ("CA4Z", "Pneumonie, agent non précisé", "Pneumonia, unspecified organism", "Respiratory"),

    # Appareil respiratoire
    ("CA08", "Rhinopharyngite aiguë", "Acute nasopharyngitis", "Respiratory"),
    ("CA20", "Bronchite aiguë", "Acute bronchitis", "Respiratory"),
    ("CA23", "Bronchiolite aiguë", "Acute bronchiolitis", "Respiratory"),
    ("CA2Z", "Bronchite aiguë, non précisée", "Acute bronchitis, unspecified", "Respiratory"),
    ("CA40.0", "Pneumonie, agent non précisé", "Pneumonia, unspecified organism", "Respiratory"),
    ("CA0Z", "Infection aiguë des voies respiratoires supérieures, non précisée", "Acute upper respiratory infection, unspecified", "Respiratory"),
    ("CB03", "Asthme", "Asthma", "Respiratory"),
    ("CB04", "Asthme persistant léger", "Mild persistent asthma", "Respiratory"),
    ("CB0Z", "Asthme, non précisé", "Asthma, unspecified", "Respiratory"),
    ("CB6Z", "Bronchopneumopathie chronique obstructive, non précisée", "Chronic obstructive pulmonary disease, unspecified", "Respiratory"),

    # Système cardiovasculaire
    ("BA00", "Hypertension essentielle", "Essential hypertension", "Cardiovascular"),
    ("BA0Z", "Hypertension, non précisée", "Hypertension, unspecified", "Cardiovascular"),
    ("BA40", "Hypertrophie ventriculaire gauche", "Left ventricular hypertrophy", "Cardiovascular"),
    ("BB71", "Insuffisance cardiaque", "Heart failure", "Cardiovascular"),
    ("BB7Z", "Insuffisance cardiaque, non précisée", "Heart failure, unspecified", "Cardiovascular"),
    ("BA81", "Cardiomyopathie hypertrophique", "Hypertrophic cardiomyopathy", "Cardiovascular"),
    ("BD10", "Endocardite aiguë", "Acute endocarditis", "Cardiovascular"),
    ("BD70", "Thrombose veineuse profonde des membres inférieurs", "Deep vein thrombosis of lower extremities", "Cardiovascular"),

    # Système digestif
    ("DA40", "Appendicite aiguë", "Acute appendicitis", "Digestive"),
    ("DA60", "Hernie inguinale, sans occlusion", "Inguinal hernia, without obstruction", "Digestive"),
    ("DA96", "Gastro-entérite et colite d'origine infectieuse", "Infectious gastroenteritis and colitis", "Digestive"),
    ("DA9Z", "Gastro-entérite, non précisée", "Gastroenteritis, unspecified", "Digestive"),
    ("DB10", "Ulcère peptique aigu", "Acute peptic ulcer", "Digestive"),
    ("DB11", "Ulcère gastrique aigu avec hémorragie", "Acute gastric ulcer with haemorrhage", "Digestive"),
    ("DC40", "Hépatite virale aiguë B", "Acute viral hepatitis B", "Digestive"),
    ("DC50", "Hépatite virale aiguë C", "Acute viral hepatitis C", "Digestive"),
    ("DC9Z", "Maladie du foie, non précisée", "Disease of liver, unspecified", "Digestive"),
    ("DD71", "Cirrhose du foie", "Cirrhosis of liver", "Digestive"),
    ("DE40", "Cholélithiase", "Cholelithiasis", "Digestive"),
    ("DE60", "Cholécystite aiguë", "Acute cholecystitis", "Digestive"),
    ("DF40", "Pancréatite aiguë", "Acute pancreatitis", "Digestive"),

    # Endocriniennes / métaboliques
    ("5A11", "Diabète sucré de type 1", "Type 1 diabetes mellitus", "Endocrine"),
    ("5A1A", "Diabète sucré de type 2", "Type 2 diabetes mellitus", "Endocrine"),
    ("5A1Z", "Diabète sucré, non précisé", "Diabetes mellitus, unspecified", "Endocrine"),
    ("5A90", "Malnutrition sévère", "Severe malnutrition", "Endocrine"),
    ("5B6Z", "Anémie ferriprive, non précisée", "Iron deficiency anaemia, unspecified", "Endocrine"),
    ("5C0Z", "Malnutrition, non précisée", "Malnutrition, unspecified", "Endocrine"),

    # Grossesse / accouchement / puerpéralité
    ("JA60", "Grossesse extra-utérine", "Ectopic pregnancy", "Pregnancy"),
    ("JA8Z", "Grossesse, non précisée", "Pregnancy, unspecified", "Pregnancy"),
    ("JB0A", "Hypertension chronique avec prééclampsie", "Chronic hypertension with pre-eclampsia", "Pregnancy"),
    ("JB01", "Prééclampsie légère à modérée", "Mild to moderate pre-eclampsia", "Pregnancy"),
    ("JB02", "Prééclampsie sévère", "Severe pre-eclampsia", "Pregnancy"),
    ("JB0Z", "Prééclampsie, non précisée", "Pre-eclampsia, unspecified", "Pregnancy"),
    ("JC1Z", "Hémorragie de la grossesse, non précisée", "Haemorrhage of pregnancy, unspecified", "Pregnancy"),
    ("JC24", "Hémorragie post-partum immédiate", "Immediate postpartum haemorrhage", "Pregnancy"),
    ("JC8Z", "Accouchement, non précisé", "Delivery, unspecified", "Pregnancy"),
    ("JD24", "Lésion obstétricale du périnée", "Obstetric perineal laceration", "Pregnancy"),
    ("JE10", "Syphilis maternelle affectant la grossesse", "Maternal syphilis affecting pregnancy", "Pregnancy"),
    ("JE11", "VIH maternel affectant la grossesse", "Maternal HIV affecting pregnancy", "Pregnancy"),
    ("JF00", "Fœtus et nouveau-né affectés par une hypertension maternelle", "Fetus and newborn affected by maternal hypertension", "Pregnancy"),

    # Périnatal
    ("KA05", "Hémorragie intraventriculaire du fœtus et du nouveau-né", "Intraventricular haemorrhage of fetus and newborn", "Perinatal"),
    ("KA2Z", "Infection néonatale, non précisée", "Neonatal infection, unspecified", "Perinatal"),
    ("KA8Z", "Naissance prématurée, non précisée", "Preterm birth, unspecified", "Perinatal"),

    # Système nerveux
    ("8A00", "Migraine", "Migraine", "Neurological"),
    ("8A20", "Épilepsie", "Epilepsy", "Neurological"),
    ("8A4Z", "Céphalée, non précisée", "Headache, unspecified", "Neurological"),
    ("8B40", "Accident vasculaire cérébral ischémique", "Ischaemic stroke", "Neurological"),
    ("8B45", "Accident vasculaire cérébral hémorragique", "Haemorrhagic stroke", "Neurological"),
    ("8B4Z", "Accident vasculaire cérébral, non précisé", "Cerebral stroke, unspecified", "Neurological"),
    ("8C40", "Coma", "Coma", "Neurological"),

    # Santé mentale
    ("6A70", "Episode dépressif unique", "Single depressive episode", "Mental"),
    ("6A71", "Episode dépressif récurrent", "Recurrent depressive disorder", "Mental"),
    ("6A7Z", "Dépression, non précisée", "Depression, unspecified", "Mental"),
    ("6A60", "Anxiété généralisée", "Generalised anxiety disorder", "Mental"),
    ("6A80", "Trouble bipolaire de type I", "Bipolar disorder type I", "Mental"),

    # Système génito-urinaire
    ("GC0Z", "Infection urinaire, non précisée", "Urinary tract infection, unspecified", "Genitourinary"),
    ("GB81", "Néphrite syndrome", "Nephritic syndrome", "Genitourinary"),
    ("GB9Z", "Maladie du rein, non précisée", "Kidney disease, unspecified", "Genitourinary"),
    ("GA40", "Hydronéphrose", "Hydronephrosis", "Genitourinary"),
    ("GA11", "Hyperplasie bénigne de la prostate", "Benign prostatic hyperplasia", "Genitourinary"),

    # Peau
    ("EA80", "Impétigo", "Impetigo", "Skin"),
    ("EA8Z", "Infection cutanée, non précisée", "Skin infection, unspecified", "Skin"),
    ("EA0Z", "Dermatite, non précisée", "Dermatitis, unspecified", "Skin"),
    ("EB10", "Urticaire", "Urticaria", "Skin"),

    # Lésions / traumatismes
    ("NA01", "Fracture fermée de l'os cranien", "Closed fracture of cranial bone", "Injury"),
    ("NA0Z", "Fracture du crâne, non précisée", "Fracture of skull, unspecified", "Injury"),
    ("NB00", "Fracture fermée de la clavicule", "Closed fracture of clavicle", "Injury"),
    ("NB4Z", "Fracture du membre supérieur, non précisée", "Fracture of upper limb, unspecified", "Injury"),
    ("NC50", "Fracture fermée du fémur", "Closed fracture of femur", "Injury"),
    ("NC5Z", "Fracture du membre inférieur, non précisée", "Fracture of lower limb, unspecified", "Injury"),
    ("ND0Z", "Brûlure, non précisée", "Burn, unspecified", "Injury"),
    ("ND1Z", "Brûlure thermique, non précisée", "Thermal burn, unspecified", "Injury"),
    ("PA60", "Polytraumatisme", "Polytrauma", "Injury"),

    # Causes externes
    ("XE0V", "Accident de transport — véhicule à moteur", "Transport accident — motor vehicle", "External"),
    ("XE5Z", "Chute, non précisée", "Fall, unspecified", "External"),
]


def search_icd11(query: str, limit: int = 20) -> list[dict]:
    """Recherche fuzzy dans le catalogue ICD-11.

    Args:
        query: texte recherché (code ou label, FR ou EN)
        limit: nombre max de résultats (défaut 20)

    Returns:
        Liste de dicts {code, label_fr, label_en, category}
    """
    q = query.lower().strip()
    if not q:
        return []

    results: list[tuple[int, dict]] = []
    for code, fr, en, cat in ICD11_CATALOG:
        # Score simple : match code = 100, début label = 80, label contient = 50
        score = 0
        if code.lower() == q:
            score = 100
        elif code.lower().startswith(q):
            score = 90
        elif fr.lower().startswith(q):
            score = 80
        elif en.lower().startswith(q):
            score = 75
        elif q in fr.lower():
            score = 50
        elif q in en.lower():
            score = 45

        if score > 0:
            results.append((score, {
                "code": code,
                "label_fr": fr,
                "label_en": en,
                "category": cat,
            }))

    # Trier par score décroissant, puis par code
    results.sort(key=lambda x: (-x[0], x[1]["code"]))
    return [r[1] for r in results[:limit]]


def get_icd11_by_code(code: str) -> dict | None:
    """Récupère le détail d'un code ICD-11.

    Returns:
        {code, label_fr, label_en, category} ou None si code non trouvé.
    """
    code_upper = code.upper().strip()
    for c, fr, en, cat in ICD11_CATALOG:
        if c == code_upper:
            return {
                "code": c,
                "label_fr": fr,
                "label_en": en,
                "category": cat,
            }
    return None


def list_icd11_categories() -> list[str]:
    """Liste les catégories disponibles dans le catalogue."""
    return sorted({cat for _, _, _, cat in ICD11_CATALOG})

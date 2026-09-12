import re
import pandas as pd

# Liste officielle des groupes sanguins valides
VALID_BLOOD_TYPES = {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'}


def clean_person_name(raw_name: str, stats: dict, field_key: str):
    """
    Normalise le nom d'une personne (patient ou médecin) :
    1. Conserve toutes les informations (y compris les civilités et titres médicaux).
    2. Nettoie la ponctuation parasite (virgules) et les espaces multiples.
    3. Corrige la casse anarchique pour appliquer un format Title Case uniforme.
    4. Incrémente le compteur de statistiques si le texte a été retouché.
    5. Retourne None (valeur BSON null dans MongoDB) si la valeur est manquante.
    
    Exemples de transformation :
        - "mR. DAVID pIERce Md"      --> "Mr. David Pierce Md"
        - "dr. KAtIe baRReTt DVM"    --> "Dr. Katie Barrett Dvm"
        - "EDWArd JOneS jR."         --> "Edward Jones Jr."
        - "NaN" / None / ""          --> None (stocké en null)
    """
    if pd.isna(raw_name):
        return None
    
    original = str(raw_name)
    
    # Nettoyage des virgules résiduelles et espaces multiples
    cleaned = re.sub(r'[\s,]+', ' ', original).strip()
    result = cleaned.title() if cleaned else None

    # Audit : Si le texte final diffère de l'original brut (hors espaces), on incrémente
    if pd.notna(result) and original.strip() != result:
        stats[field_key] += 1

    return result


def clean_hospital_name(raw_hospital: str, stats: dict):
    """
    Nettoie les artefacts de saisie dans le nom des établissements hospitaliers :
    - Supprime les guillemets et virgules parasites en début/fin de chaîne.
    - Uniformise les espaces multiples.
    - Applique le format Title Case.
    - Incrémente le compteur si une correction a été appliquée.
    - Retourne None (null dans MongoDB) si le champ est vide ou absent.
    """
    if pd.isna(raw_hospital):
        return None
    
    original = str(raw_hospital)
    cleaned = original.strip(' ,"\'')
    cleaned = re.sub(r'^[,\s]+|[,\s]+$', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    result = cleaned.title() if cleaned else None

    # Audit : Suivi des hôpitaux nettoyés
    if pd.notna(result) and original.strip() != result:
        stats["hopitaux_nettoyes"] += 1

    return result


def load_and_clean_data(csv_path: str) -> pd.DataFrame:
    """
    Pipeline ETL complet de nettoyage et de validation des données médicales.
    """
    print(f"Extraction des données brutes depuis : {csv_path}")
    df = pd.read_csv(csv_path)
    initial_count = len(df)

    # Dictionnaire de métriques pour le rapport d'audit détaillé
    audit = {
        "doublons_supprimes": 0,
        "noms_patients_nettoyes": 0,
        "medecins_nettoyes": 0,
        "hopitaux_nettoyes": 0,
        "categories_nettoyees": 0,
        "groupes_sanguins_corriges_majuscules": 0,
        "montants_negatifs_null": 0,
        "montants_invalides_null": 0,
        "dates_sortie_incoherentes_null": 0,
        "ages_invalides_null": 0,
        "chambres_invalides_null": 0,
        "noms_patients_null": 0,
        "medecins_null": 0,
        "hopitaux_null": 0,
        "groupes_sanguins_invalides_null": 0,
        "dates_admission_invalides_null": 0,
        "dates_sortie_invalides_null": 0
    }

    # -------------------------------------------------------------------------
    # 1. NORMALISATION DES NOMS DE COLONNES
    # -------------------------------------------------------------------------
    df.columns = [
        col.strip()
           .lower()
           .replace(' ', '_')
           .replace('-', '_') 
        for col in df.columns
    ]

    # -------------------------------------------------------------------------
    # 2. SUPPRESSION STRICTE DES DOUBLONS PARFAITS
    # -------------------------------------------------------------------------
    nb_doublons = df.duplicated().sum()
    audit["doublons_supprimes"] = int(nb_doublons)
    if nb_doublons > 0:
        df.drop_duplicates(inplace=True)

    # -------------------------------------------------------------------------
    # 3. NETTOYAGE TEXTUEL ET VALEURS CATÉGORIELLES (AVEC AUDIT)
    # -------------------------------------------------------------------------
    df['name'] = df['name'].apply(lambda x: clean_person_name(x, audit, "noms_patients_nettoyes"))
    audit["noms_patients_null"] = int(df['name'].isna().sum())

    df['doctor'] = df['doctor'].apply(lambda x: clean_person_name(x, audit, "medecins_nettoyes"))
    audit["medecins_null"] = int(df['doctor'].isna().sum())

    df['hospital'] = df['hospital'].apply(lambda x: clean_hospital_name(x, audit))
    audit["hopitaux_null"] = int(df['hospital'].isna().sum())

    # Normalisation des variables catégorielles (Title Case)
    categorical_cols = [
        'gender', 'medical_condition', 'insurance_provider', 
        'admission_type', 'medication', 'test_results'
    ]
    for col in categorical_cols:
        if col in df.columns:
            def clean_cat(val):
                if pd.isna(val) or str(val).strip().lower() in ['', 'nan', 'none', 'null']:
                    return None
                orig = str(val)
                res = orig.strip().title()
                if orig != res:
                    audit["categories_nettoyees"] += 1
                return res
            df[col] = df[col].apply(clean_cat)

    # Validation et normalisation du groupe sanguin en majuscules
    def validate_and_correct_blood_type(val):
        if pd.isna(val) or str(val).strip().lower() in ['', 'nan', 'none', 'null']:
            return None
        orig = str(val).strip()
        formatted = orig.upper()
        if formatted in VALID_BLOOD_TYPES:
            if orig != formatted:
                audit["groupes_sanguins_corriges_majuscules"] += 1
            return formatted
        else:
            audit["groupes_sanguins_invalides_null"] += 1
            return None

    if 'blood_type' in df.columns:
        df['blood_type'] = df['blood_type'].apply(validate_and_correct_blood_type)

    # -------------------------------------------------------------------------
    # 4. VALIDATION NUMÉRIQUE ET RÈGLES MÉTIER COMPTABLES
    # -------------------------------------------------------------------------
    age_numeric = pd.to_numeric(df['age'], errors='coerce')
    invalid_age_mask = (age_numeric.isna()) | (age_numeric < 0) | (age_numeric > 125)
    audit["ages_invalides_null"] = int(invalid_age_mask.sum())
    df['age'] = age_numeric.mask(invalid_age_mask, None)

    room_numeric = pd.to_numeric(df['room_number'], errors='coerce')
    invalid_room_mask = (room_numeric.isna()) | (room_numeric <= 0)
    audit["chambres_invalides_null"] = int(invalid_room_mask.sum())
    df['room_number'] = room_numeric.mask(invalid_room_mask, None)

    # Traitement des montants de facturation négatifs (mis à null)
    billing_numeric = pd.to_numeric(df['billing_amount'], errors='coerce')
    neg_billing_mask = billing_numeric < 0
    nan_billing_mask = billing_numeric.isna()

    audit["montants_negatifs_null"] = int(neg_billing_mask.sum())
    audit["montants_invalides_null"] = int(nan_billing_mask.sum())

    billing_numeric = billing_numeric.mask(neg_billing_mask | nan_billing_mask, None)
    df['billing_amount'] = billing_numeric.apply(lambda x: round(x, 2) if pd.notna(x) else None)

    # -------------------------------------------------------------------------
    # 5. COHÉRENCE TEMPORELLE ET FEATURE ENGINEERING
    # -------------------------------------------------------------------------
    df['date_of_admission'] = pd.to_datetime(df['date_of_admission'], errors='coerce')
    df['discharge_date'] = pd.to_datetime(df['discharge_date'], errors='coerce')

    audit["dates_admission_invalides_null"] = int(df['date_of_admission'].isna().sum())
    audit["dates_sortie_invalides_null"] = int(df['discharge_date'].isna().sum())

    # Incohérence métier : date de sortie antérieure à l'admission convertie en null
    incoherent_dates_mask = (
        df['date_of_admission'].notna() &
        df['discharge_date'].notna() &
        (df['discharge_date'] < df['date_of_admission'])
    )
    audit["dates_sortie_incoherentes_null"] = int(incoherent_dates_mask.sum())
    df.loc[incoherent_dates_mask, 'discharge_date'] = pd.NaT

    # Enrichissement : calcul de la durée du séjour en jours
    df['length_of_stay_days'] = (df['discharge_date'] - df['date_of_admission']).dt.days
    df['length_of_stay_days'] = df['length_of_stay_days'].apply(lambda x: int(x) if pd.notna(x) else None)

    # Formatage final des dates en chaînes normalisées ISO-8601
    df['date_of_admission'] = df['date_of_admission'].dt.strftime('%Y-%m-%d')
    df['discharge_date'] = df['discharge_date'].dt.strftime('%Y-%m-%d')

    # Cast sécurisé des entiers pour accepter les None
    df['age'] = df['age'].apply(lambda x: int(x) if pd.notna(x) else None)
    df['room_number'] = df['room_number'].apply(lambda x: int(x) if pd.notna(x) else None)

    # Remplacement global des NaN résiduels par None (BSON null)
    df = df.where(pd.notnull(df), None)

    # -------------------------------------------------------------------------
    # 6. RAPPORT D'AUDIT DÉTAILLÉ DANS LES LOGS
    # -------------------------------------------------------------------------
    print("=" * 65)
    print("RAPPORT D'AUDIT QUALITÉ : NETTOYAGES ET CORRECTIONS APPLIQUÉS")
    print("=" * 65)
    print(f"- Lignes brutes initiales              : {initial_count}")
    print(f"- Doublons parfaits supprimés          : {audit['doublons_supprimes']}")
    print(f"- Lignes finales conservées            : {len(df)}")
    print("-" * 65)
    print("Détail des données RETOUCHÉES / CORRIGÉES :")
    print(f"  * Noms de patients mis propres       : {audit['noms_patients_nettoyes']}")
    print(f"  * Noms de médecins mis propres       : {audit['medecins_nettoyes']}")
    print(f"  * Noms d'hôpitaux nettoyés           : {audit['hopitaux_nettoyes']}")
    print(f"  * Valeurs catégorielles normalisées  : {audit['categories_nettoyees']}")
    print(f"  * Groupes sanguins passés en majuscules: {audit['groupes_sanguins_corriges_majuscules']}")
    print("-" * 65)
    print("Détail des anomalies transformées en NULL (None) :")
    print(f"  * Dates de sortie < date d'entrée    : {audit['dates_sortie_incoherentes_null']}")
    print(f"  * Montants de facturation négatifs   : {audit['montants_negatifs_null']}")
    print(f"  * Montants de facturation non saisis : {audit['montants_invalides_null']}")
    print(f"  * Groupes sanguins invalides         : {audit['groupes_sanguins_invalides_null']}")
    print(f"  * Noms de patients manquants         : {audit['noms_patients_null']}")
    print(f"  * Médecins manquants                 : {audit['medecins_null']}")
    print(f"  * Hôpitaux manquants                 : {audit['hopitaux_null']}")
    print(f"  * Âges invalides ou hors limites     : {audit['ages_invalides_null']}")
    print(f"  * Numéros de chambre invalides       : {audit['chambres_invalides_null']}")
    print(f"  * Dates d'admission non lisibles     : {audit['dates_admission_invalides_null']}")
    print(f"  * Dates de sortie non lisibles       : {audit['dates_sortie_invalides_null']}")
    print("=" * 65)

    return df


def migrate_data(collection, df: pd.DataFrame):
    """
    Orchestre le chargement des données nettoyées dans MongoDB :
    1. Réinitialise la collection existante pour éviter les doublons inter-runs.
    2. Crée les index de performance sur les champs les plus sollicités en lecture.
    3. Effectue une insertion en masse (bulk insert) pour maximiser le débit réseau.
    """
    collection.delete_many({})
    
    collection.create_index("name")
    collection.create_index("medical_condition")
    collection.create_index("date_of_admission")

    records = df.to_dict(orient='records')
    if records:
        collection.insert_many(records)
        
    print(f"Migration validée : {len(records)} documents insérés dans MongoDB.")
import re
import pandas as pd

def clean_person_name(raw_name: str):
    """
    Normalise le nom d'une personne (patient ou médecin) :
    1. Supprime les préfixes de civilité et titres honorifiques/médicaux (Mr, Mrs, Dr, MD, DDS, PhD, DVM...).
    2. Supprime les suffixes générationnels (Jr, II, III...).
    3. Corrige la casse anarchique pour appliquer un format Title Case uniforme.
    4. Retourne None (valeur BSON null dans MongoDB) si la valeur est manquante ou vide.
    
    Exemples de transformation :
        - "mR. DAVID pIERce Md"      --> "David Pierce"
        - "dr. KAtIe baRReTt DVM"    --> "Katie Barrett"
        - "EDWArd JOneS jR."         --> "Edward Jones"
        - "Taylor howeLl Dds"        --> "Taylor Howell"
        - "NaN" / None / ""          --> None (stocké en null)
    """
    if pd.isna(raw_name):
        return None
    
    # Regex ciblant les acronymes et titres isolés par des frontières de mot (\b)
    # Les titres peuvent comporter ou non un point terminal (ex: "Dr." ou "Dr")
    pattern = r'\b(mr|mrs|ms|dr|miss|md|dds|phd|dvm|jr|ii|iii)\b\.?'
    cleaned = re.sub(pattern, '', str(raw_name), flags=re.IGNORECASE)
    
    # Nettoyage des virgules résiduelles et espaces multiples (ex: "Jones , Jr" -> "Jones")
    cleaned = re.sub(r'[\s,]+', ' ', cleaned).strip()
    
    # Mise en majuscule de la première lettre de chaque mot (Title Case) ou None si vide
    return cleaned.title() if cleaned else None


def clean_hospital_name(raw_hospital: str):
    """
    Nettoie les artefacts de saisie dans le nom des établissements hospitaliers :
    - Supprime les guillemets et virgules parasites en début/fin de chaîne.
    - Uniformise les espaces multiples.
    - Applique le format Title Case.
    - Retourne None (null dans MongoDB) si le champ est vide ou absent.
    
    Exemples de transformation :
        - '"Hernandez Rogers and Vang,"'    --> "Hernandez Rogers And Vang"
        - '"and Garcia Morris Cunningham,"' --> "And Garcia Morris Cunningham"
        - "  Group   Middleton  "           --> "Group Middleton"
        - None / NaN / ""                   --> None (stocké en null)
    """
    if pd.isna(raw_hospital):
        return None
    
    # Suppression des guillemets, virgules et espaces en bordure
    cleaned = str(raw_hospital).strip(' ,"\'')
    
    # Suppression des virgules ou espaces résiduels aux extrémités
    cleaned = re.sub(r'^[,\s]+|[,\s]+$', '', cleaned)
    
    # Réduction des espaces multiples consécutifs en un seul espace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.title() if cleaned else None


def load_and_clean_data(csv_path: str) -> pd.DataFrame:
    """
    Pipeline ETL complet de nettoyage et de validation des données médicales :
    
    Contrôles et règles appliqués :
    --------------------------------
    1. Schema Standardization :
       - Conversion des en-têtes en snake_case strict (ex: "Blood Type" -> "blood_type").
    
    2. Data Completeness & Integrity :
       - Suppression des lignes sans identifiant patient ('name') ou sans date d'admission.
       - Déduplication complète des enregistrements strictement identiques.
    
    3. String Normalization :
       - Nettoyage des titres et de la casse sur les patients et médecins via regex.
       - Nettoyage syntaxique des noms d'hôpitaux.
       - Uniformisation en Title Case des variables catégorielles (diagnostic, assurance, médicaments).
       - Passage systématique en majuscules du groupe sanguin (ex: "ab-" -> "AB-").
       - Remplacement des valeurs manquantes textuelles par None (BSON null).
    
    4. Numeric Integrity & Business Rules :
       - Typage explicite des âges et numéros de chambre en entiers.
       - Correction des montants de facturation négatifs (anomalie fréquente en compta, ex: -502.50 -> 502.50).
       - Arrondi des montants à 2 décimales pour respecter la précision monétaire.
    
    5. Temporal Consistency & Feature Engineering :
       - Parsing des dates d'admission et de sortie au format datetime.
       - Exclusion des anomalies métier où Date de sortie < Date d'admission.
       - Création d'une métrique métier dérivée : 'length_of_stay_days' (durée d'hospitalisation en jours).
       - Conversion finale des dates au format standard ISO ("YYYY-MM-DD") ou None si manquantes.
    """
    print(f"Extraction des données brutes depuis : {csv_path}")
    df = pd.read_csv(csv_path)
    initial_count = len(df)

    # -------------------------------------------------------------------------
    # 1. NORMALISATION DES NOMS DE COLONNES
    # -------------------------------------------------------------------------
    # Objectif : Remplacer les espaces et tirets par des underscores, tout en minuscules.
    # Exemple : "Medical Condition" --> "medical_condition"
    df.columns = [
        col.strip()
           .lower()
           .replace(' ', '_')
           .replace('-', '_') 
        for col in df.columns
    ]

    # -------------------------------------------------------------------------
    # 2. DÉDUPLICATION ET INTÉGRITÉ CRITIQUE
    # -------------------------------------------------------------------------
    # Un dossier médical sans nom de patient ou sans date d'entrée est inexploitable.
    df.dropna(subset=['name', 'date_of_admission'], inplace=True)
    
    # Suppression des doublons parfaits (lignes dupliquées lors d'extractions multiples)
    df.drop_duplicates(inplace=True)

    # -------------------------------------------------------------------------
    # 3. NETTOYAGE TEXTUEL ET VALEURS CATÉGORIELLES
    # -------------------------------------------------------------------------
    # Application des fonctions regex spécialisées (renvoient None si invalide)
    df['name'] = df['name'].apply(clean_person_name)
    df['doctor'] = df['doctor'].apply(clean_person_name)
    df['hospital'] = df['hospital'].apply(clean_hospital_name)

    # Normalisation des variables à vocabulaire contrôlé en Title Case
    # Si la valeur est manquante ou vide, elle est positionnée à None
    # Exemples : "cancer" -> "Cancer", "URGENT" -> "Urgent", NaN -> None
    categorical_cols = [
        'gender', 'medical_condition', 'insurance_provider', 
        'admission_type', 'medication', 'test_results'
    ]
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: str(x).strip().title() 
                if pd.notna(x) and str(x).strip() not in ['', 'nan', 'none', 'null'] 
                else None
            )

    # Le groupe sanguin suit une convention internationale en majuscules
    # Exemples : "ab+" -> "AB+", "o-" -> "O-", NaN -> None
    if 'blood_type' in df.columns:
        df['blood_type'] = df['blood_type'].apply(
            lambda x: str(x).strip().upper() 
            if pd.notna(x) and str(x).strip() not in ['', 'nan', 'none', 'null'] 
            else None
        )

    # -------------------------------------------------------------------------
    # 4. VALIDATION NUMÉRIQUE ET RÈGLES MÉTIER COMPTABLES
    # -------------------------------------------------------------------------
    # Cast en entier sécurisé (coerce transforme les chaînes invalides en NaN, gérées par fillna)
    df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0).astype(int)
    df['room_number'] = pd.to_numeric(df['room_number'], errors='coerce').fillna(0).astype(int)

    # Anomalie détectée : montants négatifs (ex: -1018.2453712282881 ou -306.3649)
    # Traitement : passage en valeur absolue (.abs()) et arrondi monétaire standard (.round(2))
    # Exemple : -502.5078127... --> 502.51
    df['billing_amount'] = (
        pd.to_numeric(df['billing_amount'], errors='coerce')
        .fillna(0.0)
        .abs()
        .round(2)
    )

    # -------------------------------------------------------------------------
    # 5. COHÉRENCE TEMPORELLE ET FEATURE ENGINEERING
    # -------------------------------------------------------------------------
    # Conversion en objets datetime pour permettre les comparaisons et calculs arithmétiques
    df['date_of_admission'] = pd.to_datetime(df['date_of_admission'], errors='coerce')
    df['discharge_date'] = pd.to_datetime(df['discharge_date'], errors='coerce')

    # Règle de cohérence temporelle : la date de sortie ne peut pas précéder l'admission
    # Exemple d'incohérence rejetée : Entrée le 2024-02-10 et Sortie le 2024-02-05
    invalid_dates_mask = df['discharge_date'] < df['date_of_admission']
    if invalid_dates_mask.any():
        nb_invalides = invalid_dates_mask.sum()
        print(f"Alerte : {nb_invalides} enregistrement(s) avec date de sortie antérieure à l'entrée supprimé(s).")
        df = df[~invalid_dates_mask]

    # Enrichissement : calcul du nombre de jours passés à l'hôpital
    # Exemple : Entrée 2024-01-31, Sortie 2024-02-02 --> 2 jours
    df['length_of_stay_days'] = (df['discharge_date'] - df['date_of_admission']).dt.days

    # Formatage final des dates en chaînes normalisées ISO-8601 pour l'ingestion NoSQL
    # dt.strftime applique None si la valeur temporelle est NaT
    df['date_of_admission'] = df['date_of_admission'].dt.strftime('%Y-%m-%d')
    df['discharge_date'] = df['discharge_date'].dt.strftime('%Y-%m-%d')

    # Remplacement global de tous les NaN / NaT résiduels par None
    # Cela permet à PyMongo d'enregistrer un vrai champ BSON null plutôt que des NaN flottants
    df = df.where(pd.notnull(df), None)

    cleaned_count = len(df)
    print(f"Nettoyage terminé avec succès : {cleaned_count}/{initial_count} enregistrements qualifiés conservés.")
    return df


def migrate_data(collection, df: pd.DataFrame):
    """
    Orchestre le chargement des données nettoyées dans MongoDB :
    1. Réinitialise la collection existante pour éviter les doublons inter-runs.
    2. Crée les index de performance sur les champs les plus sollicités en lecture.
    3. Effectue une insertion en masse (bulk insert) pour maximiser le débit réseau.
    """
    # Purge complète de la collection pour garantir une ingestion idempotente
    collection.delete_many({})
    
    # Création d'index pour accélérer les requêtes d'agrégation et de recherche
    collection.create_index("name")
    collection.create_index("medical_condition")
    collection.create_index("date_of_admission")

    # Transformation du DataFrame en liste de dictionnaires (avec None traduits en null)
    records = df.to_dict(orient='records')
    
    if records:
        # Insertion en masse (nettement plus performant que des insert_one unitaires)
        collection.insert_many(records)
        
    print(f"Migration validée : {len(records)} documents insérés dans la base.")
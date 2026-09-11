import os
from database import get_mongo_client
from utils import load_and_clean_data, migrate_data
from test import test_crud

def main():
    csv_path = os.getenv("CSV_PATH", "src/data/healthcare_dataset.csv")

    # Connexion à MongoDB
    client = get_mongo_client()
    db = client['medical_db']
    collection = db['patients']

    # Phase 1 & 2 : Extraction et Nettoyage
    df_cleaned = load_and_clean_data(csv_path)

    # Phase 3 : Chargement
    migrate_data(collection, df_cleaned)

    # Phase 4 : Tests de validation CRUD
    test_crud(collection)

if __name__ == "__main__":
    main()
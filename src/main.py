import os
from database import get_mongo_client
from utils import load_and_clean_data, migrate_data
from test import test_crud

def main():
    csv_path = os.getenv("CSV_PATH", "src/data/healthcare_dataset.csv")

    # Connexion et sélection de la collection
    client = get_mongo_client()
    db = client['medical_db']
    collection = db['patients']

    # Chargement, nettoyage et migration
    df = load_and_clean_data(csv_path)
    migrate_data(collection, df)

    # Tests de validation CRUD
    test_crud(collection)

if __name__ == "__main__":
    main()
import os
from utils import get_mongo_client, load_and_clean_data, migrate_data
from test import test_crud

def main():
    csv_path = os.getenv("CSV_PATH", "src/data/healthcare_dataset.csv")

    # cibler la base medical_db et la collection patients
    client = get_mongo_client()
    db = client['medical_db']
    collection = db['patients']

    df = load_and_clean_data(csv_path)
    migrate_data(collection, df)

    # puis déclenche la fonction de test CRUD
    test_crud(collection)

if __name__ == "__main__":
    main()
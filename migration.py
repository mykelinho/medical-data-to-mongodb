import os
import pandas as pd
from pymongo import MongoClient


def test_crud(collection):
    print("--- Lancement des tests CRUD ---")
    # insertion d'un faux patient de test (insert_one)
    collection.insert_one({"Name": "Patient Test", "Age": 30, "Medical Condition": "Aucune"})
    print("CREATE OK")
    # mettre à jour l'âge de ce patient de test (update_one)
    collection.update_one({"Name": "Patient Test"}, {"$set": {"Age": 31}})
    print("UPDATE OK")
    # supprimer le document de test de la base (delete_one).
    collection.delete_one({"Name": "Patient Test"})
    print("DELETE OK")

def main():
    csv_path = os.getenv("CSV_PATH", "/app/data/healthcare_dataset.csv")
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:admin@mongodb:27017/?authSource=admin")

    # Chargement du fichier via Pandas (pd.read_csv)
    print("Lecture du fichier CSV...")
    df = pd.read_csv(csv_path)
    
    # supprimer les lignes dont le champ Name est vide (dropna)
    # et remplacer les autres cellules vides par la mention "Inconnu" (fillna).
    df.dropna(subset=['Name'], inplace=True)
    df.fillna(None, inplace=True)
    
    #établir la connexion avec MongoDB
    #cibler la base medical_db et la collection patients
    print("Connexion à MongoDB...")
    client = MongoClient(mongo_uri)
    db = client['medical_db']
    collection = db['patients']
    
    # creation d'un index sur le champ Name pour optimiser les performances de recherche
    collection.create_index("Name")
    
    # puis vider la collection existante (delete_many({})) pour effectuer une migration propre
    collection.delete_many({})

    # transformer le DataFrame Pandas en une liste de dictionnaires (orient='records')
    # et les insère en un seul bloc (insert_many)
    records = df.to_dict(orient='records')
    collection.insert_many(records)
    print(f"Migration réussie : {len(records)} patients intégrés.")

    # puis déclenche la fonction de test CRUD
    test_crud(collection)

if __name__ == "__main__":
    main()
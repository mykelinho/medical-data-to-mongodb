import os
import pandas as pd
from pymongo import MongoClient

def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:admin@mongodb:27017/?authSource=admin")
    # établir la connexion avec MongoDB
    print("Connexion à MongoDB...")
    client = MongoClient(mongo_uri)
    return client

def load_and_clean_data(csv_path):
    # Chargement du fichier via Pandas (pd.read_csv)
    print("Lecture du fichier CSV...")
    df = pd.read_csv(csv_path)
    
    # supprimer les lignes dont le champ Name est vide (dropna)
    # et remplacer les autres cellules vides par la mention "Inconnu" (fillna).
    df.dropna(subset=['Name'], inplace=True)
    df.fillna("Inconnu", inplace=True)
    return df

def migrate_data(collection, df):
    # creation d'un index sur le champ Name pour optimiser les performances de recherche
    collection.create_index("Name")
    
    # puis vider la collection existante (delete_many({})) pour effectuer une migration propre
    collection.delete_many({})

    # transformer le DataFrame Pandas en une liste de dictionnaires (orient='records')
    # et les insère en un seul bloc (insert_many)
    records = df.to_dict(orient='records')
    collection.insert_many(records)
    print(f"Migration réussie : {len(records)} patients intégrés.")
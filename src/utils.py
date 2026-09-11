import pandas as pd

def load_and_clean_data(csv_path):
    print("Lecture du fichier CSV...")
    df = pd.read_csv(csv_path)
    
    # Nettoyage des données
    df.dropna(subset=['Name'], inplace=True)
    df.fillna("Inconnu", inplace=True)
    return df

def migrate_data(collection, df):
    # Création de l'index et réinitialisation de la collection
    collection.create_index("Name")
    collection.delete_many({})

    # Insertion en masse
    records = df.to_dict(orient='records')
    collection.insert_many(records)
    print(f"Migration réussie : {len(records)} patients intégrés.")
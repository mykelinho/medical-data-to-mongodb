import os
from database import get_mongo_client, setup_database_roles
from utils import load_and_clean_data, migrate_data
from test import test_crud

def main():
    # Étape 1 : Créer les utilisateurs et leurs accès s'ils n'existent pas encore
    setup_database_roles()

    # Étape 2 : Indiquer où se trouve le fichier CSV de données médicales
    csv_path = os.getenv("CSV_PATH", "src/data/healthcare_dataset.csv")

    # Étape 3 : Se connecter à MongoDB et choisir la table des patients
    client = get_mongo_client()
    db = client['medical_db']
    collection = db['patients']

    # Étape 4 : Charger le CSV et nettoyer toutes les erreurs (doublons, dates incohérentes...)
    df_cleaned = load_and_clean_data(csv_path)

    # Étape 5 : Envoyer toutes les données propres dans MongoDB
    migrate_data(collection, df_cleaned)

    # Étape 6 : Faire un test rapide (ajouter, lire, modifier, supprimer un faux patient) pour vérifier que tout marche
    test_crud(collection)

# Lance le programme automatiquement si on exécute ce fichier
if __name__ == "__main__":
    main()
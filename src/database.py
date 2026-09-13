import os
from pymongo import MongoClient

def get_mongo_client():
    # Récupère l'adresse de MongoDB définie dans Docker (ou prend celle par défaut)
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:admin@mongodb:27017/?authSource=admin")
    # Ouvre et renvoie la connexion vers la base de données
    return MongoClient(mongo_uri)

def setup_database_roles():
    # 1. Connexion avec le compte administrateur principal
    client = get_mongo_client()
    db = client["medical_db"]

    # 2. Récupère la liste des utilisateurs qui existent déjà
    # Cela évite que le script plante si on le relance plusieurs fois
    existing_users = [u["user"] for u in db.command("usersInfo")["users"]]

    # 3. Création du compte pour le script de migration (droits de lire et d'écrire des données)
    if "etl_user" not in existing_users:
        db.command(
            "createUser", "etl_user",
            pwd="etl_password",
            roles=[{"role": "readWrite", "db": "medical_db"}]
        )
        print("[SÉCURITÉ] Utilisateur etl_user créé (lecture et écriture).")

    # 4. Création du compte pour les soignants ou analystes (lecture seule, impossible de modifier)
    if "reader_user" not in existing_users:
        db.command(
            "createUser", "reader_user",
            pwd="reader_password",
            roles=[{"role": "read", "db": "medical_db"}]
        )
        print("[SÉCURITÉ] Utilisateur reader_user créé (lecture seule).")

    # 5. Ferme la connexion une fois terminé
    client.close()
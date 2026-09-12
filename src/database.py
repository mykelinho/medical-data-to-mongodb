from pymongo import MongoClient

def setup_database_roles():
    # 1. Connexion en tant que super-admin
    admin_uri = "mongodb://admin:admin@mongodb:27017/?authSource=admin"
    client = MongoClient(admin_uri)
    db = client["medical_db"]

    # 2. Liste des utilisateurs existants pour éviter les erreurs d'exécution multiple
    existing_users = [u["user"] for u in db.command("usersInfo")["users"]]

    # 3. Création du compte applicatif ETL (lecture/écriture)
    if "etl_user" not in existing_users:
        db.command(
            "createUser", "etl_user",
            pwd="etl_password",
            roles=[{"role": "readWrite", "db": "medical_db"}]
        )
        print("[SÉCURITÉ] Utilisateur etl_user créé (readWrite).")

    # 4. Création du compte consultation (lecture seule)
    if "reader_user" not in existing_users:
        db.command(
            "createUser", "reader_user",
            pwd="reader_password",
            roles=[{"role": "read", "db": "medical_db"}]
        )
        print("[SÉCURITÉ] Utilisateur reader_user créé (read).")

    client.close()
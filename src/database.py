import os
from pymongo import MongoClient

def get_mongo_client():
    # Connexion administrateur via l'URI définie dans Docker Compose
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:admin@mongodb:27017/?authSource=admin")
    return MongoClient(mongo_uri)

def setup_database_roles():
    client = get_mongo_client()
    admin_db = client["admin"]
    medical_db = client["medical_db"]

    # 1. Compte Admin Infra : dbadmin sur la base 'admin' (droit global)
    admin_users = [u["user"] for u in admin_db.command("usersInfo")["users"]]
    if "dbadmin" not in admin_users:
        admin_db.command(
            "createUser", "dbadmin",
            pwd="dbadmin_password123",
            roles=[{"role": "dbAdminAnyDatabase", "db": "admin"}]
        )
        print("[SÉCURITÉ] Utilisateur dbadmin créé sur 'admin' (dbAdminAnyDatabase).")

    # 2. Comptes sur la base métier 'medical_db'
    medical_users = [u["user"] for u in medical_db.command("usersInfo")["users"]]

    # Compte applicatif ETL : migrator
    if "migrator" not in medical_users:
        medical_db.command(
            "createUser", "migrator",
            pwd="migrator_password123",
            roles=[
                {"role": "readWrite", "db": "medical_db"},
                {"role": "dbAdmin", "db": "medical_db"}
            ]
        )
        print("[SÉCURITÉ] Utilisateur migrator créé sur 'medical_db' (readWrite, dbAdmin).")

    # Compte consultation / audit : auditor
    if "auditor" not in medical_users:
        medical_db.command(
            "createUser", "auditor",
            pwd="auditor_password123",
            roles=[{"role": "read", "db": "medical_db"}]
        )
        print("[SÉCURITÉ] Utilisateur auditor créé sur 'medical_db' (read).")

    client.close()
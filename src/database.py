import os
import sys
from pymongo import MongoClient

def get_mongo_client():
    # Construction de l'URI d'administration à partir des variables d'environnement
    root_user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    root_pwd = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    mongo_host = os.getenv("MONGO_HOST", "mongodb")
    mongo_port = os.getenv("MONGO_PORT", "27017")

    if not root_user or not root_pwd:
        print("[ERREUR] Les identifiants administrateur MongoDB sont absents de l'environnement.")
        sys.exit(1)

    mongo_uri = f"mongodb://{root_user}:{root_pwd}@{mongo_host}:{mongo_port}/?authSource=admin"
    return MongoClient(mongo_uri)

def setup_database_roles():
    # Récupération stricte des mots de passe des rôles (sans fallback en clair)
    dbadmin_pwd = os.getenv("DBADMIN_PASSWORD")
    migrator_pwd = os.getenv("MIGRATOR_PASSWORD")
    auditor_pwd = os.getenv("AUDITOR_PASSWORD")

    if not all([dbadmin_pwd, migrator_pwd, auditor_pwd]):
        print("[ERREUR] Un ou plusieurs mots de passe de rôles sont manquants dans le fichier .env.")
        sys.exit(1)

    client = get_mongo_client()
    admin_db = client["admin"]
    medical_db = client["medical_db"]

    # 1. Compte Admin Infra : dbadmin sur la base 'admin' (droit global)
    admin_users = [u["user"] for u in admin_db.command("usersInfo")["users"]]
    if "dbadmin" not in admin_users:
        admin_db.command(
            "createUser", "dbadmin",
            pwd=dbadmin_pwd,
            roles=[{"role": "dbAdminAnyDatabase", "db": "admin"}]
        )
        print("[SÉCURITÉ] Utilisateur dbadmin créé sur 'admin' (dbAdminAnyDatabase).")

    # 2. Comptes sur la base métier 'medical_db'
    medical_users = [u["user"] for u in medical_db.command("usersInfo")["users"]]

    # Compte applicatif : migrator
    if "migrator" not in medical_users:
        medical_db.command(
            "createUser", "migrator",
            pwd=migrator_pwd,
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
            pwd=auditor_pwd,
            roles=[{"role": "read", "db": "medical_db"}]
        )
        print("[SÉCURITÉ] Utilisateur auditor créé sur 'medical_db' (read).")

    client.close()
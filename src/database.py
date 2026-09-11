import os
from pymongo import MongoClient

def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:admin@mongodb:27017/?authSource=admin")
    print("Connexion à MongoDB...")
    client = MongoClient(mongo_uri)
    return client
#test

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
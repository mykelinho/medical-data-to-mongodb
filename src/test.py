def test_crud(collection):
    print("--- Lancement des tests CRUD ---")
    
    # 1. CREATE
    collection.insert_one({"name": "Patient Test", "age": 30, "medical_condition": "Aucune"})
    print("CREATE OK")
    
    # 2. READ
    patient = collection.find_one({"name": "Patient Test"})
    assert patient is not None, "Erreur : patient non trouvé en base"
    print("READ OK")
    
    # 3. UPDATE
    collection.update_one({"name": "Patient Test"}, {"$set": {"age": 31}})
    patient_updated = collection.find_one({"name": "Patient Test"})
    assert patient_updated["age"] == 31, "Erreur : mise à jour non appliquée"
    print("UPDATE OK")
    
    # 4. DELETE
    collection.delete_one({"name": "Patient Test"})
    patient_deleted = collection.find_one({"name": "Patient Test"})
    assert patient_deleted is None, "Erreur : suppression échouée"
    print("DELETE OK")
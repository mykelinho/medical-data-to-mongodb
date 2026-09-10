# Mission DataSoluTech - Migration NoSQL et Cloud AWS

Ce projet automatise la migration d'un dataset médical vers MongoDB via Docker, assurant portabilité et scalabilité.

## 1. Démarche Technique de Migration
- **Nettoyage et Typage** : Le script Python lit le CSV, force le typage des colonnes critiques (Age, Montant_Facture) et nettoie les valeurs manquantes pour garantir l'intégrité des données avant et après migration.
- **Indexation** : Un index unique est placé sur le `Patient_ID` et un index simple sur `Condition_Medicale` pour accélérer les requêtes.
- **Conteneurisation** : L'infrastructure s'appuie sur `docker-compose`. Un volume persistant héberge la base de données MongoDB, tandis qu'un volume supplémentaire permet au conteneur Python d'accéder au CSV local.

## 2. Schéma de la Base de Données
Le stockage en BSON dans la collection `patients` respecte la structure suivante :
```json
{
  "_id": {"$oid": "64d..."},
  "Patient_ID": "PID-1000",
  "Nom": "Jean Martin",
  "Age": 45,
  "Sexe": "M",
  "Groupe_Sanguin": "O+",
  "Condition_Medicale": "Diabète",
  "Date_Admission": "2025-05-12",
  "Montant_Facture": 1250.50
}
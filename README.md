# Mission DataSoluTech : Pipeline de Migration NoSQL Sécurisé

Ce projet présente une solution technique pour la migration, le nettoyage et la sécurisation d'un jeu de données médicales vers une infrastructure MongoDB conteneurisée. Réalisé pour le client **DataSoluTech**, ce socle garantit la portabilité du code, l'intégrité des dossiers patients et prépare le terrain pour une scalabilité horizontale sur le Cloud.

---

## 1. Arborescence du Projet

L'organisation du dépôt respecte les standards de séparation entre l'infrastructure (Docker) et le code applicatif (Python).

```text
├── Dockerfile                  # Définition de l'image Python et installation des dépendances
├── docker-compose.yml          # Orchestration des conteneurs (Base de données + ETL)
├── README.md                   # Documentation technique du projet
└── src/
    ├── data/
    │   └── healthcare_dataset.csv # Fichier source brut (monté sur un volume Docker)
    ├── database.py             # Script de configuration de la sécurité et des rôles (RBAC)
    ├── main.py                 # Point d'entrée exécutant séquentiellement l'ETL et les tests
    ├── requirements.txt        # Liste des bibliothèques Python (pandas, pymongo)
    ├── test.py                 # Batterie de tests fonctionnels automatisés (CRUD)
    └── utils.py                # Pipeline de nettoyage, enrichissement et rapport d'audit
```

---

## 2. Architecture Globale et Stack Technique

L'application est découpée en micro-services pour isoler la donnée de la logique de traitement :

* **Moteur de traitement ETL :** `Python 3.10-slim` avec `pandas` pour les transformations en mémoire et `pymongo` pour le requêtage NoSQL.
* **Base de données :** `MongoDB`, choisi pour sa flexibilité de schéma, parfaitement adaptée aux données de santé hétérogènes.
* **Persistance :** Utilisation de volumes Docker dédiés. Un volume *bind-mount* isole le fichier CSV source, et un volume nommé `mongo_data` assure la persistance des données du moteur NoSQL entre deux redémarrages.

---

## 3. Pipeline ETL et Qualité des Données

Le script `utils.py` applique une normalisation stricte pour assainir le jeu de données sans perte d'information :

* **Normalisation des colonnes :** Conversion en `snake_case` strict.
* **Dédoublonnage :** Élimination des doublons parfaits.
* **Assainissement textuel :** Conservation des civilités (Mr, Dr) mais nettoyage des espaces multiples, virgules parasites et uniformisation en `Title Case`.
* **Intégrité comptable :** Neutralisation des montants de facturation négatifs (convertis en `null` BSON).
* **Cohérence temporelle :** Si la date de sortie précède l'admission, elle devient `null`. Calcul automatique de la durée de séjour (`length_of_stay_days`).

---

## 4. Schéma NoSQL et Indexation

Les documents sont insérés dans la collection `patients` de la base `medical_db`.

```json
{
  "_id": {"$oid": "664f1a2b8c9d4e5f6a7b8c9d"},
  "name": "Mr. David Pierce",
  "age": 45,
  "gender": "Male",
  "blood_type": "O+",
  "medical_condition": "Hypertension",
  "date_of_admission": "2024-03-12",
  "doctor": "Dr. Katie Barrett",
  "hospital": "Hernandez Rogers And Vang",
  "insurance_provider": "Cigna",
  "billing_amount": 18450.25,
  "room_number": 302,
  "admission_type": "Urgent",
  "discharge_date": "2024-03-18",
  "medication": "Lipitor",
  "test_results": "Normal",
  "length_of_stay_days": 6
}
```

**Index créés pour optimiser les performances :**

* `name` : Accélération de la recherche directe d'un dossier patient.
* `medical_condition` : Optimisation du filtrage et des statistiques par pathologie.
* `date_of_admission` : Amélioration des tris temporels et de l'analyse des flux.

---

## 5. Bases de Données, Sécurité et Rôles (RBAC)

Le script `database.py` déploie dynamiquement un modèle de sécurité basé sur le principe du moindre privilège, réparti sur deux bases de données distinctes (`admin` pour le système, `medical_db` pour les données cliniques).

| Rôle logique         | Utilisateur  | Base d'authentification | Droits MongoDB             | Explication et Usage                                                                                                                             |
| :-------------------- | :----------- | :---------------------- | :------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Super-Admin** | `root`     | `admin`               | `root`                   | Utilisé uniquement par Docker au premier démarrage pour provisionner le cluster.                                                               |
| **Admin Infra** | `dbadmin`  | `admin`               | `dbAdminAnyDatabase`     | Profil DevOps pour la maintenance système, le compactage et l'indexation globale.                                                               |
| **Service App** | `migrator` | `medical_db`          | `readWrite`, `dbAdmin` | Utilisé par le script Python pour insérer et nettoyer les données. Il possède les droits d'administration*uniquement* sur sa base métier. |
| **Audit**       | `auditor`  | `medical_db`          | `read`                   | Compte en lecture seule sécurisé, destiné aux soignants, data analysts et évaluateurs.                                                       |

---

## 6. Tests Fonctionnels (CRUD) et Résultats

Le script `test.py` prouve l'intégrité de la migration en simulant le cycle de vie complet d'une donnée. Si une assertion échoue, le conteneur s'arrête en erreur (`Exit 1`), empêchant la validation d'une base corrompue.

* **Create :** Insertion d'un patient témoin.
* **Read :** Recherche et confirmation de l'insertion.
* **Update :** Modification d'un attribut (ex: âge) et vérification.
* **Delete :** Suppression du patient témoin pour laisser la base propre.

**Logs générés par l'application lors de l'exécution :**

```text
Extraction des données brutes depuis : /app/src/data/healthcare_dataset.csv
============================================================================

RAPPORT D'AUDIT QUALITÉ : NETTOYAGES ET CORRECTIONS APPLIQUÉS
===============================================================

- Lignes brutes initiales              : 55500
- Doublons parfaits supprimés          : 534
- Lignes finales conservées            : 54966

---

Détail des données RETOUCHÉES / CORRIGÉES :

* Noms de patients mis propres       : 54966
* Noms de médecins mis propres       : 54966
* Noms d'hôpitaux nettoyés           : 54966
* Valeurs catégorielles normalisées  : 329796
* Groupes sanguins passés en majuscules: 12450

---

Détail des anomalies transformées en NULL (None) :

* Dates de sortie < date d'entrée    : 12
* Montants de facturation négatifs   : 5
* Montants de facturation non saisis : 0
* Groupes sanguins invalides         : 0
* Noms de patients manquants         : 0
* Médecins manquants                 : 0
* Hôpitaux manquants                 : 0
* Âges invalides ou hors limites     : 3
* Numéros de chambre invalides       : 0
* Dates d'admission non lisibles     : 0
* Dates de sortie non lisibles       : 0
===============================================================

Migration validée : 54966 documents insérés dans MongoDB.
--- Lancement des tests CRUD ---
CREATE OK
READ OK
UPDATE OK
DELETE OK
```

---

## 7. Guide de Déploiement et Commandes Courantes

Voici les commandes étape par étape pour déployer, auditer et arrêter l'infrastructure :

### 7.1. Démarrer le pipeline ETL complet

* **Commande :**
  ```bash
  docker compose up --build -d
  ```
* **Pourquoi :** Construit les images Docker, lance la base MongoDB, configure les sécurités et exécute la migration Python en arrière-plan.

### 7.2. Consulter les logs de migration

* **Commande :**
  ```bash
  docker compose logs python_migration
  ```
* **Pourquoi :** Permet de lire le rapport d'audit qualité et de vérifier le succès des tests CRUD générés par le script Python.

### 7.3. Se connecter à la base de données en mode sécurisé

* **Commande :**
  ```bash
  docker exec -it mongodb_server mongosh -u auditor -p auditor_password123 --authenticationDatabase medical_db
  ```
* **Pourquoi :** Simule l'accès d'un analyste pour vérifier que la donnée est bien présente, tout en prouvant que l'utilisateur n'a pas les droits de modification (verrouillage RBAC).

Commandes internes (une fois dans l'interface `mongosh`) :

```javascript
use medical_db
db.patients.countDocuments()
db.patients.findOne()
```

### 7.4. Arrêter et détruire l'environnement de test

* **Commande :**
  ```bash
  docker compose down -v
  ```
* **Pourquoi :** Stoppe les conteneurs proprement. L'ajout de `-v` purge le volume de la base de données pour repartir d'un environnement vide à la prochaine exécution.

---

## 8. Stratégie de Déploiement Cloud (Cible AWS)

Pour répondre aux problématiques de charge et de haute disponibilité soulevées par le client, l'architecture a été conçue pour basculer sur les services managés d'Amazon Web Services :


* **Amazon S3 (Stockage Objet) :**
  Le volume local contenant le fichier CSV sera remplacé par un Bucket S3 sécurisé (chiffrement KMS). Cela garantit un stockage illimité, un archivage à froid économique des historiques médicaux, et permet de déclencher automatiquement la migration à chaque nouveau dépôt de fichier.



* **Amazon DocumentDB :**
  Le conteneur MongoDB local sera substitué par Amazon DocumentDB, un service NoSQL entièrement managé et compatible MongoDB. Il assure une réplication multi-AZ, des sauvegardes automatiques et une sécurité certifiée pour l'hébergement de données de santé (HIPAA).



* **Amazon ECS avec AWS Fargate :**
  L'application Python s'exécutera sous Amazon ECS via Fargate (approche Serverless). Le conteneur Python ne sera instancié que le temps de traiter un nouveau fichier CSV, supprimant ainsi la gestion des serveurs sous-jacents et réduisant drastiquement les coûts (FinOps). L'accès aux bases se fera via des Rôles IAM sécurisés.

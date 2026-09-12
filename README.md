# 🏥 Mission DataSoluTech : Pipeline de Migration NoSQL Sécurisé

Ce projet présente une solution technique d'ingénierie des données pour la migration, le nettoyage et la sécurisation d'un jeu de données médicales volumineux vers une infrastructure NoSQL MongoDB conteneurisée. Conçu pour répondre aux enjeux de performance et de scalabilité horizontale du client **DataSoluTech**, ce socle applicatif garantit l'intégrité clinique des dossiers patients, documente rigoureusement la sécurité d'accès et pose les bases d'un déploiement sur le Cloud.

---

## 1. Description du Programme : Utilité et Fonctionnement

### 1.1 Utilité Métier
Le client fait face à des limitations techniques avec ses outils traditionnels pour exploiter son historique médical (55 500 admissions). Le programme a pour vocation de :
* **Centraliser et fiabiliser** des données médicales hétérogènes sans perte d'information clinique.
* **Automatiser l'audit qualité** en traçant précisément les anomalies de saisie (doublons, valeurs négatives, incohérences de dates).
* **Fournir un moteur NoSQL sécurisé** facilitant les recherches rapides par praticien, pathologie ou date d'admission.

### 1.2 Fonctionnement Technique du Pipeline
Le programme s'exécute de façon séquentielle et automatisée via le script d'orchestration `main.py` :
1. **Initialisation de la gouvernance (`database.py`) :** Connexion en super-administrateur pour instancier la matrice de sécurité RBAC (création des comptes applicatif et audit avec leurs rôles respectifs).
2. **Extraction & Nettoyage ETL (`utils.py`) :** 
   - Chargement en mémoire via `pandas`.
   - Suppression exclusive des doublons parfaits.
   - Nettoyage textuel doux (Title Case, ponctuation parasite neutralisée, préservation des civilités `Dr.`, `Mr.`).
   - Assainissement des incohérences métier (montants négatifs et dates de sortie antérieures à l'entrée convertis en `null` BSON).
   - Enrichissement : calcul automatique de la durée de séjour (`length_of_stay_days`).
   - Production d'un rapport d'audit exhaustif affiché dans la console.
3. **Chargement NoSQL (`utils.py`) :** Remise à zéro de la collection pour garantir l'idempotence, création des index de performance B-tree, puis ingestion par lot (`insert_many`).
4. **Validation de l'intégrité (`test.py`) :** Exécution d'un cycle fonctionnel complet CRUD (Create, Read, Update, Delete) validé par assertions pour stopper l'exécution en cas d'anomalie.

---

## 2. Arborescence du Projet

L'organisation du dépôt respecte les standards de séparation entre le code applicatif (`src/`) et l'infrastructure Docker.

```text
├── Dockerfile                  # Définition de l'image Python et installation des dépendances
├── docker-compose.yml          # Orchestration des conteneurs (MongoDB + Pipeline ETL)
├── README.md                   # Documentation technique et guide d'exploitation
└── src/
    ├── data/
    │   └── healthcare_dataset.csv # Fichier source brut (monté sur un volume Docker)
    ├── database.py             # Configuration de la sécurité et des rôles (RBAC)
    ├── main.py                 # Chef d'orchestre exécutant l'ETL et les tests
    ├── requirements.txt        # Dépendances Python (pandas, pymongo)
    ├── test.py                 # Batterie de tests fonctionnels automatisés (CRUD)
    └── utils.py                # Fonctions d'ingestion, nettoyage, typage et audit
```

---

## 3. Architecture Globale et Stack Technique

L'application isole l'infrastructure de traitement et le stockage dans des micro-services conteneurisés :
* **Moteur applicatif :** `Python 3.10-slim` avec `pandas` pour le traitement vectorisé en mémoire et `pymongo` pour la communication réseau NoSQL.
* **Base de données :** `MongoDB` (image officielle), retenue pour la flexibilité de son modèle orienté documents (BSON).
* **Persistance Docker :**
  - Un volume de type *bind-mount* (`./src/data:/app/src/data`) isolant les données brutes CSV.
  - Un volume managé persistant (`mongo_data:/data/db`) pour assurer la pérennité de la base de données entre les redémarrages.

---

## 4. Schéma de la Base de Données NoSQL et Indexation

### 4.1 Modèle de Données (Collection `patients` / Base `medical_db`)
Les données cliniques sont dénormalisées sous format document BSON :

| Champ | Type BSON | Description & Règle Métier |
| :--- | :--- | :--- |
| `_id` | ObjectId | Clé primaire unique auto-générée par MongoDB. |
| `name` | String | Nom complet du patient nettoyé en Title Case avec civilité préservée. |
| `age` | Integer / Null | Âge du patient (null si hors de l'intervalle 0-125 ans). |
| `gender` | String / Null | Sexe biologique normalisé (`Male`, `Female`). |
| `blood_type` | String / Null | Groupe sanguin validé selon le standard officiel (`A+`, `O-`, etc.). |
| `medical_condition` | String / Null | Diagnostic ou pathologie principale normalisée. |
| `date_of_admission` | String (ISO-8601) | Date d'entrée au format `YYYY-MM-DD`. |
| `doctor` | String | Praticien référent avec civilité et titre conservés en Title Case. |
| `hospital` | String | Établissement de soins épuré des artefacts de saisie. |
| `insurance_provider` | String | Organisme d'assurance santé. |
| `billing_amount` | Double / Null | Montant de prise en charge (arrondi à 2 décimales, null si négatif). |
| `room_number` | Integer / Null | Numéro de chambre d'affectation. |
| `admission_type` | String | Type d'admission (`Emergency`, `Urgent`, `Elective`). |
| `discharge_date` | String (ISO-8601) / Null | Date de sortie (null si antérieure à la date d'admission). |
| `medication` | String | Traitement médicamenteux prescrit. |
| `test_results` | String | Résultats des analyses (`Normal`, `Abnormal`, `Inconclusive`). |
| `length_of_stay_days` | Integer / Null | Durée de séjour calculée en jours (`discharge_date` - `date_of_admission`). |

### 4.2 Document Exemple
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

### 4.3 Index de Performance (B-Tree)
Pour optimiser les temps de réponse face à la volumétrie :
* `name` : Accélération des recherches nominales de dossiers patients.
* `medical_condition` : Optimisation des regroupements et requêtes analytiques par pathologie.
* `date_of_admission` : Accélération des tris temporels et du suivi chronologique des flux.

---

## 5. Sécurité et Contrôle d'Accès Basé sur les Rôles (RBAC)

L'accès à MongoDB obéit au principe du moindre privilège, cloisonné entre la base technique `admin` et la base applicative `medical_db` :

| Rôle logique | Utilisateur | Base d'authentification | Droits MongoDB assignés | Périmètre et Justification |
| :--- | :--- | :--- | :--- | :--- |
| **Super-Admin** | `root` | `admin` | `root` | Initialisation du conteneur par Docker Compose et provisionnement des comptes. |
| **Admin Infra** | `dbadmin` | `admin` | `dbAdminAnyDatabase` | Profil DevOps : maintenance système, réparation et défragmentation des index. |
| **Service App** | `migrator` | `medical_db` | `readWrite`, `dbAdmin` | Script Python : insertion des données, purge, création des index sur `medical_db`. |
| **Audit / Métier** | `auditor` | `medical_db` | `read` | Lecture seule stricte pour les analystes et auditeurs, sans risque d'altération. |

---

## 6. Tests Fonctionnels (CRUD) et Audit d'Exécution

Le script `test.py` valide systématiquement le cycle de vie complet de la donnée avant de clôturer la migration :
* **Create :** Insertion d'un patient témoin (`insert_one`).
* **Read :** Recherche et assertion de l'existence du document (`find_one`).
* **Update :** Modification d'un attribut et vérification de la persistance (`update_one`).
* **Delete :** Nettoyage du patient témoin et contrôle d'absence (`delete_one`).

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

## 7. Guide de Déploiement et Commandes Ligne par Ligne

### 7.1 Démarrer l'infrastructure et lancer le pipeline
Construit l'image de migration Python, démarre l'instance MongoDB et exécute automatiquement l'ingestion :
```bash
docker compose up --build -d
```

### 7.2 Contrôler l'exécution et consulter les logs
Affiche le déroulement de la migration, le rapport d'audit et le résultat des tests CRUD :
```bash
docker compose logs python_migration
```

### 7.3 Se connecter à MongoDB en mode sécurisé (Profil Auditeur)
Ouvre un terminal interactif dans le conteneur MongoDB avec le compte en lecture seule pour vérifier les données sans risque de modification :
```bash
docker exec -it mongodb_server mongosh -u auditor -p auditor_password123 --authenticationDatabase medical_db
```

### 7.4 Vérifier les données dans l'interpréteur MongoSH
À saisir directement dans le terminal `mongosh` :
```javascript
use medical_db
db.patients.countDocuments()
db.patients.findOne()
exit
```

### 7.5 Arrêter et réinitialiser l'environnement
Stoppe les services et purge le volume persistant pour permettre un redémarrage depuis un état vierge :
```bash
docker compose down -v
```

---

## 8. Stratégie de Déploiement Cloud (Cible AWS)

Pour répondre aux objectifs de haute disponibilité et de montée en charge soulevés par DataSoluTech, les composants locaux ont été modélisés pour une transition vers l'écosystème AWS :

* **Amazon S3 (Stockage Objet Sécurisé) :** Remplace le volume local `data/` pour héberger les fichiers CSV bruts. Il assure une durabilité de 99,999999999 % (11 9's), un chiffrement KMS au repos et la possibilité de déclencher automatiquement le pipeline par événement (S3 Event Notifications).

* **Amazon DocumentDB (NoSQL Managé) :** Service de base de données managé entièrement compatible avec les API MongoDB. Il élimine la maintenance système, offre une réplication multi-AZ automatique sur 3 zones de disponibilité et répond aux exigences de conformité des données médicales.

* **Amazon ECS avec AWS Fargate (Traitement Serverless) :** Exécution du conteneur de migration sous forme de tâche éphémère (AWS Fargate). L'infrastructure compute n'est allouée et facturée que pendant la durée exacte du traitement du fichier, réduisant drastiquement les coûts d'infrastructure (FinOps).

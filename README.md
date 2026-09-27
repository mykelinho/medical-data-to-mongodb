# Migration NoSQL : Pipeline de Données Médicales sous Docker

Ce projet permet de nettoyer, fiabiliser et importer un fichier de 55 500 dossiers médicaux vers une base de données NoSQL MongoDB. L'ensemble de la solution est entièrement conteneurisé avec Docker pour s'exécuter automatiquement en une seule commande, sans nécessiter de configuration manuelle.

---

## Sommaire

1. [Cadrage de la Mission](#1-cadrage-de-la-mission)
2. [Environnement Technique (Python & Librairies)](#2-environnement-technique-python--librairies)
3. [Prérequis et Installation de Docker (Windows & Debian/Ubuntu)](#3-prérequis-et-installation-de-docker-windows--debianubuntu)
4. [Comment Lancer la Migration (Guide Pas à Pas)](#4-comment-lancer-la-migration-guide-pas-à-pas)
5. [Ce qui se Passe Pendant la Migration (L'Orchestrateur)](#5-ce-qui-se-passe-pendant-la-migration-lorchestrateur)
6. [Schéma de la Base de Données (Collection patients)](#6-schéma-de-la-base-de-données-collection-patients)
7. [Architecture Docker et Rangement des Fichiers](#7-architecture-docker-et-rangement-des-fichiers)
8. [Pourquoi MongoDB et Docker ?](#8-pourquoi-mongodb-et-docker-)
9. [Validation des Tests (CRUD)](#9-validation-des-tests-crud)
10. [Bilan Qualité du Nettoyage](#10-bilan-qualité-du-nettoyage)
11. [Indexation de la Collection](#11-indexation-de-la-collection)
12. [Sécurité et Comptes d'Accès (RBAC)](#12-sécurité-et-comptes-daccès-rbac)

---

## 1. Cadrage de la Mission

* **Le Problème Initial :** Le client manipule **55 500 dossiers de patients** stockés dans un simple fichier plat brut (`CSV`). Ce fichier est devenu trop volumineux et trop lent pour les recherches et les tâches quotidiennes des équipes hospitalières.
* **La Solution Déployée :**
  * **Python (Le Nettoyage) :** Un programme automatisé qui lit le fichier, supprime les erreurs (doublons, fautes de casse dans les noms, factures négatives) sans jamais altérer le fichier CSV d'origine.
  * **MongoDB (Le Stockage) :** Une base de données NoSQL orientée documents, rapide, évolutive et sécurisée par des accès personnalisés.
  * **Docker (Le Pack) :** Une boîte prête à l'emploi qui regroupe la base et le script pour que le projet s'exécute de façon identique sur n'importe quel ordinateur.

---

## 2. Environnement Technique (Python & Librairies)

Le conteneur de traitement applicatif repose sur un environnement Python allégé et optimisé :

* **Version de Python :** `Python 3.10-slim` (image Linux officielle légère, limitant l'empreinte disque et la consommation de mémoire RAM).
* **Dépendances applicatives (`requirements.txt`) :**
  * **`pandas` :** Utilisé pour charger le fichier CSV en mémoire, supprimer les doublons, nettoyer les colonnes textuelles de manière vectorisée et calculer le nouvel indicateur métier de durée de séjour.
  * **`pymongo` :** Le pilote officiel Python pour MongoDB. Il permet de se connecter à la base, d'initialiser les comptes et les permissions de sécurité, de créer les index B-tree et d'insérer les dossiers par lot (`insert_many`).

---

## 3. Prérequis et Installation de Docker (Windows & Debian/Ubuntu)

Avant d'exécuter le projet, le moteur Docker doit être installé et en cours d'exécution sur votre machine.

### Solution A — Installation sous Windows (Docker Desktop)

1. **Activer WSL 2 (Windows Subsystem for Linux) :**
   Ouvrez une invite PowerShell en tant qu'administrateur et exécutez :
   ```powershell
   wsl --update
   ```
2. **Installer Docker Desktop :**
   - Téléchargez l'installateur officiel sur le site de Docker ([docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)).
   - Lancez l'installation en veillant à cocher l'option **« Use WSL 2 instead of Hyper-V »**.
   - Redémarrez l'ordinateur si demandé.
3. **Démarrer et vérifier Docker :**
   - Lancez **Docker Desktop** depuis le menu Démarrer.
   - Attendez que l'icône de la baleine dans la barre des tâches devienne fixe (statut *Engine running* vert).
   - Testez dans un terminal :
     ```powershell
     docker --version
     docker compose version
     ```

### Solution B — Installation sous Linux Debian / Ubuntu (Ligne de commande)

Sur un serveur ou une machine Linux (Debian, Ubuntu), l'installation se fait directement via le gestionnaire de paquets `apt` :

1. **Mettre à jour les paquets système :**
   ```bash
   sudo apt-get update
   sudo apt-get install -y ca-certificates curl gnupg lsb-release
   ```
2. **Ajouter le dépôt officiel Docker :**
   ```bash
   sudo mkdir -p /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```
   *(Pour Ubuntu, remplacez `debian` par `ubuntu` dans l'URL ci-dessus).*
3. **Installer Docker Engine et le plugin Docker Compose :**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
   ```
4. **Démarrer le service et autoriser votre utilisateur :**
   ```bash
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   ```
   *(Déconnectez-vous puis reconnectez-vous pour que l'ajout au groupe `docker` prenne effet sans avoir à taper `sudo` devant chaque commande).*

---

## 4. Comment Lancer la Migration (Guide Pas à Pas)

### 4.1 Lancer le projet

Cette commande prépare l'environnement Python, démarre la base MongoDB et lance automatiquement le nettoyage et l'importation des données :

```bash
docker compose up --build -d
```

### 4.2 Vérifier que tout s'est bien passé (Voir les logs)

Cette commande affiche le rapport d'audit qualité du nettoyage et confirme le succès des tests :

```bash
docker compose logs python_migration
```

### 4.3 Se connecter à la base en toute sécurité (Mode Consultation)

Pour vérifier les données dans MongoDB avec le compte auditeur en lecture seule (qui protège la base contre toute altération) :

```bash
docker exec -it mongodb_server mongosh -u auditor -p auditor_password123 --authenticationDatabase medical_db
```

### 4.4 Vérifier les données dans MongoDB

Une fois dans l'interpréteur interactif MongoSH :

```javascript
use medical_db
db.patients.countDocuments()   // Doit afficher 54966
db.patients.findOne()          // Affiche la fiche complète d'un patient
exit                           // Pour quitter
```

### 4.5 Tout arrêter et remettre à zéro

Pour stopper les conteneurs et purger le volume des données afin de repartir d'un état vierge :

```bash
docker compose down -v
```

---

## 5. Ce qui se Passe Pendant la Migration (L'Orchestrateur)

Le fichier `main.py` est le chef d'orchestre du projet. Dès que le conteneur Python démarre, il déroule automatiquement ces 6 étapes dans l'ordre :

1. **Étape 1 :** Créer les comptes utilisateurs et définir leurs droits d'accès s'ils n'existent pas encore (`setup_database_roles()`).
2. **Étape 2 :** Localiser le fichier CSV des données médicales brutes (`healthcare_dataset.csv`).
3. **Étape 3 :** Établir la connexion à MongoDB et sélectionner la collection `patients` dans la base `medical_db`.
4. **Étape 4 :** Charger le CSV et corriger toutes les erreurs de saisie (`load_and_clean_data()`) : suppression des doublons, harmonisation de la casse des noms et calcul de la durée de séjour.
5. **Étape 5 :** Insérer tous les dossiers propres dans MongoDB et poser les index de performance (`migrate_data()`).
6. **Étape 6 :** Réaliser un test fonctionnel rapide (ajouter, lire, modifier, supprimer un faux patient) pour valider que la base répond parfaitement (`test_crud()`).

---

## 6. Schéma de la Base de Données (Collection patients)

Chaque patient est enregistré sous la forme d'un document BSON complet. Toutes les informations sont regroupées au même endroit sans nécessiter de tables séparées.

| Champ | Type | Description et Règle Métier |
| :--- | :--- | :--- |
| `_id` | ObjectId | Numéro d'identification unique généré automatiquement par MongoDB. |
| `name` | String | Nom et prénom propres avec civilité conservée (`Mr.`, `Dr.`). |
| `age` | Integer | Âge du patient. |
| `gender` | String | Sexe du patient (`Male`, `Female`). |
| `blood_type` | String | Groupe sanguin vérifié (`A+`, `O-`, etc.). |
| `medical_condition` | String | Maladie ou diagnostic (ex. : Cancer, Diabète, Asthme). |
| `doctor` | String | Nom du médecin traitant remis au propre. |
| `hospital` | String | Nom de l'établissement hospitalier sans espaces ni virgules parasites. |
| `insurance_provider` | String | Nom de l'organisme d'assurance santé. |
| `billing_amount` | Double / Null | Montant de la facture (remplacé par null si le montant était négatif). |
| `room_number` | Integer | Numéro de chambre d'affectation. |
| `admission_type` | String | Type d'admission (`Emergency`, `Urgent`, `Elective`). |
| `date_of_admission` | String | Date d'entrée à l'hôpital (`AAAA-MM-JJ`). |
| `discharge_date` | String | Date de sortie de l'hôpital (`AAAA-MM-JJ`). |
| `medication` | String | Médicament prescrit. |
| `test_results` | String | Résultat d'examen (`Normal`, `Abnormal`, `Inconclusive`). |
| `length_of_stay_days` | Integer | **Nouveau champ calculé :** nombre de jours passés à l'hôpital (`discharge_date` - `date_of_admission`). |

### Exemple d'une fiche patient dans MongoDB :

```json
{
  "_id": { "$oid": "664f1a2b8c9d4e5f6a7b8c9d" },
  "name": "Mr. David Pierce",
  "age": 45,
  "gender": "Male",
  "blood_type": "O+",
  "medical_condition": "Hypertension",
  "doctor": "Dr. Katie Barrett",
  "hospital": "Hernandez Rogers And Vang",
  "insurance_provider": "Cigna",
  "billing_amount": 18450.25,
  "room_number": 302,
  "admission_type": "Urgent",
  "date_of_admission": "2024-03-12",
  "discharge_date": "2024-03-18",
  "medication": "Lipitor",
  "test_results": "Normal",
  "length_of_stay_days": 6
}
```

---

## 7. Architecture Docker et Rangement des Fichiers

### Schéma du fonctionnement

```text
┌────────────────────────────────────────────────────────────────────────┐
│                                DOCKER                                  │
│                                                                        │
│   [ Fichier Source CSV ] ──> [ Scripts Python ] ──> [ Base MongoDB ]   │
│      (55 500 lignes)          - main.py              (medical_db)      │
│      Dossier partagé          - utils.py             Port 27017        │
│      src/data                 - database.py          Dossier persistant│
│                               - test.py              mongo_data        │
└────────────────────────────────────────────────────────────────────────┘
```

### Organisation des dossiers

```text
├── Dockerfile                  # Instructions de build de l'image Python (Python 3.10-slim)
├── docker-compose.yml          # Définition des services MongoDB et Python
├── README.md                   # Guide d'utilisation et documentation technique
└── src/
    ├── data/
    │   └── healthcare_dataset.csv # Fichier CSV brut d'origine (non altéré)
    ├── database.py             # Gestion des connexions et attribution des rôles RBAC
    ├── main.py                 # Script principal exécutant les étapes dans l'ordre
    ├── requirements.txt        # Dépendances Python nécessaires (pandas, pymongo)
    ├── test.py                 # Batterie de tests fonctionnels CRUD
    └── utils.py                # Fonctions de nettoyage, d'audit qualité et d'insertion
```

---

## 8. Pourquoi MongoDB et Docker ?

### MongoDB
* **Format flexible :** Permet d'ajouter plus tard de nouvelles informations médicales sans restructurer toute la base.
* **Recherches directes :** Toutes les données d'un séjour sont réunies dans une même fiche, évitant des jointures lentes.
* **Évolutif :** Conçu pour absorber la croissance continue des dossiers sans chute de performance.

### Docker
* **Rapide et léger :** Les conteneurs démarrent en quelques secondes avec une très faible empreinte mémoire.
* **Reproductibilité :** Le code s'exécute exactement de la même manière sous Windows, macOS ou Linux.
* **Données conservées :** Même lors de l'arrêt des conteneurs, les dossiers patients sont préservés grâce au volume persistant `mongo_data`.

---

## 9. Validation des Tests (CRUD)

Avant de clôturer la migration, le script `test.py` exécute un cycle complet de validation avec un patient témoin :

* **[TEST 1] Insertion patient témoin :** Insertion unitaire avec `insert_one` → **CREATE OK**
* **[TEST 2] Assertion présence en base :** Recherche du document avec `find_one` → **READ OK**
* **[TEST 3] Modification d'attribut :** Mise à jour de l'âge (de 30 à 31 ans) via `$set` avec `update_one` → **UPDATE OK**
* **[TEST 4] Purge du patient témoin :** Suppression unitaire avec `delete_one` → **DELETE OK**

> **Sécurité du pipeline :** Chaque test repose sur une assertion stricte. Si une seule vérification échoue, le programme s'arrête immédiatement pour empêcher l'exploitation d'une base non conforme.

---

## 10. Bilan Qualité du Nettoyage

Rapport d'audit affiché dans la console à la fin de la migration (`docker compose logs python_migration`) :

```text
Extraction des données brutes depuis : /app/src/data/healthcare_dataset.csv
============================================================================
RAPPORT D'AUDIT QUALITÉ : NETTOYAGES ET CORRECTIONS APPLIQUÉS
============================================================================
- Lignes brutes initiales              : 55500
- Doublons parfaits supprimés          : 534
- Lignes finales conservées            : 54966
----------------------------------------------------------------------------
Détail des données RETOUCHÉES / CORRIGÉES :
* Noms de patients mis propres         : 54933 (99,9 %)
* Noms de médecins mis propres         : 1232  (2,2 %)
* Noms d'hôpitaux nettoyés             : 27597 (50,2 %)
* Valeurs catégorielles normalisées    : 11014 (20,0 %)
* Groupes sanguins passés en majuscules: 0
----------------------------------------------------------------------------
Détail des anomalies transformées en NULL (None) :
* Dates de sortie < date d'entrée      : 0
* Montants de facturation négatifs     : 106   (passés à vide sans jeter le dossier)
* Montants de facturation non saisis   : 0
* Groupes sanguins invalides           : 0
* Noms de patients manquants           : 0
* Médecins manquants                   : 0
* Hôpitaux manquants                   : 0
* Âges invalides ou hors limites       : 0
* Numéros de chambre invalides         : 0
* Dates d'admission non lisibles       : 0
* Dates de sortie non lisibles         : 0
============================================================================
Migration validée : 54966 documents insérés dans MongoDB.
```

*Note : Les données peuvent être visualisées et explorées graphiquement avec le client officiel **MongoDB Compass**.*

---

## 11. Indexation de la Collection

Un index fonctionne comme l'index alphabétique à la fin d'un livre : il évite de parcourir l'intégralité des 54 966 documents et accélère l'accès direct aux dossiers.

| Champ Clé | Pourquoi mettre un index ? |
| :--- | :--- |
| `_id` | **Identifiant unique :** Permet à la base d'ouvrir la fiche d'un patient instantanément. |
| `name` | **Recherche par patient :** Permet aux soignants de trouver directement un dossier par nom de famille sans latence. |
| `medical_condition` | **Recherche par maladie :** Permet d'afficher immédiatement tous les patients diagnostiqués pour une pathologie précise. |
| `date_of_admission` | **Par date d'arrivée :** Permet d'afficher rapidement les admissions récentes et de faciliter les tris chronologiques. |

---

## 12. Sécurité et Comptes d'Accès (RBAC)

L'accès à MongoDB respecte le principe du moindre privilège afin de cloisonner les rôles et d'éviter les suppressions accidentelles :

| Rôle Logique | Nom Utilisateur | Base Auth | Droits MongoDB | Rôle et Explication |
| :--- | :--- | :--- | :--- | :--- |
| **Super-Admin** | `root` | `admin` | `root` | Création et initialisation du serveur MongoDB. Inactif pour l'application. |
| **Admin Infra** | `dbadmin` | `admin` | `dbAdminAnyDatabase` | Destiné à l'équipe technique (maintenance, défragmentation, gestion des index). |
| **Service ETL** | `migrator` | `medical_db` | `readWrite`, `dbAdmin` | Utilisé par le script Python pour insérer et mettre à jour les dossiers patients. |
| **Audit / Métier** | `auditor` | `medical_db` | `read` | Réservé à la consultation : lecture seule stricte avec interdiction formelle de modifier ou supprimer des données. |
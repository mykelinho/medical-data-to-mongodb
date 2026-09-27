
# Migration NoSQL : Pipeline de Données Médicales sous Docker

Ce projet permet de nettoyer, fiabiliser et importer un fichier de 55 500 dossiers médicaux vers une base de données NoSQL MongoDB. L'ensemble de la solution est conteneurisé avec Docker pour s'exécuter automatiquement en une seule commande, avec une gestion sécurisée des identifiants sans aucun mot de passe en clair dans le code.

---

## Sommaire

1. [Cadrage de la Mission](#1-cadrage-de-la-mission)
2. [Environnement Technique (Python &amp; Librairies)](#2-environnement-technique-python--librairies)
3. [Gestion Sécurisée des Identifiants (.env)](#3-gestion-sécurisée-des-identifiants-env)
4. [Prérequis et Installation de Docker (Windows &amp; Debian/Ubuntu)](#4-prérequis-et-installation-de-docker-windows--debianubuntu)
5. [Guide Pas à Pas : Comment Lancer la Migration](#5-guide-pas-à-pas--comment-lancer-la-migration)
6. [Ce qui se Passe Pendant la Migration (L&#39;Orchestrateur)](#6-ce-qui-se-passe-pendant-la-migration-lorchestrateur)
7. [Schéma de la Base de Données (Collection patients)](#7-schéma-de-la-base-de-données-collection-patients)
8. [Architecture Docker et Rangement des Fichiers](#8-architecture-docker-et-rangement-des-fichiers)
9. [Pourquoi MongoDB et Docker ?](#9-pourquoi-mongodb-et-docker-)
10. [Validation des Tests (CRUD)](#10-validation-des-tests-crud)
11. [Bilan Qualité du Nettoyage](#11-bilan-qualité-du-nettoyage)
12. [Indexation de la Collection](#12-indexation-de-la-collection)
13. [Sécurité et Comptes d&#39;Accès (RBAC)](#13-sécurité-et-comptes-daccès-rbac)

---

## 1. Cadrage de la Mission

* **Le Problème Initial :** Le client manipule **55 500 dossiers de patients** stockés dans un simple fichier plat brut (`CSV`). Ce fichier est devenu trop volumineux et trop lent pour les recherches et les tâches quotidiennes des équipes hospitalières.
* **La Solution Déployée :**
  * **Python (Le Nettoyage) :** Un programme automatisé qui lit le fichier, supprime les erreurs (doublons, fautes de casse dans les noms, factures négatives) sans jamais modifier le fichier CSV d'origine.
  * **MongoDB (Le Stockage) :** Une base de données NoSQL orientée documents, rapide, évolutive et sécurisée par des accès personnalisés.
  * **Docker (Le Pack) :** Une boîte prête à l'emploi qui regroupe la base et le script pour que le projet s'exécute à l'identique sur n'importe quel ordinateur.

---

## 2. Environnement Technique (Python & Librairies)

Le conteneur applicatif repose sur un environnement Python optimisé :

* **Version de Python :** `Python 3.10-slim` (image Linux officielle légère, limitant l'empreinte disque et l'usage de la mémoire RAM).
* **Dépendances applicatives (`requirements.txt`) :**
  * **`pandas` :** Utilisé pour charger le CSV en mémoire, supprimer les doublons, nettoyer les données textuelles de manière vectorisée et calculer la durée de séjour hospitalière.
  * **`pymongo` :** Le pilote officiel Python pour MongoDB. Il permet de se connecter à la base, d'initialiser les utilisateurs avec leurs rôles, d'appliquer les index de recherche et d'insérer les dossiers par lot (`insert_many`).

---

## 3. Gestion Sécurisée des Identifiants (.env)

Pour respecter les bonnes pratiques de sécurité, **aucun mot de passe n'est écrit en dur dans les scripts Python**.

* **Le fichier local `.env` :** Il contient les identifiants réels utilisés sur la machine. Docker Compose charge ce fichier et transmet les variables au conteneur au démarrage.
* **Le fichier `.gitignore` :** Il demande à Git d'ignorer systématiquement le fichier `.env`. Les mots de passe ne sont donc jamais publiés sur GitHub.
* **Le modèle partagé `.env.example` :** Il est présent sur GitHub et sert de modèle pour savoir quelles variables renseigner sans divulguer de secrets.

Dans le script `database.py`, les accès sont récupérés via `os.getenv()`. Si un mot de passe est absent, le script s'arrête immédiatement par sécurité.

---

## 4. Prérequis et Installation de Docker (Windows & Debian/Ubuntu)

Le moteur Docker doit être démarré sur la machine avant de lancer le projet.

### Option A — Installation sous Windows (Docker Desktop)

1. **Activer WSL 2 (Windows Subsystem for Linux) :**
   Ouvrez PowerShell en tant qu'administrateur et tapez :
   ```powershell
   wsl --update
   ```
2. **Installer Docker Desktop :**
   - Téléchargez l'installateur sur [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop).
   - Lancez l'installation en cochant **« Use WSL 2 instead of Hyper-V »**.
   - Redémarrez le PC si demandé.
3. **Démarrer Docker :**
   - Lancez **Docker Desktop** depuis le menu Démarrer.
   - Attendez que l'icône de la baleine en bas à droite devienne fixe (*Engine running*).
   - Vérifiez dans votre terminal :
     ```powershell
     docker --version
     docker compose version
     ```

### Option B — Installation sous Linux Debian / Ubuntu (Ligne de commande)

1. **Mettre à jour les paquets système :**
   ```bash
   sudo apt-get update
   sudo apt-get install -y ca-certificates curl gnupg lsb-release
   ```
2. **Ajouter le dépôt officiel Docker :**
   ```bash
   sudo mkdir -p /etc/apt/keyrings
   curl -fsSL [https://download.docker.com/linux/debian/gpg](https://download.docker.com/linux/debian/gpg) | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] [https://download.docker.com/linux/debian](https://download.docker.com/linux/debian) $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```

   *(Pour Ubuntu, remplacez `debian` par `ubuntu` dans la commande ci-dessus).*
3. **Installer Docker Engine et le plugin Compose :**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
   ```
4. **Démarrer le service et autoriser l'utilisateur :**
   ```bash
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER
   ```

   *(Fermez puis rouvrez votre session pour appliquer les permissions).*

---

## 5. Guide Pas à Pas : Comment Lancer la Migration

### 5.1 Préparer le fichier de configuration `.env`

À la racine du projet, créez votre fichier `.env` à partir du modèle fourni :

* **Sous Windows (PowerShell) :**
  ```powershell
  copy .env.example .env
  ```
* **Sous Linux / macOS :**
  ```bash
  cp .env.example .env
  ```

*(Vous pouvez modifier les mots de passe à l'intérieur du fichier `.env` si vous le souhaitez).*

### 5.2 Lancer le projet

Cette commande démarre la base MongoDB et lance le conteneur Python qui traite et importe les données médicales :

```bash
docker compose up --build -d
```

### 5.3 Vérifier l'avancement et consulter les logs

Cette commande affiche le rapport d'audit qualité du nettoyage et la validation des tests CRUD :

```bash
docker compose logs python_migration
```

### 5.4 Se connecter à MongoDB en toute sécurité (Mode Consultation)

Pour consulter les données avec le compte auditeur en lecture seule (qui empêche toute modification accidentelle) :

```bash
docker exec -it mongodb_server mongosh -u auditor -p auditor_password123 --authenticationDatabase medical_db
```

### 5.5 Vérifier les données dans l'interpréteur MongoSH

Commandes à saisir directement dans le terminal MongoSH :

```javascript
use medical_db
db.patients.countDocuments()   // Doit afficher 54966
db.patients.findOne()          // Affiche le dossier complet d'un patient
exit                           // Pour sortir
```

### 5.6 Arrêter et nettoyer le projet

Pour éteindre les conteneurs et supprimer les volumes afin de repartir sur une base vierge :

```bash
docker compose down -v
```

---

## 6. Ce qui se Passe Pendant la Migration (L'Orchestrateur)

Le fichier `main.py` est le chef d'orchestre du projet. Dès que le conteneur Python s'allume, il exécute automatiquement ces 6 étapes dans l'ordre :

1. **Étape 1 :** Créer les comptes utilisateurs et leurs accès s'ils n'existent pas encore (`setup_database_roles()`).
2. **Étape 2 :** Indiquer où se trouve le fichier CSV des données médicales brutes (`healthcare_dataset.csv`).
3. **Étape 3 :** Se connecter à MongoDB et choisir la table des patients dans la base `medical_db`.
4. **Étape 4 :** Charger le CSV et nettoyer toutes les erreurs (`load_and_clean_data()`) : suppression des doublons, mise au propre des noms et calcul automatique de la durée de séjour.
5. **Étape 5 :** Envoyer toutes les données propres dans MongoDB et créer les index de recherche (`migrate_data()`).
6. **Étape 6 :** Faire un test rapide (ajouter, lire, modifier, supprimer un faux patient) pour vérifier que la base fonctionne (`test_crud()`).

---

## 7. Schéma de la Base de Données (Collection patients)

Chaque patient forme un document BSON complet, sans nécessiter de tables séparées ni de jointures complexes :

| Champ                   | Type BSON     | Description et Règle Métier                                                                                |
| :---------------------- | :------------ | :----------------------------------------------------------------------------------------------------------- |
| `_id`                 | ObjectId      | Numéro unique auto-généré par MongoDB.                                                                   |
| `name`                | String        | Nom et prénom nettoyés en Title Case (titres`Mr.`, `Dr.` préservés).                                 |
| `age`                 | Integer       | Âge du patient.                                                                                             |
| `gender`              | String        | Sexe du patient (`Male`, `Female`).                                                                      |
| `blood_type`          | String        | Groupe sanguin vérifié (`A+`, `O-`, etc.).                                                             |
| `medical_condition`   | String        | Diagnostic ou maladie (ex. : Cancer, Diabète, Asthme).                                                      |
| `doctor`              | String        | Nom du médecin traitant nettoyé.                                                                           |
| `hospital`            | String        | Établissement de soins épuré des virgules et espaces en trop.                                             |
| `insurance_provider`  | String        | Nom de l'assurance santé.                                                                                   |
| `billing_amount`      | Double / Null | Montant facturé (arrondi, transformé en null si négatif).                                                 |
| `room_number`         | Integer       | Numéro de chambre.                                                                                          |
| `admission_type`      | String        | Type d'admission (`Emergency`, `Urgent`, `Elective`).                                                  |
| `date_of_admission`   | String        | Date d'arrivée (`AAAA-MM-JJ`).                                                                            |
| `discharge_date`      | String        | Date de sortie (`AAAA-MM-JJ`).                                                                             |
| `medication`          | String        | Traitement prescrit.                                                                                         |
| `test_results`        | String        | Résultat d'examen (`Normal`, `Abnormal`, `Inconclusive`).                                             |
| `length_of_stay_days` | Integer       | **Nouveau champ calculé :** durée de séjour en jours (`discharge_date` – `date_of_admission`). |

### Exemple de document enregistré dans MongoDB :

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

## 8. Architecture Docker et Rangement des Fichiers

### Schéma du flux de données

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

### Organisation des dossiers et fichiers

```text
├── .env                        # Variables d'environnement locales (non envoyé sur Git)
├── .env.example                # Modèle de variables d'environnement (partagé sur Git)
├── .gitignore                  # Exclusion des fichiers sensibles pour Git (exclut .env)
├── Dockerfile                  # Instructions de fabrication de l'image Python
├── docker-compose.yml          # Définition et liaison des services MongoDB et Python
├── README.md                   # Guide d'utilisation et documentation technique
└── src/
    ├── data/
    │   └── healthcare_dataset.csv # Fichier CSV d'origine (préservé intact)
    ├── database.py             # Connexion sécurisée et attribution des rôles RBAC
    ├── main.py                 # Programme principal qui orchestre les 6 étapes
    ├── requirements.txt        # Librairies Python requises (pandas, pymongo)
    ├── test.py                 # Batterie de tests automatiques CRUD
    └── utils.py                # Fonctions de nettoyage, d'audit qualité et d'insertion
```

---

## 9. Pourquoi MongoDB et Docker ?

### MongoDB

* **Schéma flexible :** Permet d'intégrer facilement de nouveaux types d'analyses sans casser la base existante.
* **Recherches sans jointure :** Toutes les données du patient sont centralisées sur sa fiche pour des lectures directes.
* **Scalabilité horizontale :** Capacité native à répartir la charge sur plusieurs serveurs si le volume continue d'augmenter.

### Docker

* **Conteneurs légers :** Moins lourd qu'une machine virtuelle classique, démarrage quasi instantané.
* **Reproductibilité :** Le pipeline tourne de la même manière sur Windows, Mac ou un serveur Linux.
* **Données préservées :** Les données restent stockées dans le volume persistant `mongo_data` même si le conteneur s'éteint.

---

## 10. Validation des Tests (CRUD)

Le script `test.py` effectue un cycle complet de tests avec un patient témoin pour valider la bonne santé de la base avant la fin du script :

* **[TEST 1] Insertion patient témoin :** Vérification de l'écriture → **CREATE OK**
* **[TEST 2] Assertion présence en base :** Vérification de la lecture → **READ OK**
* **[TEST 3] Modification d'attribut :** Vérification de la mise à jour (âge passe à 31 ans) → **UPDATE OK**
* **[TEST 4] Purge du patient témoin :** Vérification de la suppression → **DELETE OK**

> **Sécurité du pipeline :** Chaque test repose sur une assertion. En cas d'erreur sur l'une des vérifications, le programme s'arrête immédiatement (*arrêt d'urgence*) pour signaler le dysfonctionnement.

---

## 11. Bilan Qualité du Nettoyage

Rapport affiché dans la console à la fin du traitement (`docker compose logs python_migration`) :

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

*Note : Les dossiers importés peuvent aussi être consultés graphiquement via le logiciel officiel **MongoDB Compass**.*

---

## 12. Indexation de la Collection

Les index permettent d'accélérer drastiquement les requêtes des médecins et soignants sans avoir à relire l'intégralité des 54 966 fiches :

| Champ Clé            | Pourquoi mettre un index ?                                                                                               |
| :-------------------- | :----------------------------------------------------------------------------------------------------------------------- |
| `_id`               | **Identifiant unique automatique :** permet à la base d'ouvrir la fiche d'un patient instantanément.             |
| `name`              | **Recherche par patient :** permet aux soignants de trouver directement un dossier au nom de famille sans latence. |
| `medical_condition` | **Recherche par maladie :** permet d'afficher en un clic tous les patients ayant une pathologie précise.          |
| `date_of_admission` | **Par date d'arrivée :** permet d'afficher rapidement les entrées ou de trier plus rapidement.                   |

---

## 13. Sécurité et Comptes d'Accès (RBAC)

Pour protéger les données de santé, l'accès à MongoDB suit le principe du moindre privilège : chaque profil ne dispose que des droits strictement nécessaires à son rôle.

| Rôle Logique             | Utilisateur  | Base Auth      | Droits MongoDB             | Périmètre d'Action & Moindre Privilège                                          |
| :------------------------ | :----------- | :------------- | :------------------------- | :--------------------------------------------------------------------------------- |
| **Super-Admin**     | `root`     | `admin`      | `root`                   | Provisionnement initial de l'instance Docker. Inactif pour l'applicatif.           |
| **Admin Infra**     | `dbadmin`  | `admin`      | `dbAdminAnyDatabase`     | Équipe DevOps pour maintenance système, défragmentation et indexation.          |
| **Service ETL**     | `migrator` | `medical_db` | `readWrite`, `dbAdmin` | Pipeline Python : ingestion et purge strictement cloisonnées à`medical_db`.    |
| **Audit / Métier** | `auditor`  | `medical_db` | `read`                   | Consultation en lecture seule stricte : impossibilité absolue d'altérer la base. |

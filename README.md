# Migration NoSQL : Pipeline de Données Médicales sous Docker

Ce projet permet de nettoyer, sécuriser et importer un fichier de 55 500 dossiers médicaux vers une base de données NoSQL MongoDB, en utilisant Docker pour que tout fonctionne automatiquement en une seule commande.

---

## Sommaire

1. [Cadrage de la Mission](#1-cadrage-de-la-mission)
2. [Comment Lancer la Migration (Guide Pas à Pas)](#2-comment-lancer-la-migration-guide-pas-à-pas)
3. [Ce qui se Passe Pendant la Migration (L&#39;Orchestrateur)](#3-ce-qui-se-passe-pendant-la-migration-lorchestrateur)
4. [Schéma de la Base de Données (Collection patients)](#4-schéma-de-la-base-de-données-collection-patients)
5. [Architecture Docker et Rangement des Fichiers](#5-architecture-docker-et-rangement-des-fichiers)
6. [Pourquoi MongoDB et Docker ?](#6-pourquoi-mongodb-et-docker-)
7. [Validation des Tests (CRUD)](#7-validation-des-tests-crud)
8. [Bilan Qualité du Nettoyage](#8-bilan-qualité-du-nettoyage)
9. [Indexation de la Collection](#9-indexation-de-la-collection)
10. [Sécurité et Comptes d&#39;Accès (RBAC)](#10-sécurité-et-comptes-daccès-rbac)

---

## 1. Cadrage de la Mission

* **Le Problème Initial :** Le client gère un fichier brut (`CSV`) de **55 500 dossiers de patients**. Ce fichier est devenu beaucoup trop lourd et trop lent à utiliser au quotidien pour les soignants.
* **La Solution Mise en Place :**
  - **Python (Le Nettoyage) :** Un programme qui lit le fichier, supprime les erreurs (doublons, noms mal écrits, montants négatifs) sans jamais abîmer le fichier d'origine.
  - **MongoDB (Le Stockage) :** Une base moderne et rapide, qui permet de retrouver un dossier immédiatement et de sécuriser les accès.
  - **Docker (Le Pack) :** Une boîte prête à l'emploi qui regroupe la base et le script pour que le projet tourne sur n'importe quel ordinateur sans rien installer de plus.

---

## 2. Comment Lancer la Migration (Guide Pas à Pas)

### 2.1 Lancer le projet

Cette commande prépare l'environnement Python, démarre la base MongoDB et lance automatiquement le nettoyage et l'import des données :

```bash
docker compose up --build -d
```

### 2.2 Vérifier que tout s'est bien passé (Voir les logs)

Cette commande affiche le rapport de nettoyage et confirme que les tests ont réussi :

```bash
docker compose logs python_migration
```

### 2.3 Se connecter à la base en toute sécurité (Mode Consultation)

Pour vérifier les données dans MongoDB avec un compte en lecture seule (qui ne peut rien casser ni modifier) :

```bash
docker exec -it mongodb_server mongosh -u auditor -p auditor_password123 --authenticationDatabase medical_db
```

### 2.4 Vérifier les données dans MongoDB

Une fois connecté dans le terminal MongoDB, tapez ces instructions simples :

```javascript
use medical_db
db.patients.countDocuments()   // Doit afficher 54966
db.patients.findOne()          // Affiche la fiche complète d'un patient
exit                           // Pour quitter
```

### 2.5 Tout arrêter et remettre à zéro

Pour stopper les conteneurs et effacer les données enregistrées afin de repartir d'une base propre :

```bash
docker compose down -v
```

---

## 3. Ce qui se Passe Pendant la Migration (L'Orchestrateur)

Le fichier `main.py` est le chef d'orchestre du projet. Dès que Docker démarre, il exécute automatiquement ces 6 étapes dans l'ordre :

1. **Étape 1 :** Créer les comptes utilisateurs et définir leurs droits s'ils n'existent pas encore (`setup_database_roles()`).
2. **Étape 2 :** Trouver où est rangé le fichier CSV des données médicales (`healthcare_dataset.csv`).
3. **Étape 3 :** Se connecter à MongoDB et ouvrir la collection `patients` dans la base `medical_db`.
4. **Étape 4 :** Charger le CSV et corriger toutes les erreurs (`load_and_clean_data()`) : suppression des doublons, remise au propre des noms, et calcul de la durée du séjour.
5. **Étape 5 :** Envoyer tous les dossiers propres dans MongoDB et poser les index (`migrate_data()`).
6. **Étape 6 :** Faire un test rapide (ajouter, lire, modifier, supprimer un faux patient) pour vérifier que la base répond parfaitement (`test_crud()`).

---

## 4. Schéma de la Base de Données (Collection patients)

Chaque patient est enregistré sous la forme d'une fiche complète (un document BSON). Aucun tableau séparé n'est nécessaire.

| Champ                   | Type          | Description et Règle Métier                                                                                          |
| :---------------------- | :------------ | :--------------------------------------------------------------------------------------------------------------------- |
| `_id`                 | ObjectId      | Numéro unique créé automatiquement par MongoDB.                                                                     |
| `name`                | String        | Nom et prénom propres avec civilité conservée (`Mr.`, `Dr.`).                                                   |
| `age`                 | Integer       | Âge du patient.                                                                                                       |
| `gender`              | String        | Sexe du patient (`Male`, `Female`).                                                                                |
| `blood_type`          | String        | Groupe sanguin vérifié (`A+`, `O-`, etc.).                                                                       |
| `medical_condition`   | String        | Maladie ou diagnostic (ex. : Cancer, Diabète, Asthme).                                                                |
| `doctor`              | String        | Nom du médecin traitant remis au propre.                                                                              |
| `hospital`            | String        | Nom de l'hôpital nettoyé des virgules et espaces en trop.                                                            |
| `insurance_provider`  | String        | Nom de l'assurance santé.                                                                                             |
| `billing_amount`      | Double / Null | Montant de la facture (remplacé par vide si le montant était négatif).                                              |
| `room_number`         | Integer       | Numéro de la chambre.                                                                                                 |
| `admission_type`      | String        | Type d'entrée (`Emergency`, `Urgent`, `Elective`).                                                              |
| `date_of_admission`   | String        | Date d'entrée à l'hôpital (`AAAA-MM-JJ`).                                                                         |
| `discharge_date`      | String        | Date de sortie de l'hôpital (`AAAA-MM-JJ`).                                                                         |
| `medication`          | String        | Médicament prescrit.                                                                                                  |
| `test_results`        | String        | Résultat d'examen (`Normal`, `Abnormal`, `Inconclusive`).                                                       |
| `length_of_stay_days` | Integer       | **Nouveau champ calculé :** nombre de jours passés à l'hôpital (`discharge_date` - `date_of_admission`). |

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

## 5. Architecture Docker et Rangement des Fichiers

### Schéma du fonctionnement

```text
┌────────────────────────────────────────────────────────────────────────┐
│                                DOCKER                                  │
│                                                                        │
│   [ Fichier Source CSV ] ──> [ Scripts Python ] ──> [ Base MongoDB ]   │
│      (55 500 lignes)          - main.py             (medical_db)       │
│      Dossier partagé          - utils.py            Port 27017         │
│      src/data                 - database.py         Dossier persistant │
│                               - test.py             mongo_data         │
└────────────────────────────────────────────────────────────────────────┘
```

### Organisation des dossiers

```text
├── Dockerfile                  # Recette pour construire l'image Python
├── docker-compose.yml          # Fichier qui démarre MongoDB et Python ensemble
├── README.md                   # Guide d'utilisation du projet
└── src/
    ├── data/
    │   └── healthcare_dataset.csv # Fichier CSV d'origine (non modifié)
    ├── database.py             # Script qui gère la connexion et crée les utilisateurs
    ├── main.py                 # Script principal qui lance toutes les étapes
    ├── requirements.txt        # Liste des outils Python utilisés (pandas, pymongo)
    ├── test.py                 # Script qui vérifie le bon fonctionnement de la base
    └── utils.py                # Fonctions qui nettoient et transfèrent les données
```

---

## 6. Pourquoi MongoDB et Docker ?

### MongoDB

* **Format flexible :** On peut rajouter de nouvelles informations sur les fiches des patients plus tard sans tout casser.
* **Recherches directes :** Toutes les informations d'un patient sont regroupées sur sa fiche, sans avoir besoin de faire des liaisons lentes entre plusieurs tableaux.
* **Évolutif :** La base est capable d'accueillir des millions de dossiers supplémentaires sans perte de vitesse.

### Docker

* **Rapide et léger :** Les conteneurs démarrent en quelques secondes et consomment très peu de mémoire.
* **Fonctionne partout :** Le projet tourne exactement de la même manière sur Windows, Mac ou Linux.
* **Données conservées :** Même si on éteint Docker, les dossiers patients restent stockés en sécurité grâce au volume `mongo_data`.

---

## 7. Validation des Tests (CRUD)

À la fin de l'importation, le fichier `test.py` effectue 4 vérifications automatiques avec un faux patient pour prouver que la base fonctionne bien :

* **[TEST 1] CREATE :** On ajoute un patient témoin dans la base → **CREATE OK**
* **[TEST 2] READ :** On recherche ce patient et on vérifie qu'il existe bien → **READ OK**
* **[TEST 3] UPDATE :** On modifie son âge (de 30 à 31 ans) pour vérifier l'enregistrement → **UPDATE OK**
* **[TEST 4] DELETE :** On supprime ce faux patient pour laisser la base propre → **DELETE OK**

> **Sécurité :** Si une seule de ces 4 étapes échoue, le programme s'arrête immédiatement et signale une erreur.

---

## 8. Bilan Qualité du Nettoyage

Voici le rapport affiché par le conteneur Python à la fin du traitement (`docker compose logs python_migration`) :

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

*Note : Les données peuvent aussi être visualisées très facilement avec l'application graphique **MongoDB Compass**.*

---

## 9. Indexation de la Collection

Un index fonctionne comme l'index à la fin d'un gros livre : au lieu de relire les 54 966 lignes une par une, la base va directement à la bonne page.

| Champ Clé            | Pourquoi mettre un index ?                                                                                               |
| :-------------------- | :----------------------------------------------------------------------------------------------------------------------- |
| `_id`               | **Identifiant unique :** permet d'ouvrir la fiche d'un patient instantanément.                                    |
| `name`              | **Recherche par patient :** permet aux soignants de trouver directement un patient par son nom de famille.         |
| `medical_condition` | **Recherche par maladie :** permet d'afficher en un clic tous les patients qui ont une maladie précise.           |
| `date_of_admission` | **Par date d'arrivée :** permet d'afficher rapidement les arrivées récentes ou de faire des tris dans le temps. |

---

## 10. Sécurité et Comptes d'Accès (RBAC)

Pour éviter les accidents ou les vols de données, chaque compte a uniquement les droits nécessaires pour accomplir sa tâche (principe du moindre privilège) :

| Rôle Logique             | Nom Utilisateur | Base           | Droits                     | Rôle et Explication                                                                |
| :------------------------ | :-------------- | :------------- | :------------------------- | :---------------------------------------------------------------------------------- |
| **Super-Admin**     | `root`        | `admin`      | `root`                   | Sert uniquement à créer la base au tout début. Inactif pour l'application.       |
| **Admin Infra**     | `dbadmin`     | `admin`      | `dbAdminAnyDatabase`     | Pour les équipes techniques (maintenance, nettoyage, index).                       |
| **Service ETL**     | `migrator`    | `medical_db` | `readWrite`, `dbAdmin` | Utilisé par le script Python pour insérer et modifier les données médicales.    |
| **Audit / Métier** | `auditor`     | `medical_db` | `read`                   | Réservé à la consultation : impossible de supprimer ou de modifier des données. |

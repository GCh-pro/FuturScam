# Documentation Technique - FuturScam ETL

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Composants principaux](#composants-principaux)
4. [Flux de données](#flux-de-données)
5. [Schéma de données](#schéma-de-données)
6. [Dépendances](#dépendances)
7. [Configuration](#configuration)
8. [Déploiement et exécution](#déploiement-et-exécution)
9. [Gestion des erreurs](#gestion-des-erreurs)
10. [Monitoring et logs](#monitoring-et-logs)
11. [Sécurité](#sécurité)
12. [Maintenance](#maintenance)

---

## 🎯 Vue d'ensemble

### Description

FuturScam ETL est un système d'extraction, transformation et chargement (ETL) automatisé conçu pour collecter des offres de missions freelance IT (RFPs - Request For Proposals) depuis deux sources principales :

1. **Emails entrants** (via Microsoft Graph API)
2. **API Boond Manager** (système de gestion de missions)

### Objectifs

- **Automatisation** : Extraction et traitement automatique des RFPs
- **Enrichissement** : Amélioration des descriptions via ChatGPT (GPT-4)
- **Normalisation** : Transformation des données vers un format MongoDB unifié
- **Notification** : Envoi d'alertes personnalisées aux utilisateurs abonnés
- **Incrémentalité** : Traitement uniquement des données nouvelles/modifiées

### Technologies utilisées

- **Python 3.x** : Langage principal
- **MongoDB** : Base de données NoSQL (via API REST)
- **Azure Active Directory** : Authentification Microsoft Graph
- **OpenAI GPT-4** : Enrichissement NLP
- **Boond Manager API** : Source de données métier
- **Microsoft Graph API** : Extraction d'emails

---

## 🏗️ Architecture

### Architecture globale

```
┌─────────────────────────────────────────────────────────────────┐
│                         FuturScam ETL                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐       ┌──────────────┐                       │
│  │   Sources    │       │ Enrichment   │                       │
│  ├──────────────┤       ├──────────────┤                       │
│  │ MS Graph API │──────▶│  ChatGPT     │                       │
│  │ Boond API    │       │  GPT-4o      │                       │
│  └──────────────┘       └──────────────┘                       │
│         │                       │                               │
│         ▼                       ▼                               │
│  ┌─────────────────────────────────────┐                       │
│  │        Transformation Layer         │                       │
│  │  ┌──────────────┐  ┌──────────────┐ │                       │
│  │  │ Pro Unity    │  │ Boond        │ │                       │
│  │  │ Mapper       │  │ Mapper       │ │                       │
│  │  └──────────────┘  └──────────────┘ │                       │
│  └─────────────────────────────────────┘                       │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────┐                       │
│  │         MongoDB API                 │                       │
│  │  (http://localhost:8000/mongodb)    │                       │
│  └─────────────────────────────────────┘                       │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────┐                       │
│  │    Subscription Notifier            │                       │
│  │  (Email notifications to users)     │                       │
│  └─────────────────────────────────────┘                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Structure des répertoires

```
FuturScam/
├── src/
│   ├── __init__.py
│   └── main.py                    # Point d'entrée principal de l'ETL
├── app/
│   ├── __init__.py
│   ├── boond_manager_extractor.py # Extraction depuis Boond Manager API
│   ├── job_completer.py           # Enrichissement ChatGPT
│   ├── job_mail_exporter.py       # Extraction d'emails MS Graph
│   ├── subscription_notifier.py   # Notifications aux abonnés
│   └── attachments/               # Stockage temporaire des JSON extraits
├── mappers/
│   ├── __init__.py
│   ├── mapper_to_mongo.py         # Moteur de mapping générique
│   ├── boond_mappings.py          # Mapping Boond → MongoDB
│   └── pro_unity_mappings.py      # Mapping Pro Unity → MongoDB
├── helpers/
│   ├── __init__.py                # Utilitaires (get_by_path, set_by_path...)
├── params.py                      # Configuration et secrets
├── requirements.txt               # Dépendances Python
├── .last_execution                # Timestamp de la dernière exécution
├── run_etl_continuous.ps1         # Script d'exécution continue
├── run_etl_continuous.bat         # Version Batch
├── ETL_SETUP.md                   # Guide de déploiement
└── TECHNICAL_DOCUMENTATION.md     # Ce document
```

---

## 🔧 Composants principaux

### 1. **src/main.py** - Orchestrateur principal

**Responsabilités :**
- Lecture du timestamp de dernière exécution (`.last_execution`)
- Orchestration du flux ETL complet
- Gestion de la sauvegarde du nouveau timestamp
- Nettoyage des RFPs expirées et fermées
- Coordination des notifications aux abonnés

**Fonctions clés :**

```python
def main():
    """
    Point d'entrée principal de l'ETL.
    
    Workflow:
    1. Récupération du dernier timestamp d'exécution
    2. Traitement des emails (Pro Unity)
    3. Traitement des opportunités Boond Manager
    4. Nettoyage des RFPs expirées/fermées
    5. Envoi des notifications aux abonnés
    6. Sauvegarde du nouveau timestamp
    """
```

**Timestamp incrémental :**
- Stocké dans `.last_execution` (format ISO 8601)
- Précision à la microseconde
- Ajout automatique de +1ms pour éviter les doublons
- UTC timezone-aware

---

### 2. **app/job_mail_exporter.py** - Extraction d'emails

**Responsabilités :**
- Authentification OAuth2 via Azure AD (client credentials flow)
- Extraction des emails avec préfixe `[JOB EXPORT]`
- Filtrage par date de réception (incrémental)
- Téléchargement et sauvegarde des pièces jointes JSON

**Méthodes principales :**

```python
def authenticate(self):
    """Authentification via MSAL (Microsoft Authentication Library)"""

def get_filtered_emails(self, subject_prefix="[JOB EXPORT]", cutoff_datetime=None):
    """
    Récupération des emails filtrés.
    
    Args:
        subject_prefix: Filtre sur le sujet
        cutoff_datetime: Timestamp UTC pour filtrage incrémental
    
    Returns:
        Liste des emails correspondant aux critères
    """

def save_attachments(self, mail):
    """
    Télécharge et sauvegarde les pièces jointes JSON uniquement.
    Les fichiers sont stockés dans app/attachments/
    """
```

**Flow d'authentification :**
```
Client App (FuturScam ETL)
    │
    ├──► Azure AD Token Endpoint
    │    (avec client_id + client_secret)
    │
    ├──► Obtention du Access Token
    │
    └──► MS Graph API
         (avec Bearer token)
         └──► GET /users/{user}/messages
```

---

### 3. **app/boond_manager_extractor.py** - Extraction Boond

**Responsabilités :**
- Authentification JWT (HS256) avec Boond Manager API
- Récupération des opportunités (RFPs)
- Filtrage par date de modification (`updateDate`)
- Extraction des détails complets via endpoint `/information`
- Extraction des compétences/langues via ChatGPT

**Méthodes principales :**

```python
def fetch_boond_opportunities():
    """
    Récupère toutes les opportunités depuis Boond Manager.
    Utilise JWT avec signature HS256.
    
    Returns:
        dict: Réponse JSON de l'API Boond
    """

def filter_recent_opportunities(data: dict, cutoff_date: datetime, job_enhancer=None):
    """
    Filtre les opportunités modifiées après cutoff_date.
    Pour chaque opportunité filtrée:
    - Récupère les détails complets
    - Extrait skills/languages via ChatGPT (si job_enhancer fourni)
    
    Returns:
        list: Liste des opportunités détaillées
    """

def transform_boond_to_mongo_format(opportunity: dict):
    """
    Transformation Boond → MongoDB via le moteur de mapping.
    Applique les règles de mapping et les post-traitements.
    """
```

**Authentification JWT :**
```python
payload = {
    "clientToken": params.CLIENT_BM,
    "clientKey": params.TOKEN_BM,
    "userToken": params.USER_BM
}
jwt_token = jwt.encode(payload, params.TOKEN_BM, algorithm="HS256")
```

---

### 4. **app/job_completer.py** - Enrichissement ChatGPT

**Responsabilités :**
- Extraction automatique des compétences et langues depuis texte libre
- Enrichissement et structuration des descriptions de poste
- Catégorisation automatique des RFPs (RFP_type)
- Génération de HTML structuré et propre

**Classe principale :**

```python
class JobDescriptionEnhancer:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
```

**Méthodes clés :**

```python
def extract_skills_and_languages(self, criteria: str, description: str = "") -> dict:
    """
    Extraction NLP des compétences techniques et langues.
    
    Args:
        criteria: Critères de la mission
        description: Description complète
    
    Returns:
        {
            "skills": ["Python", "React", "AWS", ...],
            "languages": ["Français", "Anglais", ...]
        }
    """

def enhance_job_description_html(self, job_description: str) -> dict:
    """
    Enrichissement et structuration de la description.
    
    Returns:
        {
            "RFP_type": "Data, AI, BI",
            "job_description": "<section>...</section>"
        }
    """
```

**Catégories RFP_type disponibles :**
- Go-To-Market, Sales B2B
- Data, AI, BI
- Integration, API, Architecture
- Cybersecurity
- Cloud, Infrastructure
- Software Engineering
- PMO, Project Management
- Business Analysis
- Support & Operations
- Autre

**Template HTML généré :**
```html
<section>
  <h2>Contexte de la mission</h2>
  <p>…</p>
</section>

<section>
  <h2>Responsabilités principales</h2>
  <ul><li>…</li></ul>
</section>

<section>
  <h2>Profil recherché</h2>
  <ul><li>…</li></ul>
</section>

<section>
  <h2>Compétences techniques</h2>
  <ul><li>…</li></ul>
</section>

<section>
  <h2>Soft Skills</h2>
  <ul><li>…</li></ul>
</section>
```

---

### 5. **app/subscription_notifier.py** - Notifications

**Responsabilités :**
- Récupération des utilisateurs avec abonnements (metadata.role='abonnements')
- Filtrage des RFPs par catégorie (RFP_type)
- Génération d'emails HTML personnalisés
- Envoi via API `/mail`

**Workflow :**
```
1. Récupérer tous les utilisateurs ayant des abonnements
   └─► GET /users → Filtrer metadata.role == "abonnements"

2. Pour chaque utilisateur:
   └─► Pour chaque abonnement de l'utilisateur:
       └─► Filtrer les nouvelles RFPs où RFP_type correspond

3. Si l'utilisateur a des RFPs correspondantes:
   └─► Générer 1 email avec TOUTES les RFPs de TOUS ses abonnements
   └─► POST /mail (envoi de l'email)
```

**Méthodes principales :**

```python
def get_users_with_subscriptions(self) -> List[Dict]:
    """Récupère les utilisateurs ayant des metadata.role='abonnements'"""

def get_new_rfps_for_subscription(self, subscription_name: str, all_new_rfps: List[Dict]):
    """Filtre les RFPs par correspondance RFP_type ~ subscription_name"""

def generate_email_body(self, user_name: str, subscriptions_rfps: Dict[str, List[Dict]]):
    """Génère un email HTML avec toutes les RFPs de tous les abonnements"""

def notify_all_subscribers(self, new_rfps: List[Dict]):
    """
    Envoie 1 email par utilisateur contenant toutes les nouvelles RFPs
    correspondant à leurs abonnements.
    """
```

---

### 6. **mappers/** - Moteur de transformation

#### 6.1 **mapper_to_mongo.py** - Moteur générique

**Concept :**
Moteur de mapping déclaratif permettant de transformer n'importe quelle structure JSON vers le format MongoDB unifié.

**Fonction principale :**

```python
def map_json(source: dict, mapping: dict, list_mappings: dict) -> dict:
    """
    Transforme un document source vers le format destination.
    
    Args:
        source: Document source (dict)
        mapping: Dictionnaire de mappings simples {src_path: dst_path}
        list_mappings: Mappings de listes avec transformations
    
    Returns:
        Document transformé au format destination
    """
```

**Exemples de mappings :**

```python
# Mapping simple
mapping = {
    "data.attributes.title": "roleTitle",
    "data.attributes.reference": "job_id"
}

# Mapping de listes avec transformation
list_mappings = {
    "data.attributes.skills": (
        "skills",                          # Chemin destination
        {"name": "name", "level": "seniority"},  # Mapping des champs
        lambda src, dst: dst               # Fonction de transformation optionnelle
    )
}
```

#### 6.2 **boond_mappings.py** - Mapping Boond

**Responsabilités :**
- Définition des règles de mapping Boond → MongoDB
- Énumérations (types d'origine, etc.)
- Post-traitements spécifiques (extraction company depuis `included`, dates, etc.)

**Mappings principaux :**

```python
BOOND_TO_MONGO_MAPPING = {
    # Company info
    "data.attributes.place": "company.city",
    "data.attributes.companyName": "company.name",
    
    # Conditions
    "data.attributes.startDate": "conditions.fromAt",
    "data.attributes.dailyRate": "conditions.dailyRate.min",
    
    # Top-level
    "data.attributes.reference": "job_id",
    "data.attributes.title": "roleTitle",
    "data.attributes.description": "job_desc",
}

BOOND_LIST_MAPPINGS = {
    "data.attributes.skills": ("skills", {...}, transform_fn),
    "data.attributes.extracted_skills": ("skills_from_chatgpt", {...}, transform_fn),
}
```

**Post-traitements (`apply_boond_defaults`) :**
- Extraction du nom de la société depuis `included` (relations Boond)
- Extraction du manager (mainManager) → metadata avec email généré
- Validation et normalisation des dates
- Gestion des valeurs par défaut (deadlineAt → 9999-12-31 si vide)
- Fusion des skills/languages (Boond + ChatGPT)
- Transformation `serviceProvider` (ID → texte via enum)

#### 6.3 **pro_unity_mappings.py** - Mapping Pro Unity

**Responsabilités :**
- Mapping JSON Pro Unity → MongoDB
- Post-traitements pour valeurs par défaut

```python
MAPPING = {
    "locationInfo.mainLocation.city": "company.city",
    "budgetInfo.minDailyRate": "conditions.dailyRate.min",
    "roleInfo.roles[0].name": "roleTitle",
    # ...
}

LIST_MAPPINGS = {
    "skillInfo.skills": ("skills", {"name": "name", "seniority": "seniority"}, ...),
    "languageInfo.languageGroups": ("languages", {...}, ...),
}
```

---

## 📊 Flux de données

### Flux ETL complet

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. LECTURE DU TIMESTAMP                                             │
│    └─► Fichier .last_execution → datetime UTC                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. EXTRACTION EMAILS (Pro Unity)                                    │
│    ├─► Authentification Azure AD (OAuth2)                           │
│    ├─► GET MS Graph API (filter: receivedDateTime > last_execution) │
│    ├─► Téléchargement pièces jointes JSON                          │
│    └─► Sauvegarde dans app/attachments/                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. TRANSFORMATION EMAILS                                            │
│    ├─► Pour chaque fichier JSON dans attachments/                  │
│    ├─► Mapping via pro_unity_mappings.py                           │
│    ├─► Enrichissement ChatGPT (job_desc + RFP_type)                │
│    ├─► POST /mongodb (création/mise à jour)                        │
│    └─► Suppression du fichier JSON traité                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. EXTRACTION BOOND                                                 │
│    ├─► Authentification JWT (HS256)                                │
│    ├─► GET /api/opportunities (tous)                               │
│    ├─► Filtrage par updateDate > last_execution                    │
│    ├─► Pour chaque opportunité récente:                            │
│    │   ├─► GET /api/opportunities/{id}/information                 │
│    │   └─► Extraction skills/languages via ChatGPT                 │
│    └─► Cleanup des opportunités fermées (state != 0)               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. TRANSFORMATION BOOND                                             │
│    ├─► Pour chaque opportunité (state == 0 uniquement)             │
│    ├─► Mapping via boond_mappings.py                               │
│    ├─► Extraction company/manager depuis 'included'                │
│    ├─► Enrichissement ChatGPT (job_desc + RFP_type)                │
│    ├─► Application règle tarifaire (-15%, min 65€, max 120€)       │
│    └─► POST /mongodb (création) OU PUT /mongodb/{id} (update)      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. NETTOYAGE                                                        │
│    ├─► GET /mongodb (toutes les RFPs)                              │
│    ├─► Filtrage deadlineAt < today()                               │
│    └─► DELETE /mongodb/{id} pour chaque RFP expirée                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. NOTIFICATIONS                                                    │
│    ├─► GET /users (avec metadata.role='abonnements')               │
│    ├─► Pour chaque utilisateur:                                    │
│    │   ├─► Filtrer nouvelles RFPs par RFP_type ~ subscription      │
│    │   ├─► Générer email HTML personnalisé                         │
│    │   └─► POST /mail                                              │
│    └─► Log du nombre d'emails envoyés                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 8. SAUVEGARDE TIMESTAMP                                             │
│    └─► Écriture dans .last_execution (current_time + 1ms)          │
└─────────────────────────────────────────────────────────────────────┘
```

### Gestion des duplicatas

**Pro Unity (Emails) :**
- POST /mongodb tente la création
- Si erreur `duplicate key` (E11000) → Fallback automatique sur PUT /mongodb/{job_id}
- Garantit l'idempotence

**Boond Manager :**
- Utilise `reference` comme `job_id` (unique dans MongoDB)
- Même mécanisme de fallback POST → PUT

---

## 📐 Schéma de données

### Format MongoDB unifié (MissionRequestPending)

```json
{
  "job_id": "string (unique)",
  "roleTitle": "string",
  "job_desc": "string (HTML enrichi)",
  "job_url": "string",
  "seniority": "NS | Junior | Medior | Senior",
  "remoteOption": "OnSite | Remote | Hybrid | NotSpecified",
  "isActive": "boolean",
  "RFP_type": "Data, AI, BI | Cybersecurity | ...",
  
  "company": {
    "name": "string",
    "city": "string",
    "country": "string",
    "street": "string",
    "zipcode": "string",
    "region": "string"
  },
  
  "conditions": {
    "dailyRate": {
      "currency": "EUR",
      "min": "number | null",
      "max": "number | null"
    },
    "fixedMargin": "number",
    "fromAt": "ISO 8601 date",
    "toAt": "ISO 8601 date",
    "startImmediately": "boolean",
    "occupation": "FullTime | PartTime | ..."
  },
  
  "skills": [
    {
      "name": "string",
      "seniority": "Required | Nice to have | ..."
    }
  ],
  
  "languages": [
    {
      "language": "string",
      "level": "string"
    }
  ],
  
  "publishedAt": "ISO 8601 datetime",
  "deadlineAt": "ISO 8601 datetime",
  "serviceProvider": "string",
  
  "metadata": [
    {
      "name": "string",
      "mail": "string",
      "role": "operator | abonnements | ..."
    }
  ]
}
```

### Règles de transformation

#### Règle tarifaire (Budget)
Appliquée dans `save_to_mongodb_api()` :
```python
# Formule: -15% avec min 65€ et max 120€
calculated = original * 0.85
final = max(65, min(120, calculated))
```

#### Dates par défaut
- `publishedAt` : Date courante si absente
- `deadlineAt` : `9999-12-31T23:59:59` si vide/null (Boond)
- `fromAt` / `toAt` : Validées et normalisées en ISO 8601

#### Valeurs par défaut
- `seniority` : `"NS"` (Not Specified)
- `remoteOption` : `"NotSpecified"`
- `company.name` : `"Unknown Company"`
- `conditions.occupation` : `"FullTime"`
- `conditions.startImmediately` : `false`

---

## 📦 Dépendances

### requirements.txt

```
requests       # Requêtes HTTP (Graph API, Boond API, MongoDB API)
msal           # Microsoft Authentication Library (Azure AD)
pymongo        # Driver MongoDB (si connexion directe)
openAI         # SDK OpenAI pour ChatGPT
pyjwt          # Génération de tokens JWT pour Boond
```

### Environnements

**Python :**
- Version recommandée : Python 3.9+
- Encodage : UTF-8

**Système d'exploitation :**
- Windows 10/11 (scripts .ps1 / .bat)
- Compatibilité Linux possible (adapter les scripts shell)

---

## ⚙️ Configuration

### params.py - Fichier de configuration

```python
# MongoDB API
MONGO_URI = "mongodb+srv://user:password@cluster.mongodb.net/"

# Azure AD (Microsoft Graph)
AZURE_CLIENT = "application_client_id"
AZURE_URI = "https://login.microsoftonline.com/{tenant_id}"
AZURE_SECRET = "client_secret"
AZURE_USER_EMAIL = "user@domain.be"

# Boond Manager API
CLIENT_BM = "hex_encoded_client"
TOKEN_BM = "hex_encoded_token"
USER_BM = "hex_encoded_user"

# OpenAI
OPENAI_API_KEY = "sk-..."
```

### Variables d'environnement (alternative recommandée)

Pour la production, il est préférable d'utiliser des variables d'environnement :

```python
# params.py (version sécurisée)
import os

MONGO_URI = os.getenv("MONGO_URI")
AZURE_CLIENT = os.getenv("AZURE_CLIENT")
AZURE_SECRET = os.getenv("AZURE_SECRET")
# ...
```

### Configuration Azure AD

**Permissions Microsoft Graph requises :**
- `Mail.Read` (Application)
- `User.Read.All` (Application)

**Configuration de l'application Azure AD :**
1. Créer une App Registration dans Azure Portal
2. Ajouter un client secret
3. Assigner les permissions API (Graph API)
4. Consentement admin requis

---

## 🚀 Déploiement et exécution

### Installation

```powershell
# Cloner le repository
cd C:\Users\Guillaume_Chinzi\code\FuturScam

# Installer les dépendances
pip install -r requirements.txt

# Configurer params.py avec vos credentials
```

### Modes d'exécution

#### 1. **Exécution unique**

```powershell
# PowerShell
python src\main.py

# Ou via script
.\run_etl.ps1
```

#### 2. **Exécution continue (Always-on)**

```powershell
# Intervalle par défaut (1 heure)
.\run_etl_continuous.ps1

# Intervalle personnalisé (30 minutes)
.\run_etl_continuous.ps1 -IntervalMinutes 30

# Intervalle de test (5 minutes)
.\run_etl_continuous.ps1 -IntervalMinutes 5
```

**Arrêt :** `Ctrl+C`

#### 3. **Planificateur de tâches Windows**

Voir [ETL_SETUP.md](ETL_SETUP.md) pour configuration détaillée.

**Création rapide via PowerShell :**
```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument '-ExecutionPolicy Bypass -File "C:\Users\Guillaume_Chinzi\code\FuturScam\run_etl_continuous.ps1"' `
    -WorkingDirectory "C:\Users\Guillaume_Chinzi\code\FuturScam"

$trigger = New-ScheduledTaskTrigger `
    -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask `
    -TaskName "FuturScam ETL" `
    -Action $action `
    -Trigger $trigger
```

#### 4. **Exécution en arrière-plan**

```powershell
# Lancer en arrière-plan (fenêtre cachée)
Start-Process powershell -ArgumentList `
    "-ExecutionPolicy Bypass -File .\run_etl_continuous.ps1 -IntervalMinutes 60" `
    -WindowStyle Hidden

# Arrêter le processus
Get-Process python | Where-Object {$_.CommandLine -like "*main.py*"} | Stop-Process
```

### Réinitialisation

**Forcer le retraitement de toutes les données :**
```powershell
# Supprimer le fichier de timestamp
Remove-Item .last_execution

# Ou le redéfinir à une date spécifique
Set-Content .last_execution "2025-01-01T00:00:00.000000"
```

---

## ⚠️ Gestion des erreurs

### Stratégie de gestion des erreurs

**Principe : Idempotence**
- Si une erreur survient, le timestamp `.last_execution` n'est **PAS** mis à jour
- La prochaine exécution retraitera les mêmes données
- Garantit qu'aucune donnée n'est perdue

### Gestion par composant

#### 1. **Extraction emails**
```python
try:
    response = requests.get(url, headers=self.headers)
    response.raise_for_status()
except Exception as e:
    print(f"[ERROR] Error fetching emails: {e}")
    return []  # Retourne liste vide, continue avec Boond
```

#### 2. **Extraction Boond**
```python
if response.status_code != 200:
    print(f"Error: received status code {response.status_code}")
    return None  # Échec de la récupération complète
```

#### 3. **Enrichissement ChatGPT**
```python
try:
    result = job_enhancer.enhance_job_description_html(job_desc)
except Exception as e:
    print(f"[ERROR] Error enhancing: {e}")
    return rfp_document  # Retourne document non enrichi (fallback)
```

#### 4. **Sauvegarde MongoDB**
```python
# Tentative POST (création)
if response.status_code == 400 and "duplicate key" in response.text:
    # Fallback automatique vers PUT (mise à jour)
    update_response = requests.put(f"{api_url}/mongodb/{job_id}", ...)
```

### Logs d'erreur

**Niveaux de log :**
- `[OK]` : Succès
- `[INFO]` : Information
- `[WARN]` : Avertissement (erreur non bloquante)
- `[ERROR]` : Erreur critique
- `[DEBUG]` : Debug (développement)

**Exemple :**
```
[ERROR] MongoDB API error: status 500
Response: Internal Server Error
[WARN] Last execution timestamp NOT updated due to error
```

### Retry logic

**Actuellement :** Pas de retry automatique

**Recommandation pour production :**
```python
import time
from functools import wraps

def retry(max_attempts=3, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    print(f"[RETRY] Attempt {attempt+1} failed: {e}")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3, delay=10)
def save_to_mongodb_api(rfp_document: dict, api_url: str):
    # ...
```

---

## 📊 Monitoring et logs

### Logs générés

**Affichage console :**
Tous les logs sont écrits sur `stdout` avec préfixes clairs.

**Capture dans fichier :**
```powershell
# Redirection vers fichier log
python src\main.py >> logs\etl_$(Get-Date -Format 'yyyyMMdd_HHmmss').log 2>&1
```

### Métriques importantes

**À surveiller :**
- Nombre d'emails traités
- Nombre d'opportunités Boond traitées
- Nombre de RFPs créées/mises à jour
- Nombre de RFPs expirées supprimées
- Nombre de notifications envoyées
- Durée d'exécution totale
- Erreurs API (taux de réussite)

**Exemple de sortie :**
```
[SUMMARY]
  - Email RFPs saved: 5
  - Boond RFPs saved: 12
  - Expired RFPs deleted: 3
  - Total RFPs saved: 17
[SUMMARY] Sent 8 subscription notification email(s) to 8 user(s)
```

### Monitoring de santé

**Fichier `.last_execution` :**
```powershell
# Vérifier la dernière exécution
Get-Content .last_execution

# Exemple de sortie
2026-01-14T15:32:10.123456
```

**Vérifier l'âge du dernier run :**
```powershell
$lastRun = Get-Content .last_execution | ConvertTo-DateTime
$age = (Get-Date) - $lastRun
if ($age.TotalHours -gt 2) {
    Write-Host "WARNING: ETL hasn't run in $($age.TotalHours) hours"
}
```

### Alerting (recommandé)

**Intégration avec outils de monitoring :**
- **Email alerts** : Envoyer un email en cas d'échec
- **Slack/Teams** : Webhook pour notifications
- **Prometheus** : Export de métriques
- **Datadog/New Relic** : APM monitoring

---

## 🔒 Sécurité

### Gestion des secrets

**⚠️ CRITIQUE : params.py contient des secrets en clair**

**Problèmes identifiés :**
1. ✅ Credentials Azure AD exposés
2. ✅ Clés API OpenAI exposées
3. ✅ Tokens Boond exposés
4. ✅ Credentials MongoDB exposés

**Recommandations :**

#### 1. **Utiliser des variables d'environnement**

```python
# params.py (version sécurisée)
import os
from dotenv import load_dotenv

load_dotenv()  # Charge .env

MONGO_URI = os.getenv("MONGO_URI")
AZURE_CLIENT = os.getenv("AZURE_CLIENT")
AZURE_SECRET = os.getenv("AZURE_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# ...
```

**Fichier `.env` (à ajouter dans `.gitignore`) :**
```
MONGO_URI=mongodb+srv://...
AZURE_CLIENT=xxx
AZURE_SECRET=xxx
OPENAI_API_KEY=sk-...
```

#### 2. **Azure Key Vault (recommandé pour production)**

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://myvault.vault.azure.net/", credential=credential)

MONGO_URI = client.get_secret("mongo-uri").value
OPENAI_API_KEY = client.get_secret("openai-api-key").value
```

#### 3. **Hashicorp Vault**

### Permissions

**Principe du moindre privilège :**

**Azure AD Application :**
- ✅ `Mail.Read` (lecture seule)
- ❌ Pas de `Mail.ReadWrite` (éviter modification)

**MongoDB :**
- ✅ Accès limité à la collection `rfps`
- ❌ Pas d'accès admin à la base

**API Keys :**
- ✅ Rotation régulière des secrets
- ✅ Limitation de scope (OpenAI rate limits)

### Sécurité réseau

**HTTPS uniquement :**
- ✅ MongoDB via TLS (`mongodb+srv://`)
- ✅ Microsoft Graph API (HTTPS)
- ✅ Boond Manager API (HTTPS)
- ❌ **MongoDB API locale (http://localhost:8000)** → Passer en HTTPS

**Recommandation :**
```python
# Ajouter validation SSL
API_URL = os.getenv("API_URL", "https://api.futurwork.be")
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"

response = requests.post(
    f"{API_URL}/mongodb",
    json=data,
    verify=VERIFY_SSL
)
```

### Validation des données

**Sanitization :**
- ✅ Validation des dates (format ISO 8601)
- ✅ Validation des emails (regex)
- ❌ **Manque validation des inputs JSON** (risque injection)

**Recommandation - Ajouter validation Pydantic :**
```python
from pydantic import BaseModel, validator

class RFPDocument(BaseModel):
    job_id: str
    roleTitle: str
    job_desc: str
    # ...
    
    @validator('job_id')
    def validate_job_id(cls, v):
        if not v or len(v) > 100:
            raise ValueError('Invalid job_id')
        return v
```

---

## 🔧 Maintenance

### Tâches de maintenance régulières

#### Quotidien
- ✅ Vérifier les logs d'exécution
- ✅ Vérifier le fichier `.last_execution`
- ✅ Monitorer les erreurs API (taux d'échec)

#### Hebdomadaire
- ✅ Vérifier l'espace disque (attachments/)
- ✅ Analyser les métriques de performance
- ✅ Vérifier les RFPs expirées (nettoyage effectif)

#### Mensuel
- ✅ Rotation des logs
- ✅ Rotation des secrets (API keys)
- ✅ Mise à jour des dépendances Python
- ✅ Review de la consommation OpenAI (budget)

### Nettoyage automatique

**Attachments temporaires :**
Les fichiers JSON sont supprimés après traitement dans `main.py` :
```python
os.remove(file_path)
print(f"[DELETE] File '{filename}' deleted")
```

**RFPs expirées :**
Nettoyage automatique dans chaque run :
```python
def cleanup_expired_rfps(api_url: str):
    """Delete RFPs with deadlineAt < today()"""
```

**RFPs Boond fermées :**
Nettoyage automatique dans chaque run :
```python
def cleanup_closed_boond_rfps(boond_data: dict, api_url: str):
    """Delete RFPs if Boond state != 0 (open)"""
```

### Backup et récupération

**Backup MongoDB :**
```bash
# Via mongodump (si accès direct)
mongodump --uri="mongodb+srv://..." --out=/backup/$(date +%Y%m%d)

# Via API (export JSON)
curl http://localhost:8000/mongodb > backup_rfps_$(date +%Y%m%d).json
```

**Récupération :**
```python
# Importer depuis backup JSON
import json
import requests

with open('backup_rfps.json', 'r') as f:
    rfps = json.load(f)
    
for rfp in rfps:
    requests.post('http://localhost:8000/mongodb', json=rfp)
```

### Mise à jour des dépendances

```powershell
# Vérifier les mises à jour disponibles
pip list --outdated

# Mettre à jour requirements.txt
pip freeze > requirements.txt

# Tester après mise à jour
python src\main.py
```

### Performance

**Optimisations possibles :**

1. **Parallélisation des requêtes API**
```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fetch_opportunity_details, id) for id in filtered_ids]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
```

2. **Cache pour réduire appels ChatGPT**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def extract_skills_cached(text_hash):
    return job_enhancer.extract_skills_and_languages(text)
```

3. **Batch processing pour MongoDB**
```python
# Grouper les POST/PUT en bulk operations
bulk_operations = [
    {"insertOne": {"document": rfp1}},
    {"updateOne": {"filter": {...}, "update": {...}}}
]
```

---

## 📝 Annexes

### Glossaire

- **ETL** : Extract, Transform, Load
- **RFP** : Request For Proposal (offre de mission)
- **JWT** : JSON Web Token
- **OAuth2** : Protocole d'authentification
- **MSAL** : Microsoft Authentication Library
- **NLP** : Natural Language Processing
- **CRUD** : Create, Read, Update, Delete

### Références

- [Microsoft Graph API Documentation](https://learn.microsoft.com/en-us/graph/)
- [Boond Manager API Documentation](https://ui.boondmanager.com/api/doc)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [MongoDB Documentation](https://www.mongodb.com/docs/)
- [Python MSAL Documentation](https://msal-python.readthedocs.io/)

### Changelog

**Version 1.0 - 2026-01-14**
- ✅ Documentation technique complète initiale
- ✅ Architecture et flux documentés
- ✅ Review de sécurité effectuée
- ✅ Recommandations d'amélioration ajoutées

---

## ✅ Checklist de déploiement

- [ ] Installer Python 3.9+
- [ ] Cloner le repository
- [ ] Installer les dépendances (`pip install -r requirements.txt`)
- [ ] Configurer `params.py` (ou variables d'environnement)
- [ ] Créer le répertoire `app/attachments/`
- [ ] Tester l'authentification Azure AD
- [ ] Tester l'authentification Boond Manager
- [ ] Vérifier la connexion à l'API MongoDB
- [ ] Exécuter un run de test (`python src\main.py`)
- [ ] Configurer le planificateur de tâches (si production)
- [ ] Configurer les alertes de monitoring
- [ ] Documenter les credentials (coffre-fort sécurisé)
- [ ] Mettre en place les backups MongoDB

---

**Document maintenu par : Guillaume Chinzi**  
**Dernière mise à jour : 2026-01-14**  
**Version : 1.0**

# Olist API

API REST développée avec FastAPI et MongoDB pour exposer les données du dataset Brazilian E-Commerce Public Dataset by Olist.

Le projet a pour objectif de transformer les données CSV d'origine en données documentaires exploitables par une API REST, tout en proposant une modélisation adaptée à MongoDB, des agrégations métier et une première optimisation des performances par indexation.

## 1. Présentation du projet

Le dataset Olist contient environ 100 000 commandes réalisées entre 2016 et 2018 sur une plateforme e-commerce brésilienne.

Les données disponibles concernent notamment :

- les clients ;

- les commandes ;

- les produits ;

- les vendeurs ;

- les paiements ;

- les avis clients ;

- les informations géographiques.

Les données originales sont réparties dans plusieurs fichiers `CSV` et suivent une organisation relationnelle.

L'objectif du projet est de :

1. analyser et nettoyer les données ;

2. transformer les données pour les adapter à une approche documentaire ;

3. stocker les données dans MongoDB ;

4. exposer les données via une API REST FastAPI ;

5. proposer des résultats agrégés utiles ;

6. optimiser certaines requêtes avec des index MongoDB ;

7. fournir une API documentée et reproductible.

## 2. Architecture

L'architecture générale du projet est la suivante :
```
                    Dataset Olist
                         │
                         ▼
                  Fichiers CSV
                         │
                         ▼
                  ┌─────────────┐
                  │     ETL     │
                  │             │
                  │ Clean       │
                  │ Transform   │
                  │ Load        │
                  └──────┬──────┘
                         │
                         ▼
                    ┌─────────┐
                    │ MongoDB │
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
                    │ FastAPI │
                    └────┬────┘
                         │
                         ▼
                  Réponse JSON
                         │
                         ▼
                Applications / Data
```
## Organisation du projet
```
olist_api/
│
├── src/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   │
│   │   ├── models/
│   │   │   ├── customer.py
│   │   │   ├── order.py
│   │   │   ├── product.py
│   │   │   └── seller.py
│   │   │
│   │   ├── routers/
│   │   │   ├── customers.py
│   │   │   ├── orders.py
│   │   │   ├── products.py
│   │   │   ├── sellers.py
│   │   │   └── statistics.py
│   │   │
│   │   └── queries/
│   │       └── statistics.py
│   │
│   └── etl/
│       ├── main.py
│       ├── clean_csv.py
│       ├── transform.py
│       └── load_mongo.py
│
├── tests/
│   ├── test_api.py
│   └── test_mongodb.py
│
├── requirements.txt
├── .env.example
├── pyproject.toml
└── README.md
```
## 3. Modélisation MongoDB

Le modèle MongoDB ne reproduit pas directement la structure relationnelle du dataset original.

Le choix a été de regrouper dans un même document les informations principalement consultées ensemble.

La collection orders constitue notamment un document riche contenant :
```json
{
  "order_id": "...",
  "customer_id": "...",
  "status": "delivered",
  "purchase_timestamp": "2017-11-18 19:28:06",
  "items": [
    {
      "product_id": "...",
      "seller_id": "...",
      "price": 45.0,
      "freight_value": 27.2
    }
  ],
  "payments": [
    {
      "type": "credit_card",
      "installments": 1,
      "value": 72.2
    }
  ],
  "reviews": [
    {
      "review_id": "...",
      "score": 5,
      "comment_title": null,
      "comment_message": "...",
      "creation_date": "...",
      "answer_timestamp": "..."
    }
  ],
  "delivery": {
    "estimated_delivery": "...",
    "delivered_at": "..."
  }
}
```
## Pourquoi embarquer ces données ?

Les éléments `items`, `payments`, `reviews` et `delivery` sont liés à une commande et sont susceptibles d'être consultés avec celle-ci.

Les embarquer permet notamment d'éviter de multiplier les requêtes et les jointures pour obtenir les informations nécessaires à une commande.

Le modèle privilégie donc les usages de consultation retenus pour l'API plutôt que la reproduction stricte du modèle relationnel d'origine.

## 4. ETL

Le projet contient un processus ETL permettant de préparer et charger les données.

## Étapes
```
CSV
 │
 ▼
Clean
 │
 ▼
Transform
 │
 ▼
MongoDB
```
## Nettoyage

Le fichiers `clean_csv.py` est utilisé pour préparer les données et traiter certaines valeurs problématiques ou manquantes.

## Transformation

Le fichier `transform.py` transforme les données afin de construire les documents MongoDB.

Cette étape permet notamment de regrouper les informations liées à une commande dans un document contenant des tableaux et sous-documents.

## Chargement

Le fichier `load_mongo.py` permet d'insérer les documents transformés dans MongoDB.

Le processus est piloté par :
```
src/etl/main.py
```

L'objectif est de rendre l'import reproductible plutôt que de dépendre d'une insertion manuelle des données.

## 5. Installation
## Prérequis

- Python 3.14 ou version compatible avec le projet

- MongoDB

- pip

- Git

## Cloner le projet
```Shell
git clone https://github.com/merazig/olist-api.git
cd olist-api
```
## Créer l'environnement virtuel

Windows :
```shell
python -m venv env
.\env\Scripts\Activate.ps1
```
Installer les dépendances
```shell
pip install -r requirements.txt
```
## 6. Configuration

Créer un fichier `.env` à partir de `.env.example`.

Exemple :
```
MONGO_URI=mongodb://localhost:27017
MONGO_DB=olist
```

Les valeurs présentes dans `.env` ne doivent pas être versionnées si elles contiennent des informations sensibles.

Le fichier `.env.example` permet à un autre développeur de connaître les variables nécessaires à l'exécution du projet.

## 7. Import des données

Après avoir configuré MongoDB et placé les fichiers du dataset dans le répertoire prévu par l'ETL, lancer le processus d'import :
```shell
python -m src.etl.main
```

L'ETL effectue les différentes étapes de préparation, transformation et chargement des données dans MongoDB.

La base utilisée par l'application est :
```
olist
```
## 8. Lancer l'API

Depuis la racine du projet :
```shell
uvicorn src.app.main:app --reload
```

L'API est alors accessible à :
```text
http://127.0.0.1:8000
```
## 9. Documentation Swagger

FastAPI génère automatiquement une documentation interactive.

Une fois l'API lancée, accéder à :
```
http://127.0.0.1:8000/docs
```

Cette interface permet de :

- consulter les endpoints ;

- voir les paramètres attendus ;

- exécuter les requêtes ;

- visualiser les réponses JSON ;

- consulter les erreurs HTTP possibles.

## 10. Endpoints principaux
## Customers
```
GET /customers
```
```powershell
Invoke-RestMethod "http://127.0.0.1:8000/customers?limit=3"
```
Retourne les clients disponibles.
```
GET /customers/{customer_id}
```
Exemple :

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/customers/34a4d38dfc89ce24d9e96604ac22d7f4"
```

Retourne un client à partir de son identifiant.

Si le client n'existe pas :
```
404 Not Found
```

avec une réponse du type :
```json
{
  "detail": "Customer not found"
}
```
## Orders
```
GET /orders
```
```powershell
Invoke-RestMethod "http://127.0.0.1:8000/orders?limit=3"
```
Ou avec pagination:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/orders?limit=10&skip=20"
```

Retourne les commandes disponibles.
```
GET /orders/{order_id}
```
```powershell
Invoke-RestMethod "http://127.0.0.1:8000/orders/e481f51cbdc54678b7cc49136f2d6af7"
```
Retourne une commande à partir de son identifiant.

Cette commande est particulièrement intéressante car elle permet de vérifier que MongoDB contient bien les données embarquées :

```text
order
 ├── customer_id
 ├── dates
 ├── items[]
 ├── payments[]
 └── reviews[]
```

# Products
```
GET /products
```
```powershell
Invoke-RestMethod "http://127.0.0.1:8000/products?limit=3"
```

Avec pagination :

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/products?limit=10&skip=20"
```
Retourne les produits disponibles.
```
GET /products/{product_id}
```
```powershell
Invoke-RestMethod "http://127.0.0.1:8000/products/1e9e8ef04dbcff4541ed26657ea517e5"
```
Retourne un produit à partir de son identifiant.

## Sellers
```
GET /sellers
```
```powershell
Invoke-RestMethod "http://127.0.0.1:8000/sellers?limit=3"
```

avec pagination :

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/sellers?limit=10&skip=20"
```

Retourne les vendeurs disponibles.
```
GET /sellers/{seller_id}
```

Retourne un vendeur à partir de son identifiant.

## 11. Agrégations MongoDB

Deux agrégations métier ont été mises en place.

## Commandes par statut

Endpoint :
```
GET /statistics/orders-by-status
```

Cette agrégation regroupe les commandes selon leur statut et compte le nombre de commandes dans chaque groupe.

Pipeline principal :
```python
[
  {
    $group: {
      _id: "$status",
      count: { $sum: 1 }
    }
  },
  {
    $sort: {
      count: -1
    }
  }
]
```

Elle permet notamment d'obtenir une répartition des commandes entre les différents statuts.

## Chiffre d'affaires par mois

Endpoint :
```
GET /statistics/revenue-by-month
```

Cette agrégation :

- décompose le tableau payments avec $unwind ;

- convertit purchase_timestamp en date ;

- regroupe les paiements par mois ;

- additionne les valeurs des paiements ;

- trie les résultats chronologiquement.

Elle permet d'obtenir une vision mensuelle du chiffre d'affaires exploitable pour du reporting.

## 12. Index et performances

MongoDB crée automatiquement un index sur `_id`.

Cet index correspond à l'identifiant technique de chaque document.

Pour les recherches de commandes par client, un index supplémentaire a été créé :
```python
db.orders.create_index("customer_id")
```
## Avant l'index

Une recherche sur :
```mongosh
db.orders.find({
  customer_id: "06b8999e2fba1a1fbc88172c00ba8bc7"
})
```

utilisait un :
```
COLLSCAN
```

MongoDB devait examiner les **99 441 documents** de la collection.

Résultat observé avec `explain()` :
```
executionTimeMillis: 153
totalKeysExamined: 0
totalDocsExamined: 99441
```
## Après l'index

Après création de :
```
customer_id_1
```

MongoDB utilise :
```
IXSCAN
```

puis récupère le document correspondant.

Résultat observé :
```
executionTimeMillis: 11
totalKeysExamined: 1
totalDocsExamined: 1
```

L'index permet donc de passer d'une recherche parcourant toute la collection à une recherche utilisant directement l'index.

L'analyse avec `explain()` permet de démontrer concrètement l'intérêt de cet index sur cette requête.

## 13. Tests

Des tests automatisés sont présents dans le dossier `tests/`.
```
tests/
├── test_api.py
└── test_mongodb.py
```

Les tests couvrent notamment :

- la connexion à MongoDB ;

- l'existence de la collection orders ;

- la présence de l'index customer_id ;

- la récupération d'un client existant ;

- la gestion d'un client inexistant ;

- l'agrégation des commandes par statut ;

- l'agrégation du chiffre d'affaires mensuel.

Lancer les tests :
```
pytest
```

Résultat actuel :
```
7 passed
```
## 14. Validation et gestion des erreurs

FastAPI assure la validation des paramètres déclarés dans les routes.

Les ressources inexistantes sont gérées avec des réponses HTTP `404`.

Les erreurs de validation des paramètres sont automatiquement retournées par FastAPI avec une réponse HTTP adaptée, notamment `422 Unprocessable` Entity.

Cette séparation permet de distinguer :

- les erreurs de validation des paramètres ;

- les ressources absentes ;

- les erreurs liées au traitement de la requête.

## 15. Pourquoi une API entre l'application et MongoDB ?

L'application cliente n'accède pas directement à MongoDB.

Le parcours d'une requête est :
```
Client
  │
  │ HTTP GET
  ▼
FastAPI
  │
  │ Requête MongoDB
  ▼
MongoDB
  │
  │ Résultat
  ▼
FastAPI
  │
  │ JSON
  ▼
Client
```

Cette architecture permet notamment de :

- contrôler les données accessibles ;

- valider les paramètres ;

- gérer les erreurs ;

- contrôler le volume des réponses ;

- masquer les détails internes de MongoDB ;

- fournir une interface stable aux applications clientes.

## 16. Technologies utilisées

- **Python** — langage principal

- **FastAPI** — création de l'API REST

- **MongoDB** — stockage documentaire

- **PyMongo** — communication entre Python et MongoDB

- **Pydantic** — validation et modèles de données

- **Pandas** — préparation des données

- **Pytest** — tests automatisés

- **Ruff** — analyse et qualité du code

## 17. Objectifs du projet

Ce projet met en pratique :

- la conception d'une base MongoDB ;

- la modélisation documentaire ;

- la préparation de données avec un ETL ;

- la création d'une API REST avec FastAPI ;

- la validation des données ;

- les agrégations MongoDB ;

- l'indexation ;

- l'analyse de performances avec explain() ;

- les tests automatisés ;

- la documentation d'une API.

## 18. Source des données

Dataset utilisé :

**Brazilian E-Commerce Public Dataset by Olist**

Le dataset est disponible publiquement sur Kaggle.

Les données utilisées dans ce projet sont fournies à des fins d'analyse et de démonstration.
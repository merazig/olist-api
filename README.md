# Olist MongoDB & FastAPI

Projet Data Engineering réalisé à partir du dataset e-commerce réel **Brazilian E-Commerce by Olist**.

L'objectif est de partir des fichiers CSV du dataset, d'en analyser les relations, de construire un modèle documentaire MongoDB adapté aux usages de l'API, puis d'exposer les données avec **FastAPI**.

> J'ai conçu l'architecture et le modèle documentaire à partir de la structure du dataset et des besoins d'accès de l'API, en justifiant les choix d'embedding, de références, de dénormalisation et d'indexation.

## Stack

**Python · Pandas · MongoDB · PyMongo · FastAPI · Pydantic · Uvicorn · Docker · Git/GitHub**

## Architecture

```text
CSV Olist
    │
    ▼
data/raw/
    │
    ▼
Nettoyage / validation
    │
    ▼
data/processed/
    │
    ▼
MongoDB
    │
    ▼
FastAPI
    │
    ▼
Swagger / OpenAPI
```

## Analyse du modèle relationnel

Le dataset d'origine est constitué de plusieurs fichiers reliés entre eux :

```text
CUSTOMER
    │
    │ customer_id
    ▼
  ORDER
    │
    ├── order_id ───────► PAYMENT
    │
    ├── order_id ───────► REVIEW
    │
    └── order_id ───────► ORDER_ITEM
                              │
                              ├── product_id ──► PRODUCT
                              │
                              └── seller_id ───► SELLER

CUSTOMER / SELLER
    │
    └── zip_code_prefix ──► GEOLOCATION

PRODUCT
    │
    └── product_category_name
              │
              ▼
    CATEGORY_TRANSLATION
```

L'analyse des cardinalités montre que les données directement liées à une commande restent relativement limitées : une commande possède généralement peu d'articles, de paiements et d'avis.

## Modèle MongoDB retenu

J'ai retenu cinq collections principales :

```text
customers
products
sellers
orders
geolocations
```

Les données suivantes sont embarquées dans `orders` :

```text
orders
├── dates
├── items[]
├── payments[]
└── reviews[]
```

Les produits, vendeurs et clients restent dans des collections séparées.

### Pourquoi ce choix ?

**Embedding**

`items`, `payments` et `reviews` sont embarqués dans `orders` car ils sont directement liés à une commande et sont généralement consultés avec celle-ci.

Cela permet notamment de récupérer une commande complète sans devoir reconstruire l'ensemble de ses informations à partir de plusieurs collections.

**Références**

Les `products` et `sellers` restent séparés car ils sont réutilisés par de nombreuses commandes. Les dupliquer dans chaque document `orders` augmenterait inutilement la taille des documents et créerait de la redondance.

Les `customers` restent également séparés afin de pouvoir les consulter indépendamment des commandes.

**Géolocalisation**

`geolocations` est conservée dans une collection séparée. Un même `zip_code_prefix` peut correspondre à plusieurs coordonnées géographiques ; il ne constitue donc pas une clé unique à lui seul.

## Particularité `customer_id`

Dans le dataset Olist, `customer_id` identifie l'enregistrement client associé à une commande.

`customer_unique_id` permet de rapprocher plusieurs `customer_id` appartenant au même client au sens métier global.

Cette distinction est importante pour ne pas confondre l'identifiant technique utilisé dans les relations du dataset avec l'identité client globale.

## Exemple de document `orders`

```json
{
  "order_id": "abc123",
  "customer_id": "customer456",
  "status": "delivered",
  "dates": {
    "purchase": "...",
    "approved": "...",
    "delivered_carrier": "...",
    "delivered_customer": "...",
    "estimated_delivery": "..."
  },
  "items": [
    {
      "order_item_id": 1,
      "product_id": "prod001",
      "seller_id": "seller001",
      "price": 58.90,
      "freight_value": 13.29
    }
  ],
  "payments": [
    {
      "sequential": 1,
      "type": "credit_card",
      "installments": 8,
      "value": 99.33
    }
  ],
  "reviews": [
    {
      "review_id": "review001",
      "score": 5,
      "comment_message": "..."
    }
  ]
}
```

## Index MongoDB

Les index sont principalement placés sur les identifiants et les champs utilisés par les recherches de l'API :

```text
customers.customer_id
customers.customer_unique_id

products.product_id

sellers.seller_id

orders.order_id
orders.customer_id
orders.status
orders.items.product_id
orders.items.seller_id

geolocations:
(zip_code_prefix, location.lat, location.lng)
```

Les identifiants principaux sont indexés en `unique` lorsque cela correspond aux contraintes du modèle.

## Nettoyage et ingestion

Le nettoyage est réalisé par :

```text
src/ingestion/cleaner.py
```

Il comprend notamment :

* normalisation des identifiants ;
* conversion des dates et données numériques ;
* normalisation des villes et États ;
* conservation des codes postaux sur 5 caractères ;
* gestion des valeurs manquantes ;
* suppression des doublons ;
* traduction des catégories produits.

L'ingestion est réalisée par :

```text
src/ingestion/loader.py
```

Le chargement MongoDB est effectué par lots et les index sont créés avant l'ingestion.

## API REST

Endpoints disponibles :

```text
GET /health

GET /customers
GET /customers/{customer_id}
GET /customers/{customer_id}/orders

GET /products
GET /products/{product_id}

GET /orders
GET /orders/{order_id}

GET /sellers

GET /reviews
```

La documentation interactive est disponible avec Swagger :

```text
http://127.0.0.1:8000/docs
```

OpenAPI :

```text
http://127.0.0.1:8000/openapi.json
```

## Organisation

```text
data/
├── raw/
└── processed/

src/
├── ingestion/       # nettoyage et ingestion
├── database/        # connexion, index et vérification
├── models/          # modèles métier
├── repositories/    # accès aux données
├── services/        # logique métier
└── api/             # routes FastAPI

tests/
logs/
```

La séparation `repository → service → API` permet de distinguer l'accès aux données, la logique métier et l'exposition HTTP.

## Installation

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configurer `.env` :

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=olist
```

## Nettoyage et ingestion

```powershell
python src/ingestion/cleaner.py
python src/ingestion/loader.py
```

## Lancement de l'API

```powershell
python -m uvicorn src.main:app --reload
```

API :

```text
http://127.0.0.1:8000
```

Swagger :

```text
http://127.0.0.1:8000/docs
```

## Données chargées

Après ingestion :

```text
customers       99 441
products        32 951
sellers          3 095
orders          99 441
geolocations   720 154
```

Les données embarquées sont présentes dans les commandes :

```text
items       98 666 commandes
payments    99 440 commandes
reviews     98 673 commandes
```

## Vérification

Les contrôles portent notamment sur :

* les volumes chargés ;
* les identifiants ;
* les relations entre les données ;
* les références produits / vendeurs / clients ;
* les données géographiques ;
* les catégories ;
* le fonctionnement des endpoints FastAPI.

Les principaux endpoints ont été testés avec succès, notamment `/health`, `/customers`, `/products`, `/orders`, `/sellers` et `/reviews`.

## Statut

**MongoDB : validé**
**Modélisation : validée**
**Ingestion : validée**
**Indexation : validée**
**API REST : validée**
**Swagger / OpenAPI : disponible**


### Architecture actuelle 

Windows
│
├── Python / FastAPI
│      │
│      │ PyMongo
│      ▼
│   MongoDB
│   [Docker]
│
└── Docker

### Architecture entièrement conteneurisée

Docker Compose
│
├── fastapi
│     └── API REST
│
└── mongodb
      └── Base Olist

### Architecture finale

                  Docker Compose
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
   ┌──────────────┐          ┌──────────────┐
   │   FastAPI    │          │   MongoDB    │
   │              │ PyMongo  │              │
   │   :8000      ├─────────►│   :27017     │
   └──────────────┘          └──────┬───────┘
                                    │
                              volume MongoDB
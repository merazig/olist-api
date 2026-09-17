Projet Data Engineering — Olist
MongoDB & FastAPI
Objectif : concevoir, stocker et exposer les données e-commerce du dataset Olist avec MongoDB et FastAPI.

1. Vue d'ensemble du projet
Dataset Olist (CSV)
        │
        ▼
  Python / Pandas
        │
        │ Nettoyage + transformation
        ▼
     MongoDB
        │
        │ Requêtes
        ▼
     FastAPI
        │
        ▼
     REST API
        │
        ▼
 Swagger / Postman

Technologies
Python

Pandas

MongoDB

PyMongo

FastAPI

Pydantic

Uvicorn

MongoDB Compass

Swagger UI

Git / GitHub

Pytest (optionnel)

2. Dataset Olist
Fichiers principaux
Fichier	Contenu
olist_customers_dataset.csv	Clients
olist_orders_dataset.csv	Commandes
olist_order_items_dataset.csv	Articles des commandes
olist_order_payments_dataset.csv	Paiements
olist_order_reviews_dataset.csv	Avis
olist_products_dataset.csv	Produits
olist_sellers_dataset.csv	Vendeurs
olist_geolocation_dataset.csv	Géolocalisation
product_category_name_translation.csv	Traduction des catégories

Relations principales
CUSTOMER
   │
   │ customer_id
   ▼
ORDER
   │
   ├──────────────► PAYMENT
   │
   ├──────────────► REVIEW
   │
   └──────────────► ORDER_ITEM
                         │
                         ├────────► PRODUCT
                         │
                         └────────► SELLER

3. Architecture du projet
olist-project/
│
├── data/
│   ├── raw/
│   │   ├── olist_customers_dataset.csv
│   │   ├── olist_orders_dataset.csv
│   │   ├── olist_order_items_dataset.csv
│   │   ├── olist_order_payments_dataset.csv
│   │   ├── olist_order_reviews_dataset.csv
│   │   ├── olist_products_dataset.csv
│   │   ├── olist_sellers_dataset.csv
│   │   ├── olist_geolocation_dataset.csv
│   │   └── product_category_name_translation.csv
│   │
│   └── processed/
│
├── etl/
│   ├── __init__.py
│   ├── load_csv.py
│   ├── transform.py
│   └── load_mongodb.py
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   │
│   ├── models/
│   │   ├── customer.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── seller.py
│   │
│   └── routers/
│       ├── customers.py
│       ├── products.py
│       ├── orders.py
│       ├── sellers.py
│       └── statistics.py
│
├── tests/
│   └── test_api.py
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── PLAN.md

4. Modélisation MongoDB
Collections prévues
customers
sellers
products
orders

Éventuellement :

reviews

si les avis ne sont pas intégrés aux commandes.

Modèle orders
On utilise une modélisation hybride.

Les données fortement liées à une commande sont embarquées :

orders
 ├── items[]
 ├── payments[]
 └── delivery

Les entités réutilisées sont conservées dans des collections séparées :

customers
products
sellers

Exemple de document orders
{
  "_id": "ORDER_ID",
  "customer_id": "CUSTOMER_ID",
  "status": "delivered",

  "purchase_timestamp": "2017-10-02T10:56:33",

  "items": [
    {
      "product_id": "PRODUCT_ID",
      "seller_id": "SELLER_ID",
      "price": 29.99,
      "freight_value": 8.72
    }
  ],

  "payments": [
    {
      "type": "credit_card",
      "installments": 2,
      "value": 38.71
    }
  ],

  "delivery": {
    "estimated_delivery": "2017-10-18T00:00:00",
    "delivered_at": "2017-10-10T21:25:13"
  }
}

5. Justification de la modélisation
Pourquoi embarquer items ?
Une commande est généralement consultée avec ses articles.

order
 └── items[]

Cela évite de devoir effectuer une requête séparée pour récupérer les articles.

Pourquoi embarquer payments ?
Les paiements sont directement associés à une commande et sont généralement consultés dans son contexte.

Pourquoi garder products séparé ?
Un produit peut être associé à plusieurs commandes.

Le dupliquer dans chaque commande pourrait entraîner beaucoup de duplication.

Pourquoi garder customers séparé ?
Un client possède plusieurs commandes.

On évite donc de dupliquer toutes ses informations dans chaque commande.

Pourquoi garder sellers séparé ?
Un vendeur peut vendre de nombreux produits et apparaître dans de nombreuses commandes.

6. ETL
Étape 1 — Charger les CSV
Objectif :

CSV
 ↓
Pandas DataFrame

À vérifier :

types des colonnes ;

valeurs nulles ;

doublons ;

clés primaires ;

relations entre fichiers.

Étape 2 — Nettoyage
Vérifier notamment :

valeurs manquantes ;

dates ;

nombres ;

identifiants ;

catégories ;

doublons.

Transformer les dates :

string
 ↓
datetime

Transformer les valeurs numériques :

string
 ↓
float / int

Étape 3 — Transformation
Construire les documents MongoDB.

Exemple :

orders.csv
      +
order_items.csv
      +
payments.csv
      +
reviews.csv
      ↓
document orders

Étape 4 — Insertion MongoDB
Créer les collections puis insérer les documents.

Vérifier :

Nombre de customers
Nombre de products
Nombre de sellers
Nombre de orders

Comparer avec les données sources.

7. Index MongoDB
Créer des index sur les champs fréquemment recherchés.

Exemples :

db.orders.create_index("customer_id")
db.orders.create_index("status")
db.orders.create_index("purchase_timestamp")

db.products.create_index("category")

db.sellers.create_index("seller_id")

À expliquer pendant la soutenance
Les index ont été choisis en fonction des champs utilisés par les endpoints et les requêtes fréquentes afin d'améliorer les performances de recherche.

8. API FastAPI
Endpoint Customers
GET /customers
GET /customers/{customer_id}
GET /customers/{customer_id}/orders

Endpoint Products
GET /products
GET /products/{product_id}
GET /products?category=health_beauty

Endpoint Orders
GET /orders
GET /orders/{order_id}
GET /orders?status=delivered

Endpoint Sellers
GET /sellers
GET /sellers/{seller_id}

Endpoint Statistics
GET /statistics/orders
GET /statistics/products
GET /statistics/revenue
GET /statistics/categories

9. Pagination
Pour éviter de retourner toute la base :

GET /products?skip=0&limit=20

Exemple :

@app.get("/products")
def get_products(
    skip: int = 0,
    limit: int = 20
):
    return list(
        db.products
        .find({})
        .skip(skip)
        .limit(limit)
    )

Prévoir une limite maximale :

limit <= 100

10. Filtres
Commandes
GET /orders?status=delivered

Produits
GET /products?category=health_beauty

Client
GET /customers/{customer_id}/orders

11. Gestion des erreurs
Prévoir notamment :

Ressource inexistante
GET /products/unknown-id

Réponse :

{
  "detail": "Product not found"
}

avec un statut HTTP :

404 Not Found

Paramètre invalide
Retourner :

400 Bad Request

ou laisser FastAPI gérer la validation lorsque Pydantic suffit.

12. Pydantic
Créer des modèles pour structurer les réponses.

Exemple :

class Product(BaseModel):
    id: str
    category: str | None = None
    weight_g: float | None = None

Objectifs :

réponses structurées ;

validation ;

documentation Swagger ;

meilleure lisibilité du code.

13. Aggregations MongoDB
Utiliser les aggregation pipelines pour les statistiques.

Commandes par statut
pipeline = [
    {
        "$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }
    },
    {
        "$sort": {
            "count": -1
        }
    }
]

Endpoint :

GET /statistics/orders

Chiffre d'affaires
Calculer à partir des articles :

prix + frais de livraison

Puis faire une somme.

Endpoint :

GET /statistics/revenue

Top catégories
Faire une aggregation permettant d'obtenir :

catégorie
nombre de produits / commandes

Endpoint :

GET /statistics/categories

14. Tests
Tester au minimum :

GET /customers
GET /customers/{id}
GET /products
GET /products/{id}
GET /orders
GET /orders/{id}
GET /customers/{id}/orders
GET /statistics/orders

Tester également :

ID inexistant
paramètre invalide
pagination
filtres

15. Planning
MARDI — DATA + MONGODB
Objectif
Avoir une base MongoDB fonctionnelle et correctement alimentée.

Matin / début de session
 Récupérer les CSV

 Inspecter les fichiers

 Comprendre les colonnes

 Identifier les clés

 Identifier les relations

 Vérifier les valeurs manquantes

 Vérifier les doublons

Modélisation
 Définir les collections

 Décider ce qui est embarqué

 Décider ce qui est référencé

 Dessiner le schéma MongoDB

 Écrire la justification des choix

ETL
 Écrire le chargement CSV

 Nettoyer les données

 Convertir les dates

 Convertir les nombres

 Construire les documents orders

MongoDB
 Créer la base

 Créer les collections

 Insérer les données

 Vérifier les documents

 Compter les documents

 Créer les index

 Tester quelques requêtes

FIN DU MARDI
[ ] CSV propres
[ ] ETL fonctionnel
[ ] MongoDB rempli
[ ] Modèle documenté
[ ] Index créés

MERCREDI — FASTAPI
Objectif
Avoir une API REST fonctionnelle connectée à MongoDB.

Configuration
 Créer l'environnement Python

 Installer les dépendances

 Configurer .env

 Créer database.py

 Tester la connexion MongoDB

API
 Créer main.py

 Créer les routers

 Créer /customers

 Créer /products

 Créer /orders

 Créer /sellers

 Créer /statistics

Fonctionnalités
 Ajouter les paramètres de recherche

 Ajouter les filtres

 Ajouter la pagination

 Ajouter les erreurs 404

 Ajouter les modèles Pydantic

 Nettoyer les réponses JSON

Statistiques
 Commandes par statut

 Chiffre d'affaires

 Catégories

 Une autre statistique pertinente

Documentation
 Vérifier /docs

 Vérifier les descriptions

 Vérifier les réponses

 Tester tous les endpoints dans Swagger

FIN DU MERCREDI
[ ] API fonctionnelle
[ ] MongoDB connecté
[ ] Endpoints principaux terminés
[ ] Pagination terminée
[ ] Filtres terminés
[ ] Statistiques terminées
[ ] Swagger fonctionnel

VENDREDI MATIN — TESTS + SOUTENANCE
Objectif
Stabiliser le projet et préparer une démonstration fluide.

Tests
 Tester tous les endpoints

 Tester les erreurs

 Tester les filtres

 Tester la pagination

 Tester les aggregations

 Vérifier les performances basiques

 Corriger les bugs

Code
 Nettoyer le code

 Supprimer les fichiers inutiles

 Vérifier les imports

 Vérifier .gitignore

 Vérifier .env

 Vérifier requirements.txt

 Vérifier le README

Démonstration
 Démarrer MongoDB

 Démarrer FastAPI

 Ouvrir Swagger

 Vérifier que tout fonctionne

 Préparer les requêtes de démonstration

 Répéter la présentation

16. Démonstration prévue
Étape 1 — Montrer MongoDB
Montrer :

customers
products
sellers
orders

Puis ouvrir un document order.

Expliquer :

order
 ├── customer_id
 ├── status
 ├── items[]
 ├── payments[]
 └── delivery

Étape 2 — Montrer Swagger
Ouvrir :

/docs

Étape 3 — Récupérer un produit
GET /products

Puis :

GET /products/{id}

Étape 4 — Récupérer une commande
GET /orders/{id}

Montrer que le document contient directement :

les informations de commande ;

les articles ;

les paiements ;

la livraison.

Étape 5 — Rechercher les commandes d'un client
GET /customers/{id}/orders

Étape 6 — Montrer un filtre
GET /orders?status=delivered

Étape 7 — Montrer une statistique
GET /statistics/orders

Puis éventuellement :

GET /statistics/revenue

17. Plan de soutenance
1. Présentation du projet
À dire
Nous avons travaillé sur le dataset e-commerce Olist, composé de plusieurs fichiers CSV représentant différentes entités d'une plateforme e-commerce.

2. Problématique
Notre objectif était de transformer ces données en une base MongoDB cohérente puis de les rendre accessibles via une API REST développée avec FastAPI.

3. Architecture
Montrer :

CSV
 ↓
Python / Pandas
 ↓
MongoDB
 ↓
FastAPI
 ↓
REST API
 ↓
Swagger

Expliquer brièvement chaque couche.

4. Modélisation MongoDB
Montrer le document orders.

Expliquer :

pourquoi items est embarqué ;

pourquoi payments est embarqué ;

pourquoi products est séparé ;

pourquoi customers est séparé ;

pourquoi sellers est séparé ;

pourquoi certains index ont été créés.

5. API
Présenter les endpoints principaux :

GET /customers
GET /customers/{id}

GET /products
GET /products/{id}

GET /orders
GET /orders/{id}

GET /customers/{id}/orders

GET /statistics/...

6. Démonstration
Faire quelques requêtes dans Swagger.

Ordre conseillé :

1. Products
2. Product detail
3. Order detail
4. Customer orders
5. Filter
6. Statistics

7. Conclusion
Revenir sur :

Dataset réel
      ↓
Nettoyage / ETL
      ↓
Modélisation NoSQL
      ↓
MongoDB
      ↓
API FastAPI
      ↓
REST / Swagger

18. Questions possibles du jury
Préparer les réponses à ces questions.

Pourquoi MongoDB plutôt qu'une base SQL ?
Réponse à préparer :

modèle document ;

données imbriquées ;

flexibilité du schéma ;

possibilité d'utiliser des aggregations ;

adaptation aux besoins de consultation.

Pourquoi avoir embarqué certaines données ?
Réponse :

Parce qu'elles sont fortement liées à une commande et sont généralement consultées dans son contexte.

Pourquoi ne pas tout embarquer ?
Réponse :

Certaines entités sont réutilisées par beaucoup de documents. Les dupliquer pourrait augmenter fortement la taille des données et compliquer leur mise à jour.

Pourquoi ces index ?
Réponse :

Nous avons choisi les index en fonction des champs utilisés dans les recherches et les endpoints fréquents.

Pourquoi FastAPI ?
Réponse :

framework Python moderne ;

rapide à mettre en place ;

validation avec Pydantic ;

documentation Swagger automatique ;

adapté à la création d'API REST.

Quelle différence entre MongoDB et FastAPI ?
MongoDB
= stockage + requêtes

FastAPI
= exposition des données via HTTP

Comment avez-vous géré les données manquantes ?
Préparer une réponse basée sur ce que vous avez réellement fait :

suppression
OU
valeur par défaut
OU
None / null
OU
conservation telle quelle

Ne pas prétendre avoir traité un cas si ce n'est pas le cas.

19. Checklist finale
Data
 Tous les CSV sont compris

 Les relations sont comprises

 Les données sont nettoyées

 Les dates sont correctement gérées

 Les valeurs numériques sont correctement typées

MongoDB
 Collections créées

 Documents cohérents

 Embedding justifié

 Références justifiées

 Index créés

 Aggregations fonctionnelles

FastAPI
 API démarre

 MongoDB connecté

 Endpoints fonctionnels

 Pagination

 Filtres

 Erreurs 404

 Pydantic

 Swagger

Projet
 requirements.txt

 .gitignore

 .env

 README

 Code propre

 Tests

Soutenance
 Architecture expliquée

 Modèle MongoDB expliqué

 Choix techniques justifiés

 Démo préparée

 Swagger prêt

 MongoDB prêt

 Répétition effectuée

20. Objectif final
À la fin du projet, nous devons pouvoir montrer :

             OLIST CSV
                 │
                 ▼
          ┌─────────────┐
          │     ETL     │
          │ Python/Pandas│
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │   MongoDB   │
          │             │
          │ customers   │
          │ products    │
          │ sellers     │
          │ orders      │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │   FastAPI   │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │ REST / JSON │
          └──────┬──────┘
                 │
                 ▼
             Swagger

Critère de réussite :

Un utilisateur doit pouvoir interroger les données Olist via une API REST sans avoir besoin de connaître la structure des fichiers CSV d'origine.
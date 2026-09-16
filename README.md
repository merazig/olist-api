
« J'ai conçu une architecture et un modèle documentaire MongoDB à partir des relations du dataset et des besoins d'accès de l'API REST, puis j'ai justifié mes choix de dénormalisation, d'embedding, de références et d'indexation. »

### Stack

Python + Pandas + MongoDB + PyMongo/Motor + FastAPI + Pydantic + Docker + Git/GitHub

                  ┌──────────────┐
                  │ CSV / Dataset│
                  └──────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ Python        │
                 │ Pandas        │
                 │ Validation    │
                 └──────┬────────┘
                        │
                        ▼
                ┌────────────────┐
                │    MongoDB     │
                │ Collections    │
                │ Index           │
                └───────┬────────┘
                        │
                        ▼
                ┌────────────────┐
                │    FastAPI     │
                │ REST API       │
                │ Pydantic       │
                └───────┬────────┘
                        │
                        ▼
                ┌────────────────┐
                │ Swagger /      │
                │ OpenAPI        │
                └────────────────┘

### Pourquoi cette modélisation ?

* **Embedding** pour les données fortement liées à la commande et généralement consultées avec celle-ci : `items`, `payments`, `delivery` et `reviews`.
* **Références** pour les entités réutilisées dans plusieurs commandes ou susceptibles d'être volumineuses : `customer_id`, `product_id` et `seller_id`.
* **Limiter la taille des documents MongoDB** afin d'éviter une duplication excessive des données et de respecter les contraintes de taille des documents.
* **Adapter le modèle aux besoins de l'API REST**, en privilégiant les structures permettant de répondre efficacement aux principales requêtes sans multiplier les jointures applicatives.
* **Créer des index** sur les champs fréquemment utilisés dans les recherches, les filtres et les relations, notamment `order_id`, `customer_id`, `product_id` et `seller_id`.


### Structure relationnelle identifiée

Le cœur du dataset est :

CUSTOMER
   │
   │ customer_id
   ▼
ORDER
   │
   ├─────────────── order_id ───────────────┐
   │                                        │
   ▼                                        ▼
ORDER_ITEM                              PAYMENT
   │
   ├── product_id ──► PRODUCT
   │
   └── seller_id ───► SELLER

ORDER
   │
   └── order_id ──► REVIEW

PRODUCT
   │
   └── product_category_name
                  │
                  ▼
       CATEGORY_TRANSLATION

CUSTOMER / SELLER
   │
   └── zip_code_prefix
              │
              ▼
          GEOLOCATION

Relation 

CUSTOMER
   │
   │ 1:N
   ▼
 ORDERS
   │
   ├────────── 1:N ──────────► ORDER_ITEMS
   │                              │
   │                              ├──► PRODUCTS
   │                              │
   │                              └──► SELLERS
   │
   ├────────── 1:N ──────────► PAYMENTS
   │
   └────────── 1:N ──────────► REVIEWS


### MongoDB ?

MongoDB est particulièrement intéressant ici parce que le modèle relationnel initial est composé de nombreuses tables liées, alors que l'accès API sera souvent orienté vers une commande complète.

Une commande peut naturellement être représentée comme un document :
### Json

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
      "product_id": "prod001",
      "seller_id": "seller001",
      "price": 58.90,
      "freight_value": 13.29
    }
  ],

  "payments": [
    {
      "type": "credit_card",
      "installments": 8,
      "value": 99.33
    }
  ],

  "reviews": [
    {
      "score": 5,
      "comment": "..."
    }
  ]
}
"""Requête des statistiques."""


def revenue_by_month(collection):
    """Calcule le chiffre d'affaires total pour chaque mois.

    Les paiements étant stockés dans le tableau `payments`, celui-ci
    est décomposé avec `$unwind`. Les commandes sont ensuite regroupées
    par mois à partir de `purchase_timestamp`, et les valeurs des
    paiements sont additionnées.

    Args:
        collection: Collection MongoDB `orders`.

    Returns:
        Une liste de dictionnaires contenant le mois et le chiffre
        d'affaires correspondant.
    """
    pipeline = [
        {"$unwind": "$payments"},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m",
                        "date": {"$dateFromString": {"dateString": "$purchase_timestamp"}},
                    }
                },
                "revenue": {"$sum": "$payments.value"},
            }
        },
        {"$project": {"_id": 0, "month": "$_id", "revenue": 1}},
        {"$sort": {"month": 1}},
    ]

    return list(collection.aggregate(pipeline))


def orders_by_status(collection):
    """Retourne le nombre de commandes pour chaque statut.

    Args:
        collection: Collection MongoDB `orders`.

    Returns:
        Une liste contenant le statut et le nombre de commandes.
    """
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "status": "$_id", "count": 1}},
        {"$sort": {"count": -1}},
    ]

    return list(collection.aggregate(pipeline))

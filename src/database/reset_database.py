import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017",
)

MONGO_DATABASE = os.getenv(
    "MONGO_DATABASE",
    "olist",
)


def main() -> None:
    """Supprime complètement la base MongoDB Olist."""
    client = MongoClient(MONGO_URI)

    try:
        client.admin.command("ping")

        print(
            f"Base MongoDB ciblée : {MONGO_DATABASE}"
        )

        confirmation = input(
            "ATTENTION : supprimer toute la base "
            f"'{MONGO_DATABASE}' ? (oui/non) : "
        )

        if confirmation.lower() != "oui":
            print("Suppression annulée.")
            return

        client.drop_database(MONGO_DATABASE)

        print(
            f"Base '{MONGO_DATABASE}' supprimée."
        )

    finally:
        client.close()
        print("Connexion MongoDB fermée.")


if __name__ == "__main__":
    main()

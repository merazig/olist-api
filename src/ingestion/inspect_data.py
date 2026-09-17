from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/raw")


def inspect_csv(file_path: Path) -> None:
    """Inspecte la structure d'un fichier CSV."""
    df = pd.read_csv(file_path)

    print("\n" + "=" * 80)
    print(f"FICHIER : {file_path.name}")
    print("=" * 80)

    print(f"Nombre de lignes : {len(df):,}")
    print(f"Nombre de colonnes : {len(df.columns)}")

    print("\nColonnes :")
    for column in df.columns:
        print(f"  - {column}")

    print("\nTypes :")
    print(df.dtypes)

    print("\nValeurs manquantes :")
    print(df.isna().sum())

    print("\nPremières lignes :")
    print(df.head(3).to_string(index=False))


def main() -> None:
    """Inspecte tous les fichiers CSV du dossier raw."""
    for file_path in sorted(DATA_DIR.glob("*.csv")):
        inspect_csv(file_path)


if __name__ == "__main__":
    main()
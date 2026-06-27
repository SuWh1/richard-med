from app.db.session import SessionLocal
from app.services.catalog_import import import_catalog


def main() -> None:
    session = SessionLocal()
    try:
        stats = import_catalog(session)
        session.commit()
    finally:
        session.close()

    print(
        f"services: +{stats.services_inserted} inserted, "
        f"{stats.services_updated} updated"
    )
    print(f"aliases seeded: {stats.aliases_seeded}")
    if stats.groups_unresolved:
        print(f"unresolved synonym groups: {', '.join(stats.groups_unresolved)}")


if __name__ == "__main__":
    main()

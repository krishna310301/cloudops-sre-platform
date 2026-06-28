from sqlalchemy import create_engine, inspect, text

from app.config import get_settings

INITIAL_REVISION = "20260612_0001"
INITIAL_TABLES = {
    "deployments",
    "health_checks",
    "incident_updates",
    "incidents",
    "services",
}


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    with engine.begin() as connection:
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())
        if "alembic_version" in table_names:
            return
        if not INITIAL_TABLES.issubset(table_names):
            return

        connection.execute(
            text(
                "CREATE TABLE alembic_version "
                "(version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
            )
        )
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": INITIAL_REVISION},
        )
        print(
            "Stamped existing initial schema with Alembic revision "
            f"{INITIAL_REVISION}."
        )


if __name__ == "__main__":
    main()

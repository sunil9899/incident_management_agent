import psycopg

from app.core.config import get_settings


settings = get_settings()

connection_url = (
    settings.database_url
    .render_as_string(hide_password=False)
    .replace("postgresql+asyncpg://", "postgresql://", 1)
)

with psycopg.connect(connection_url) as conn:
    with conn.cursor() as cursor:

        cursor.execute("""
            SELECT
                current_user,
                current_database(),
                current_schema(),
                current_setting('search_path'),
                has_schema_privilege(
                    current_user, 'public', 'USAGE'
                ),
                has_schema_privilege(
                    current_user, 'public', 'CREATE'
                );
        """)

        print("Connection details:", cursor.fetchone())

        cursor.execute("""
            CREATE TABLE public._langgraph_permission_test (
                id SERIAL PRIMARY KEY
            );
        """)

        print("CREATE TABLE: SUCCESS")

        cursor.execute("""
            DROP TABLE public._langgraph_permission_test;
        """)

        print("DROP TABLE: SUCCESS")
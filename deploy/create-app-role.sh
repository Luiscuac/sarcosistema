#!/bin/sh
set -eu

: "${APP_DB_USER:?APP_DB_USER is required}"
: "${APP_DB_PASSWORD:?APP_DB_PASSWORD is required}"

psql --set=ON_ERROR_STOP=1 \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=admin_role="$POSTGRES_USER" \
  --set=database_name="$POSTGRES_DB" \
  --set=app_db_user="$APP_DB_USER" \
  --set=app_db_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE :"app_db_user" LOGIN PASSWORD :'app_db_password';
GRANT CONNECT ON DATABASE :"database_name" TO :"app_db_user";
GRANT USAGE ON SCHEMA public TO :"app_db_user";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"app_db_user";
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO :"app_db_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"admin_role" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"app_db_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"admin_role" IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO :"app_db_user";
SQL

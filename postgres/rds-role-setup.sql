-- Required in tests to mirror RDS role required for PostGIS installation.
CREATE ROLE rds_superuser WITH
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  INHERIT
  NOLOGIN
  NOREPLICATION
  NOBYPASSRLS
  CONNECTION LIMIT -1
;

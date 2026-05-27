FROM postgres:16-alpine
COPY init.sql /docker-entrypoint-initdb.d/init.sql
ENV POSTGRES_DB=registro
ENV POSTGRES_USER=appuser
ENV POSTGRES_PASSWORD=apppass123
EXPOSE 5432

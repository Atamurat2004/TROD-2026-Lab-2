FROM postgres:17.5-alpine3.21


RUN apk update && apk upgrade --no-cache

COPY init.sql /docker-entrypoint-initdb.d/init.sql

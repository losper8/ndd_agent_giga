FROM postgres:13

COPY ./docker/postgres/db-init.sh /docker-entrypoint-initdb.d/
RUN chmod ugo+rwx /docker-entrypoint-initdb.d/

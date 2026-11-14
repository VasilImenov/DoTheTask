
FROM postgres:18

COPY init/ /docker-entrypoint-initdb.d/

CMD ["postgres", "-c", "timezone=Europe/Sofia"]

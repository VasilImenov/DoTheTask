FROM postgres:18
COPY dvdrental.tar /dvdrental/dvdrental.tar
COPY init/ /docker-entrypoint-initdb.d/
RUN find /docker-entrypoint-initdb.d -type f -exec sed -i 's/\r$//' {} +
CMD ["postgres", "-c", "timezone=Europe/Sofia"]

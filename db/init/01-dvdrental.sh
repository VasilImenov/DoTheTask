#!/bin/bash
set -e
pg_restore --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB" /dvdrental/dvdrental.tar

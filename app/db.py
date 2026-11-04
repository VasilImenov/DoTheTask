import psycopg2
from flask import g
from psycopg2.extras import RealDictCursor


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect()
    return g.db


def query(sql, args=(), one=False):
    with get_db().cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, args)
        rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

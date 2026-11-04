from dotenv import load_dotenv
from flask import Flask


def create_app():
    load_dotenv()
    app = Flask(__name__)

    from . import db, pages

    app.teardown_appcontext(db.close_db)
    app.register_blueprint(pages.bp)
    return app

import os

from dotenv import load_dotenv
from flask import Flask

from src.db import init_db, sanitize_url
from src.routes import bp as api_routes


def create_app() -> Flask:
    app = Flask(__name__)
    load_dotenv()  # take environment variables from .env

    app.config['SQLALCHEMY_DATABASE_URI'] = sanitize_url(os.environ.get('DATABASE_URL'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    init_db(app)

    app.register_blueprint(api_routes, url_prefix='/api')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=os.getenv('PORT', 5000))
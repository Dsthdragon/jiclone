import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS

from config import Config

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()
cors = CORS()


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="build/static", template_folder="build")
    app.config.from_object(config_class)
    app.debug=True
    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    from jiClone.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api/")

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            print("static")
            return send_from_directory(app.static_folder, path)
        elif path != "" and os.path.exists(os.path.join(app.template_folder, path)):
            print("template")
            return send_from_directory(app.template_folder, path)
        else:
            return send_from_directory(app.template_folder, "index.html")

    return app

from jiClone import models

from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

from app.config import Config
from app.extensions import db, jwt, migrate


def create_app():

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Enable CORS
    CORS(app)

    # Swagger API documentation
    Swagger(app)

    # Import models
    from app.models import User, HeritageSite, Contribution, Feedback

    # Register routes
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.public import public_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(public_bp, url_prefix="/api")

    # Home route
    @app.route("/")
    def home():
        return jsonify({
            "message": "Heritage Portal Backend is Running!",
            "status": "success"
        })

    # Health check
    @app.route("/health")
    def health():
        return jsonify({
            "status": "healthy"
        })

    return app
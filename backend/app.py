import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask
from flask_cors import CORS

from backend.routes.generate import generate_bp
from backend.routes.health import health_bp
from backend.services.model_manager import model_manager


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(generate_bp)
    return app


if __name__ == "__main__":
    print("Pre-loading model...")
    model_manager.preload()
    create_app().run(host="0.0.0.0", port=5000, debug=False)

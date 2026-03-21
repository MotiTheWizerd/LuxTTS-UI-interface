from flask import Blueprint, jsonify

from backend.services.model_manager import model_manager

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health")
def health():
    return jsonify({"status": "ok", "model_loaded": model_manager.is_loaded})

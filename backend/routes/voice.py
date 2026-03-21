import io

from flask import Blueprint, jsonify, request

from backend.services.model_manager import model_manager
from backend.services.voice_store import voice_store

voice_bp = Blueprint("voice", __name__)


@voice_bp.route("/api/voices", methods=["GET"])
def list_voices():
    """Return all saved voice IDs."""
    return jsonify({"voices": voice_store.list()})


@voice_bp.route("/api/voices/clone", methods=["POST"])
def clone_voice():
    """Upload audio, encode the voice prompt, and save it."""
    if "prompt_audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "A voice name is required"}), 400

    duration = float(request.form.get("duration", 5))
    rms = float(request.form.get("rms", 0.001))

    prompt_bytes = io.BytesIO(request.files["prompt_audio"].read())

    try:
        model = model_manager.get_model()
        encode_dict = model.encode_prompt(prompt_bytes, duration=duration, rms=rms)
        voice_id = voice_store.save(name, encode_dict)
        return jsonify({"voice_id": voice_id, "message": f"Voice '{voice_id}' saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@voice_bp.route("/api/voices/<voice_id>", methods=["DELETE"])
def delete_voice(voice_id):
    """Delete a saved voice."""
    if voice_store.delete(voice_id):
        return jsonify({"message": f"Voice '{voice_id}' deleted"})
    return jsonify({"error": f"Voice '{voice_id}' not found"}), 404

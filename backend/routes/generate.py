import base64
import io

import soundfile as sf
from flask import Blueprint, Response, jsonify, request, send_file, stream_with_context

from backend.services.model_manager import model_manager
from backend.utils.params import GenerateParams
from backend.utils.sse import sse_done, sse_event

generate_bp = Blueprint("generate", __name__)


@generate_bp.route("/api/generate", methods=["POST"])
def generate():
    if "prompt_audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    params = GenerateParams.from_request(request)
    if not params.text:
        return jsonify({"error": "No text provided"}), 400

    prompt_bytes = io.BytesIO(request.files["prompt_audio"].read())

    try:
        model = model_manager.get_model()
        encoded_prompt = model.encode_prompt(
            prompt_bytes, duration=params.duration, rms=params.rms
        )
        final_wav = model.generate_speech(
            params.text,
            encoded_prompt,
            num_steps=params.num_steps,
            guidance_scale=params.guidance_scale,
            t_shift=params.t_shift,
            speed=params.speed,
            return_smooth=params.return_smooth,
        )

        wav_data = final_wav.numpy().squeeze()
        sample_rate = 24000 if params.return_smooth else 48000

        buf = io.BytesIO()
        sf.write(buf, wav_data, sample_rate, format="WAV")
        buf.seek(0)

        return send_file(buf, mimetype="audio/wav", download_name="output.wav")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@generate_bp.route("/api/generate/stream", methods=["POST"])
def generate_stream():
    if "prompt_audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    params = GenerateParams.from_request(request)
    if not params.text:
        return jsonify({"error": "No text provided"}), 400

    # Read the uploaded bytes eagerly — the request's file stream will be
    # closed by the time the generator runs.
    prompt_bytes = io.BytesIO(request.files["prompt_audio"].read())

    def event_stream():
        try:
            yield sse_event({"type": "status", "stage": "encoding"})

            model = model_manager.get_model()
            encoded_prompt = model.encode_prompt(
                prompt_bytes, duration=params.duration, rms=params.rms
            )

            yield sse_event({"type": "status", "stage": "generating"})

            for chunk in model.generate_speech_streaming(
                params.text,
                encoded_prompt,
                num_steps=params.num_steps,
                guidance_scale=params.guidance_scale,
                t_shift=params.t_shift,
                speed=params.speed,
                return_smooth=params.return_smooth,
            ):
                yield sse_event(
                    {
                        "type": "audio",
                        "chunk_index": chunk["chunk_index"],
                        "total_chunks": chunk["total_chunks"],
                        "sample_rate": chunk["sample_rate"],
                        "is_final": chunk["is_final"],
                        "audio": base64.b64encode(chunk["audio_bytes"]).decode(
                            "ascii"
                        ),
                    }
                )

            yield sse_done()
        except Exception as e:
            yield sse_event({"type": "error", "error": str(e)})

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

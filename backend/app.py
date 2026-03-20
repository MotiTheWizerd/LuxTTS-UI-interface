import sys
import os
import io
import json
import base64
import tempfile
import soundfile as sf
from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)
CORS(app)

lux_tts = None

def get_model():
    global lux_tts
    if lux_tts is None:
        from zipvoice.luxvoice import LuxTTS
        print("Loading LuxTTS model...")
        lux_tts = LuxTTS('YatharthS/LuxTTS', device='cpu', threads=2)
        print("Model loaded.")
    return lux_tts

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "model_loaded": lux_tts is not None})

@app.route('/api/generate', methods=['POST'])
def generate():
    if 'prompt_audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    text = request.form.get('text', '').strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    audio_file = request.files['prompt_audio']
    duration = float(request.form.get('duration', 5))
    rms = float(request.form.get('rms', 0.01))
    num_steps = int(request.form.get('num_steps', 4))
    guidance_scale = float(request.form.get('guidance_scale', 3.0))
    t_shift = float(request.form.get('t_shift', 0.5))
    speed = float(request.form.get('speed', 1.0))
    return_smooth = request.form.get('return_smooth', 'false').lower() == 'true'

    # Save uploaded file to temp
    ext = os.path.splitext(audio_file.filename)[1] or '.wav'
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        model = get_model()
        encoded_prompt = model.encode_prompt(tmp_path, duration=duration, rms=rms)
        final_wav = model.generate_speech(
            text, encoded_prompt,
            num_steps=num_steps,
            guidance_scale=guidance_scale,
            t_shift=t_shift,
            speed=speed,
            return_smooth=return_smooth
        )

        wav_data = final_wav.numpy().squeeze()
        sample_rate = 24000 if return_smooth else 48000

        buf = io.BytesIO()
        sf.write(buf, wav_data, sample_rate, format='WAV')
        buf.seek(0)

        return send_file(buf, mimetype='audio/wav', download_name='output.wav')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.unlink(tmp_path)

@app.route('/api/generate/stream', methods=['POST'])
def generate_stream():
    if 'prompt_audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    text = request.form.get('text', '').strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400

    audio_file = request.files['prompt_audio']
    duration = float(request.form.get('duration', 5))
    rms = float(request.form.get('rms', 0.01))
    num_steps = int(request.form.get('num_steps', 4))
    guidance_scale = float(request.form.get('guidance_scale', 3.0))
    t_shift = float(request.form.get('t_shift', 0.5))
    speed = float(request.form.get('speed', 1.0))
    return_smooth = request.form.get('return_smooth', 'false').lower() == 'true'

    ext = os.path.splitext(audio_file.filename)[1] or '.wav'
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    def event_stream():
        try:
            yield f"data: {json.dumps({'type': 'status', 'stage': 'encoding'})}\n\n"

            model = get_model()
            encoded_prompt = model.encode_prompt(tmp_path, duration=duration, rms=rms)

            yield f"data: {json.dumps({'type': 'status', 'stage': 'generating'})}\n\n"

            for chunk in model.generate_speech_streaming(
                text, encoded_prompt,
                num_steps=num_steps,
                guidance_scale=guidance_scale,
                t_shift=t_shift,
                speed=speed,
                return_smooth=return_smooth,
            ):
                payload = json.dumps({
                    "type": "audio",
                    "chunk_index": chunk["chunk_index"],
                    "total_chunks": chunk["total_chunks"],
                    "sample_rate": chunk["sample_rate"],
                    "is_final": chunk["is_final"],
                    "audio": base64.b64encode(chunk["audio_bytes"]).decode("ascii"),
                })
                yield f"data: {payload}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            os.unlink(tmp_path)

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )

if __name__ == '__main__':
    print("Pre-loading model...")
    get_model()
    app.run(host='0.0.0.0', port=5000, debug=False)

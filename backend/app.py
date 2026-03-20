import sys
import os
import io
import tempfile
import soundfile as sf
from flask import Flask, request, jsonify, send_file
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

if __name__ == '__main__':
    print("Pre-loading model...")
    get_model()
    app.run(host='0.0.0.0', port=5000, debug=False)

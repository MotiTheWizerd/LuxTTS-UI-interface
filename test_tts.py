from zipvoice.luxvoice import LuxTTS
import soundfile as sf

# Load model on CPU
lux_tts = LuxTTS('YatharthS/LuxTTS', device='cpu', threads=2)

text = "Hey, what's up? I'm feeling really great if you ask me honestly!"

# Use a sample audio file for voice cloning - replace with your own .wav file
prompt_audio = '2pac_clone.mp3'

encoded_prompt = lux_tts.encode_prompt(prompt_audio, rms=0.01)
final_wav = lux_tts.generate_speech(text, encoded_prompt, num_steps=4)

final_wav = final_wav.numpy().squeeze()
sf.write('output.wav', final_wav, 48000)
print("Done! Saved to output.wav")

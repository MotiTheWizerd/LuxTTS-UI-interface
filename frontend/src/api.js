const BASE_URL = localStorage.getItem('backendUrl') || 'http://localhost:5000';

export async function generateSpeech(params) {
  const formData = new FormData();
  formData.append('prompt_audio', params.promptAudio);
  formData.append('text', params.text);
  formData.append('duration', params.duration);
  formData.append('rms', params.rms);
  formData.append('num_steps', params.numSteps);
  formData.append('guidance_scale', params.guidanceScale);
  formData.append('t_shift', params.tShift);
  formData.append('speed', params.speed);
  formData.append('return_smooth', params.returnSmooth);

  const res = await fetch(`${BASE_URL}/api/generate`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Generation failed' }));
    throw new Error(err.error || 'Generation failed');
  }

  return res.blob();
}

export async function checkHealth() {
  try {
    const res = await fetch(`${BASE_URL}/api/health`);
    return res.ok;
  } catch {
    return false;
  }
}

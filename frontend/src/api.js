const BASE_URL = localStorage.getItem('backendUrl') || 'http://localhost:5000';

function buildFormData(params) {
  const formData = new FormData();
  if (params.voiceId) {
    formData.append('voice_id', params.voiceId);
  } else if (params.promptAudio) {
    formData.append('prompt_audio', params.promptAudio);
  }
  formData.append('text', params.text);
  formData.append('duration', params.duration);
  formData.append('rms', params.rms);
  formData.append('num_steps', params.numSteps);
  formData.append('guidance_scale', params.guidanceScale);
  formData.append('t_shift', params.tShift);
  formData.append('speed', params.speed);
  formData.append('return_smooth', params.returnSmooth);
  return formData;
}

export async function generateSpeech(params) {
  const res = await fetch(`${BASE_URL}/api/generate`, {
    method: 'POST',
    body: buildFormData(params),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Generation failed' }));
    throw new Error(err.error || 'Generation failed');
  }

  return res.blob();
}

export async function streamSpeech(params, { onStatus, onChunk, onDone, onError }) {
  const res = await fetch(`${BASE_URL}/api/generate/stream`, {
    method: 'POST',
    body: buildFormData(params),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Streaming failed' }));
    throw new Error(err.error || 'Streaming failed');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop();

    for (const line of lines) {
      const data = line.replace(/^data: /, '').trim();
      if (!data) continue;
      if (data === '[DONE]') {
        onDone?.();
        return;
      }

      try {
        const parsed = JSON.parse(data);
        if (parsed.type === 'error' || parsed.error) {
          onError?.(new Error(parsed.error));
          return;
        }

        if (parsed.type === 'status') {
          onStatus?.(parsed.stage);
          continue;
        }

        // Decode base64 WAV to ArrayBuffer for Web Audio API
        const binary = atob(parsed.audio);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);

        onChunk?.({
          chunkIndex: parsed.chunk_index,
          totalChunks: parsed.total_chunks,
          sampleRate: parsed.sample_rate,
          isFinal: parsed.is_final,
          audio: bytes.buffer,
        });
      } catch (e) {
        onError?.(e);
      }
    }
  }
}

// --- Voice management ---

export async function listVoices() {
  const res = await fetch(`${BASE_URL}/api/voices`);
  if (!res.ok) throw new Error('Failed to list voices');
  const data = await res.json();
  return data.voices;
}

export async function cloneVoice(audioFile, name, { duration = 5, rms = 0.001 } = {}) {
  const formData = new FormData();
  formData.append('prompt_audio', audioFile);
  formData.append('name', name);
  formData.append('duration', duration);
  formData.append('rms', rms);

  const res = await fetch(`${BASE_URL}/api/voices/clone`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Clone failed' }));
    throw new Error(err.error || 'Clone failed');
  }
  return res.json();
}

export async function deleteVoice(voiceId) {
  const res = await fetch(`${BASE_URL}/api/voices/${voiceId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Delete failed' }));
    throw new Error(err.error || 'Delete failed');
  }
  return res.json();
}

export async function checkHealth() {
  try {
    const res = await fetch(`${BASE_URL}/api/health`);
    return res.ok;
  } catch {
    return false;
  }
}

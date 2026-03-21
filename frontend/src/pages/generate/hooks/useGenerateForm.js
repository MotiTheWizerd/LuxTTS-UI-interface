import { useState, useCallback } from 'react';

const DEFAULT_ADVANCED = {
  duration: 5,
  rms: 0.01,
  numSteps: 4,
  guidanceScale: 3.0,
  tShift: 0.5,
  returnSmooth: false,
};

export default function useGenerateForm() {
  const [file, setFile] = useState(null);
  const [voiceId, setVoiceId] = useState(null);
  const [text, setText] = useState('');
  const [speed, setSpeed] = useState(1.0);
  const [mode, setMode] = useState('standard');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [advanced, setAdvanced] = useState(DEFAULT_ADVANCED);

  const updateAdvanced = useCallback((key, value) => {
    setAdvanced((prev) => ({ ...prev, [key]: value }));
  }, []);

  const toggleAdvanced = useCallback(() => {
    setShowAdvanced((prev) => !prev);
  }, []);

  const clearFile = useCallback(() => setFile(null), []);

  const selectVoice = useCallback((id) => {
    setVoiceId(id);
    setFile(null);
  }, []);

  const clearVoice = useCallback(() => setVoiceId(null), []);

  const buildParams = useCallback(() => ({
    promptAudio: voiceId ? null : file,
    voiceId: voiceId || null,
    text: text.trim(),
    speed,
    ...advanced,
  }), [file, voiceId, text, speed, advanced]);

  const canGenerate = (file || voiceId) && text.trim();

  return {
    file, setFile, clearFile,
    voiceId, selectVoice, clearVoice,
    text, setText,
    speed, setSpeed,
    mode, setMode,
    showAdvanced, toggleAdvanced,
    advanced, updateAdvanced,
    canGenerate,
    buildParams,
  };
}

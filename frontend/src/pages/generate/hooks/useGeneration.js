import { useState, useCallback } from 'react';
import { generateSpeech, streamSpeech } from '../../../api';

export default function useGeneration() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [resultUrl, setResultUrl] = useState(null);
  const [streamChunks, setStreamChunks] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStage, setStreamStage] = useState(null);
  const [error, setError] = useState(null);

  const resetStreaming = useCallback(() => {
    setIsStreaming(false);
    setStreamStage(null);
    setIsGenerating(false);
  }, []);

  const generateStandard = useCallback(async (params) => {
    setStreamChunks([]);
    setError(null);
    setIsGenerating(true);

    try {
      const blob = await generateSpeech(params);
      setResultUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(blob);
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setIsGenerating(false);
    }
  }, []);

  const generateStreaming = useCallback(async (params) => {
    setStreamChunks([]);
    setResultUrl(null);
    setError(null);
    setIsGenerating(true);
    setIsStreaming(true);
    setStreamStage('encoding');

    try {
      await streamSpeech(params, {
        onStatus: (stage) => setStreamStage(stage),
        onChunk: (chunk) => {
          setStreamStage('generating');
          setStreamChunks((prev) => [...prev, chunk]);
        },
        onDone: () => resetStreaming(),
        onError: (err) => {
          setError(err.message);
          resetStreaming();
        },
      });
    } catch (e) {
      setError(e.message);
      resetStreaming();
    }
  }, [resetStreaming]);

  const generate = useCallback((params, mode) => {
    if (mode === 'streaming') {
      return generateStreaming(params);
    }
    return generateStandard(params);
  }, [generateStandard, generateStreaming]);

  return {
    isGenerating,
    resultUrl,
    streamChunks,
    isStreaming,
    streamStage,
    error,
    generate,
  };
}

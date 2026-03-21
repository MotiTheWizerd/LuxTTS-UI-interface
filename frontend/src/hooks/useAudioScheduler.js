import { useRef, useState, useCallback } from 'react';

/**
 * Schedules decoded audio buffers on a Web Audio API timeline
 * for gapless, sample-accurate playback of streaming chunks.
 */
export default function useAudioScheduler() {
  const ctxRef = useRef(null);
  const nextTimeRef = useRef(0);
  const sourcesRef = useRef([]);
  const [playing, setPlaying] = useState(false);
  const [currentChunk, setCurrentChunk] = useState(0);
  const [progress, setProgress] = useState(0);
  const activeRef = useRef(false);
  const totalDurationRef = useRef(0);
  const timerRef = useRef(null);
  const totalChunksRef = useRef(1);
  const scheduledChunksRef = useRef(0);

  const getContext = useCallback(() => {
    if (!ctxRef.current) {
      ctxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    return ctxRef.current;
  }, []);

  const startProgressTimer = useCallback(() => {
    if (timerRef.current) return;
    timerRef.current = setInterval(() => {
      const ctx = ctxRef.current;
      if (!ctx || !activeRef.current) return;
      const total = totalDurationRef.current;
      if (total <= 0) return;
      const elapsed = ctx.currentTime;
      setProgress(Math.min((elapsed / total) * 100, 100));
    }, 100);
  }, []);

  const stopProgressTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const scheduleChunk = useCallback(async (chunk) => {
    const ctx = getContext();

    // Resume context if suspended (autoplay policy)
    if (ctx.state === 'suspended') {
      await ctx.resume();
    }

    const arrayBuffer = chunk.audio;
    const audioBuffer = await ctx.decodeAudioData(arrayBuffer);

    const source = ctx.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(ctx.destination);

    // Schedule at the end of the current timeline
    const startAt = Math.max(nextTimeRef.current, ctx.currentTime);
    source.start(startAt);

    nextTimeRef.current = startAt + audioBuffer.duration;
    totalDurationRef.current = nextTimeRef.current;
    scheduledChunksRef.current += 1;
    totalChunksRef.current = chunk.totalChunks || totalChunksRef.current;

    sourcesRef.current.push(source);
    setCurrentChunk(scheduledChunksRef.current);

    if (!activeRef.current) {
      activeRef.current = true;
      setPlaying(true);
      startProgressTimer();
    }

    // Detect when the last scheduled source ends
    source.onended = () => {
      // Remove from tracked sources
      sourcesRef.current = sourcesRef.current.filter((s) => s !== source);
      if (sourcesRef.current.length === 0 && chunk.isFinal) {
        activeRef.current = false;
        setPlaying(false);
        setProgress(100);
        stopProgressTimer();
      }
    };
  }, [getContext, startProgressTimer, stopProgressTimer]);

  const togglePlay = useCallback(async () => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    if (playing) {
      await ctx.suspend();
      setPlaying(false);
    } else {
      await ctx.resume();
      setPlaying(true);
    }
  }, [playing]);

  const markComplete = useCallback(() => {
    activeRef.current = false;
    setPlaying(false);
    setProgress(100);
    stopProgressTimer();
  }, [stopProgressTimer]);

  const reset = useCallback(() => {
    stopProgressTimer();
    sourcesRef.current.forEach((s) => {
      try { s.stop(); } catch (_) { /* already stopped */ }
    });
    sourcesRef.current = [];
    nextTimeRef.current = 0;
    totalDurationRef.current = 0;
    scheduledChunksRef.current = 0;
    totalChunksRef.current = 1;
    activeRef.current = false;
    setPlaying(false);
    setCurrentChunk(0);
    setProgress(0);

    if (ctxRef.current) {
      ctxRef.current.close();
      ctxRef.current = null;
    }
  }, [stopProgressTimer]);

  return {
    playing,
    currentChunk,
    progress,
    isActive: activeRef,
    scheduleChunk,
    togglePlay,
    markComplete,
    reset,
  };
}

import { useRef, useState, useCallback } from 'react';

/**
 * Controls audio element playback — play/pause, sequential chunk
 * playback, progress tracking, and objectURL lifecycle.
 */
export default function useAudioPlayback() {
  const audioRef = useRef();
  const [playing, setPlaying] = useState(false);
  const [currentChunk, setCurrentChunk] = useState(0);
  const [progress, setProgress] = useState(0);
  const activeRef = useRef(false);

  const playChunk = useCallback((chunk, onEnded) => {
    const audio = audioRef.current;
    if (!audio) return;

    const url = URL.createObjectURL(chunk.audio);
    audio.src = url;

    audio.play().then(() => {
      activeRef.current = true;
      setPlaying(true);
      setCurrentChunk(chunk.chunkIndex + 1);
    }).catch(() => {
      activeRef.current = false;
      setPlaying(false);
    });

    audio.onended = () => {
      URL.revokeObjectURL(url);
      onEnded?.();
    };

    audio.ontimeupdate = () => {
      if (!audio.duration) return;
      const chunkProgress = audio.currentTime / audio.duration;
      const totalChunks = chunk.totalChunks || 1;
      const overall = ((chunk.chunkIndex + chunkProgress) / totalChunks) * 100;
      setProgress(Math.min(overall, 100));
    };
  }, []);

  const togglePlay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      audio.play();
      setPlaying(true);
    }
  }, [playing]);

  const markComplete = useCallback(() => {
    activeRef.current = false;
    setPlaying(false);
    setProgress(100);
  }, []);

  return {
    audioRef,
    playing,
    currentChunk,
    progress,
    isActive: activeRef,
    playChunk,
    togglePlay,
    markComplete,
  };
}

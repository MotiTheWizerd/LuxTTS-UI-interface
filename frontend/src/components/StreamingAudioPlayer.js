import { useEffect, useRef } from 'react';
import { HiDownload } from 'react-icons/hi';
import useAudioScheduler from '../hooks/useAudioScheduler';
import PlaybackControls from './PlaybackControls';

export default function StreamingAudioPlayer({ chunks, isStreaming, stage }) {
  const {
    playing,
    currentChunk,
    progress,
    scheduleChunk,
    togglePlay,
    reset,
  } = useAudioScheduler();

  const processedCountRef = useRef(0);
  const rawChunksRef = useRef([]);

  // Schedule new chunks as they arrive — no queue, straight to the timeline
  useEffect(() => {
    if (!chunks || chunks.length === 0) return;
    if (processedCountRef.current >= chunks.length) return;

    const newChunks = chunks.slice(processedCountRef.current);
    processedCountRef.current = chunks.length;

    for (const chunk of newChunks) {
      rawChunksRef.current.push(chunk.audio);
      scheduleChunk(chunk);
    }
  }, [chunks, scheduleChunk]);

  // Reset when a new generation starts (chunks cleared)
  useEffect(() => {
    if (!chunks || chunks.length === 0) {
      processedCountRef.current = 0;
      rawChunksRef.current = [];
      reset();
    }
  }, [chunks, reset]);

  const handleDownload = () => {
    const buffers = rawChunksRef.current;
    if (buffers.length === 0) return;
    // Merge ArrayBuffers into a single WAV blob for download
    const blobs = buffers.map((buf) => new Blob([buf], { type: 'audio/wav' }));
    const merged = new Blob(blobs, { type: 'audio/wav' });
    const url = URL.createObjectURL(merged);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'output.wav';
    a.click();
    URL.revokeObjectURL(url);
  };

  const totalChunks = chunks?.[0]?.totalChunks || '?';
  const hasChunks = chunks && chunks.length > 0;

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center gap-3">
        <PlaybackControls
          playing={playing}
          progress={progress}
          currentChunk={currentChunk}
          totalChunks={totalChunks}
          isStreaming={isStreaming}
          stage={stage}
          hasChunks={hasChunks}
          onTogglePlay={togglePlay}
        />

        <button
          onClick={handleDownload}
          disabled={!hasChunks || isStreaming}
          className={`transition-colors shrink-0 ${
            hasChunks && !isStreaming
              ? 'text-gray-400 hover:text-indigo-400'
              : 'text-gray-700 cursor-not-allowed'
          }`}
        >
          <HiDownload className="text-lg" />
        </button>
      </div>
    </div>
  );
}

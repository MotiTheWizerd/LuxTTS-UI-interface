import { useCallback, useRef } from 'react';
import { HiDownload } from 'react-icons/hi';
import useChunkQueue from '../hooks/useChunkQueue';
import useAudioPlayback from '../hooks/useAudioPlayback';
import PlaybackControls from './PlaybackControls';

export default function StreamingAudioPlayer({ chunks, isStreaming, stage }) {
  const {
    audioRef,
    playing,
    currentChunk,
    progress,
    isActive,
    playChunk,
    togglePlay,
    markComplete,
  } = useAudioPlayback();

  // Stable ref so the queue callback always sees the latest playNext
  const playNextRef = useRef();

  const { dequeue, allBlobs } = useChunkQueue(chunks, () => {
    if (!isActive.current) playNextRef.current();
  });

  const playNext = useCallback(() => {
    const next = dequeue();
    if (next) {
      playChunk(next, () => playNextRef.current());
    } else {
      markComplete();
    }
  }, [dequeue, playChunk, markComplete]);

  playNextRef.current = playNext;

  const handleDownload = () => {
    if (allBlobs.current.length === 0) return;
    const merged = new Blob(allBlobs.current, { type: 'audio/wav' });
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
      <audio ref={audioRef} className="hidden" />

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

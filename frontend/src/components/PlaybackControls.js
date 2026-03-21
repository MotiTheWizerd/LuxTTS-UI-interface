import { HiPlay, HiPause } from 'react-icons/hi';

export default function PlaybackControls({
  playing,
  progress,
  currentChunk,
  totalChunks,
  isStreaming,
  stage,
  hasChunks,
  onTogglePlay,
}) {
  return (
    <>
      <button
        onClick={onTogglePlay}
        disabled={!hasChunks}
        className={`w-10 h-10 flex items-center justify-center rounded-full transition-colors shrink-0 ${
          hasChunks
            ? 'bg-indigo-600 hover:bg-indigo-500'
            : 'bg-gray-700 cursor-not-allowed'
        }`}
      >
        {playing ? <HiPause /> : <HiPlay />}
      </button>

      <div className="flex-1">
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-500 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-gray-500 font-mono">
            {isStreaming ? (
              <span className="text-indigo-400 flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 bg-indigo-400 rounded-full animate-pulse" />
                {stage === 'encoding'
                  ? 'Encoding voice...'
                  : `Streaming ${currentChunk}/${totalChunks}`}
              </span>
            ) : hasChunks ? (
              'Complete'
            ) : (
              'Waiting...'
            )}
          </span>
          <span className="text-xs text-gray-500 font-mono">
            {currentChunk}/{totalChunks} chunks
          </span>
        </div>
      </div>
    </>
  );
}

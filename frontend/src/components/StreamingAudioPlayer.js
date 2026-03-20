import { useRef, useState, useEffect, useCallback } from 'react';
import { HiPlay, HiPause, HiDownload } from 'react-icons/hi';

export default function StreamingAudioPlayer({ chunks, isStreaming, stage }) {
  const [playing, setPlaying] = useState(false);
  const [currentChunk, setCurrentChunk] = useState(0);
  const [progress, setProgress] = useState(0);
  const audioRef = useRef();
  const queueRef = useRef([]);
  const playingRef = useRef(false);
  const allBlobsRef = useRef([]);

  // Queue incoming chunks for sequential playback
  useEffect(() => {
    if (!chunks || chunks.length === 0) return;

    const latest = chunks[chunks.length - 1];

    // Avoid re-adding already queued chunks
    if (queueRef.current.length >= chunks.length) return;
    queueRef.current.push(latest);
    allBlobsRef.current.push(latest.audio);

    // Auto-play if not already playing
    if (!playingRef.current) {
      playNext();
    }
  }, [chunks]);

  const playNext = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (queueRef.current.length === 0) {
      playingRef.current = false;
      setPlaying(false);
      setProgress(100);
      return;
    }

    const chunk = queueRef.current.shift();
    const url = URL.createObjectURL(chunk.audio);

    audio.src = url;
    audio.play().then(() => {
      playingRef.current = true;
      setPlaying(true);
      setCurrentChunk(chunk.chunkIndex + 1);
    }).catch(() => {
      playingRef.current = false;
      setPlaying(false);
    });

    audio.onended = () => {
      URL.revokeObjectURL(url);
      playNext();
    };

    audio.ontimeupdate = () => {
      if (!audio.duration) return;
      const chunkProgress = audio.currentTime / audio.duration;
      const totalChunks = chunk.totalChunks || 1;
      const overall = ((chunk.chunkIndex + chunkProgress) / totalChunks) * 100;
      setProgress(Math.min(overall, 100));
    };
  }, []);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      audio.play();
      setPlaying(true);
    }
  };

  // Merge all received blobs for download
  const handleDownload = () => {
    if (allBlobsRef.current.length === 0) return;
    // Use the last complete blob if only one chunk, otherwise merge
    const merged = new Blob(allBlobsRef.current, { type: 'audio/wav' });
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
        <button
          onClick={togglePlay}
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
                  {stage === 'encoding' ? 'Encoding voice...' : `Streaming ${currentChunk}/${totalChunks}`}
                </span>
              ) : hasChunks ? (
                'Complete'
              ) : (
                'Waiting...'
              )}
            </span>
            <span className="text-xs text-gray-500 font-mono">
              {chunks?.length || 0}/{totalChunks} chunks
            </span>
          </div>
        </div>

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

import { useRef, useState, useEffect } from 'react';
import { HiPlay, HiPause, HiDownload } from 'react-icons/hi';

export default function AudioPlayer({ src }) {
  const audioRef = useRef();
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTime = () => setCurrentTime(audio.currentTime);
    const onMeta = () => setDuration(audio.duration);
    const onEnd = () => setPlaying(false);

    audio.addEventListener('timeupdate', onTime);
    audio.addEventListener('loadedmetadata', onMeta);
    audio.addEventListener('ended', onEnd);

    return () => {
      audio.removeEventListener('timeupdate', onTime);
      audio.removeEventListener('loadedmetadata', onMeta);
      audio.removeEventListener('ended', onEnd);
    };
  }, [src]);

  const toggle = () => {
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setPlaying(!playing);
  };

  const seek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    audioRef.current.currentTime = pct * duration;
  };

  const fmt = (t) => {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const progress = duration ? (currentTime / duration) * 100 : 0;

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
      <audio ref={audioRef} src={src} className="hidden" />
      <div className="flex items-center gap-3">
        <button
          onClick={toggle}
          className="w-10 h-10 flex items-center justify-center rounded-full bg-indigo-600 hover:bg-indigo-500 transition-colors shrink-0"
        >
          {playing ? <HiPause /> : <HiPlay />}
        </button>
        <div className="flex-1">
          <div
            onClick={seek}
            className="h-2 bg-gray-700 rounded-full cursor-pointer overflow-hidden"
          >
            <div
              className="h-full bg-indigo-500 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs text-gray-500 font-mono">{fmt(currentTime)}</span>
            <span className="text-xs text-gray-500 font-mono">{fmt(duration)}</span>
          </div>
        </div>
        <a
          href={src}
          download="output.wav"
          className="text-gray-400 hover:text-indigo-400 transition-colors shrink-0"
        >
          <HiDownload className="text-lg" />
        </a>
      </div>
    </div>
  );
}

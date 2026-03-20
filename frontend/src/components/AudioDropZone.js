import { useState, useRef } from 'react';
import { HiUpload, HiX, HiPlay, HiPause } from 'react-icons/hi';

export default function AudioDropZone({ file, onFileSelect, onRemove }) {
  const [dragging, setDragging] = useState(false);
  const [playing, setPlaying] = useState(false);
  const inputRef = useRef();
  const audioRef = useRef();

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && isAudioFile(f)) onFileSelect(f);
  };

  const handleSelect = (e) => {
    const f = e.target.files[0];
    if (f) onFileSelect(f);
  };

  const isAudioFile = (f) => /\.(wav|mp3|ogg|flac|m4a)$/i.test(f.name);

  const togglePreview = () => {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setPlaying(!playing);
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (file) {
    return (
      <div className="border border-gray-700 rounded-lg p-4 bg-gray-800/50">
        <div className="flex items-center gap-3">
          <button
            onClick={togglePreview}
            className="w-8 h-8 flex items-center justify-center rounded-full bg-indigo-600 hover:bg-indigo-500 transition-colors"
          >
            {playing ? <HiPause className="text-sm" /> : <HiPlay className="text-sm" />}
          </button>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-200 truncate">{file.name}</p>
            <p className="text-xs text-gray-500">{formatSize(file.size)}</p>
          </div>
          <button
            onClick={onRemove}
            className="text-gray-500 hover:text-red-400 transition-colors"
          >
            <HiX />
          </button>
        </div>
        <audio
          ref={audioRef}
          src={URL.createObjectURL(file)}
          onEnded={() => setPlaying(false)}
          className="hidden"
        />
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        dragging
          ? 'border-indigo-500 bg-indigo-500/10'
          : 'border-gray-700 hover:border-gray-600 bg-gray-800/30'
      }`}
    >
      <HiUpload className="mx-auto text-2xl text-gray-500 mb-2" />
      <p className="text-sm text-gray-400">
        Drag & drop a voice file, or <span className="text-indigo-400">browse</span>
      </p>
      <p className="text-xs text-gray-600 mt-1">.wav, .mp3 — minimum 3 seconds</p>
      <input
        ref={inputRef}
        type="file"
        accept=".wav,.mp3,.ogg,.flac,.m4a"
        onChange={handleSelect}
        className="hidden"
      />
    </div>
  );
}

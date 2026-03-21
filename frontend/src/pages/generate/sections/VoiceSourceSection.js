import { useState, useEffect, useCallback } from 'react';
import { HiTrash, HiSave } from 'react-icons/hi';
import AudioDropZone from '../../../components/AudioDropZone';
import { listVoices, cloneVoice, deleteVoice } from '../../../api';

export default function VoiceSourceSection({
  file, onFileSelect, onRemove,
  voiceId, onSelectVoice, onClearVoice,
}) {
  const [voices, setVoices] = useState([]);
  const [cloneName, setCloneName] = useState('');
  const [cloning, setCloning] = useState(false);
  const [error, setError] = useState(null);

  const refreshVoices = useCallback(async () => {
    try {
      const list = await listVoices();
      setVoices(list);
    } catch {
      // silently fail — voices list is optional
    }
  }, []);

  useEffect(() => { refreshVoices(); }, [refreshVoices]);

  const handleClone = async () => {
    if (!file || !cloneName.trim()) return;
    setCloning(true);
    setError(null);
    try {
      const result = await cloneVoice(file, cloneName.trim());
      onSelectVoice(result.voice_id);
      setCloneName('');
      onRemove();
      await refreshVoices();
    } catch (e) {
      setError(e.message);
    } finally {
      setCloning(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteVoice(id);
      if (voiceId === id) onClearVoice();
      await refreshVoices();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
      <h3 className="text-sm font-medium text-gray-300 mb-3">Voice Source</h3>

      {/* Saved voices */}
      {voices.length > 0 && (
        <div className="mb-4">
          <label className="text-xs text-gray-500 mb-1.5 block">Saved Voices</label>
          <div className="flex flex-wrap gap-2">
            {voices.map((v) => (
              <div key={v} className="flex items-center gap-1">
                <button
                  onClick={() => onSelectVoice(v)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    voiceId === v
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  {v}
                </button>
                <button
                  onClick={() => handleDelete(v)}
                  className="text-gray-600 hover:text-red-400 transition-colors p-1"
                  title="Delete voice"
                >
                  <HiTrash className="text-xs" />
                </button>
              </div>
            ))}
          </div>
          {voiceId && (
            <button
              onClick={onClearVoice}
              className="mt-2 text-xs text-gray-500 hover:text-gray-300"
            >
              Use file upload instead
            </button>
          )}
        </div>
      )}

      {/* File upload + clone */}
      {!voiceId && (
        <>
          <AudioDropZone file={file} onFileSelect={onFileSelect} onRemove={onRemove} />
          {file && (
            <div className="mt-3 flex items-center gap-2">
              <input
                type="text"
                placeholder="Voice name..."
                value={cloneName}
                onChange={(e) => setCloneName(e.target.value)}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={handleClone}
                disabled={!cloneName.trim() || cloning}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors ${
                  cloneName.trim() && !cloning
                    ? 'bg-indigo-600 hover:bg-indigo-500 text-white'
                    : 'bg-gray-800 text-gray-600 cursor-not-allowed'
                }`}
              >
                <HiSave />
                {cloning ? 'Cloning...' : 'Save Voice'}
              </button>
            </div>
          )}
        </>
      )}

      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </div>
  );
}

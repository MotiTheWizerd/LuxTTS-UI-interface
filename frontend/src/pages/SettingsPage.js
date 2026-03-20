import { useState } from 'react';

export default function SettingsPage() {
  const [url, setUrl] = useState(localStorage.getItem('backendUrl') || 'http://localhost:5000');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    localStorage.setItem('backendUrl', url);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Backend URL</h3>
        <div className="flex gap-3">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
          >
            {saved ? 'Saved!' : 'Save'}
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-2">The URL where the Flask backend is running</p>
      </div>
    </div>
  );
}

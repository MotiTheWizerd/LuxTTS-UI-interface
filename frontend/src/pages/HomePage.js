import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { HiLightningBolt, HiStatusOnline, HiStatusOffline } from 'react-icons/hi';
import { checkHealth } from '../api';

export default function HomePage() {
  const [backendUp, setBackendUp] = useState(null);

  useEffect(() => {
    checkHealth().then(setBackendUp);
  }, []);

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <h3 className="text-lg font-semibold mb-2">Welcome to LuxTTS</h3>
        <p className="text-sm text-gray-400 mb-4">
          Voice cloning & text-to-speech powered by LuxTTS. Upload a voice sample,
          enter your text, and generate high-quality 48kHz speech.
        </p>
        <Link
          to="/generate"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
        >
          <HiLightningBolt />
          Start Generating
        </Link>
      </div>

      <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Backend Status</h3>
        <div className="flex items-center gap-2">
          {backendUp === null ? (
            <span className="text-sm text-gray-500">Checking...</span>
          ) : backendUp ? (
            <>
              <HiStatusOnline className="text-green-400" />
              <span className="text-sm text-green-400">Connected</span>
            </>
          ) : (
            <>
              <HiStatusOffline className="text-red-400" />
              <span className="text-sm text-red-400">
                Not connected — run <code className="bg-gray-800 px-1.5 py-0.5 rounded text-xs">python backend/app.py</code>
              </span>
            </>
          )}
        </div>
      </div>

      <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Quick Start</h3>
        <ol className="text-sm text-gray-400 space-y-2 list-decimal list-inside">
          <li>Upload a voice sample (min 3 seconds)</li>
          <li>Enter the text you want to synthesize</li>
          <li>Adjust speed and optional advanced settings</li>
          <li>Click Generate and listen to the result</li>
        </ol>
      </div>
    </div>
  );
}

import { HiLightningBolt } from 'react-icons/hi';
import { HiSignal } from 'react-icons/hi2';

export default function ModeToggle({ mode, onChange }) {
  return (
    <div className="flex items-center bg-gray-800 rounded-lg p-0.5 border border-gray-700">
      <button
        onClick={() => onChange('standard')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
          mode === 'standard'
            ? 'bg-indigo-600 text-white'
            : 'text-gray-400 hover:text-gray-200'
        }`}
      >
        <HiLightningBolt className="text-sm" />
        Standard
      </button>
      <button
        onClick={() => onChange('streaming')}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
          mode === 'streaming'
            ? 'bg-indigo-600 text-white'
            : 'text-gray-400 hover:text-gray-200'
        }`}
      >
        <HiSignal className="text-sm" />
        Streaming
      </button>
    </div>
  );
}

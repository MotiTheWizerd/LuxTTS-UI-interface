import { HiLightningBolt } from 'react-icons/hi';
import { HiSignal } from 'react-icons/hi2';
import ModeToggle from '../../../components/ModeToggle';

export default function GenerateButton({
  mode, onModeChange,
  isGenerating, streamStage,
  canGenerate, onGenerate,
}) {
  return (
    <div className="flex items-center gap-3">
      <ModeToggle mode={mode} onChange={onModeChange} />
      <button
        onClick={onGenerate}
        disabled={!canGenerate || isGenerating}
        className={`flex-1 py-3 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-colors ${
          canGenerate && !isGenerating
            ? 'bg-indigo-600 hover:bg-indigo-500 text-white'
            : 'bg-gray-800 text-gray-600 cursor-not-allowed'
        }`}
      >
        {isGenerating ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {mode === 'streaming'
              ? streamStage === 'encoding' ? 'Encoding voice...' : 'Streaming...'
              : 'Generating...'}
          </>
        ) : (
          <>
            {mode === 'streaming' ? <HiSignal /> : <HiLightningBolt />}
            {mode === 'streaming' ? 'Stream Speech' : 'Generate Speech'}
          </>
        )}
      </button>
    </div>
  );
}

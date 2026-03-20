import { useState } from 'react';
import { HiLightningBolt } from 'react-icons/hi';
import { HiSignal } from 'react-icons/hi2';
import AudioDropZone from '../components/AudioDropZone';
import AudioPlayer from '../components/AudioPlayer';
import StreamingAudioPlayer from '../components/StreamingAudioPlayer';
import ModeToggle from '../components/ModeToggle';
import ParameterSlider from '../components/ParameterSlider';
import ParameterToggle from '../components/ParameterToggle';
import AdvancedPanel from '../components/AdvancedPanel';
import { generateSpeech, streamSpeech } from '../api';

export default function GeneratePage() {
  const [file, setFile] = useState(null);
  const [text, setText] = useState('');
  const [speed, setSpeed] = useState(1.0);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [advanced, setAdvanced] = useState({
    duration: 5,
    rms: 0.01,
    numSteps: 4,
    guidanceScale: 3.0,
    tShift: 0.5,
    returnSmooth: false,
  });
  const [mode, setMode] = useState('standard');
  const [isGenerating, setIsGenerating] = useState(false);
  const [resultUrl, setResultUrl] = useState(null);
  const [streamChunks, setStreamChunks] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStage, setStreamStage] = useState(null); // 'encoding' | 'generating' | null
  const [error, setError] = useState(null);

  const updateAdvanced = (key, value) => {
    setAdvanced((prev) => ({ ...prev, [key]: value }));
  };

  const canGenerate = file && text.trim() && !isGenerating;

  const handleGenerate = async () => {
    if (!canGenerate) return;
    setIsGenerating(true);
    setError(null);

    const params = {
      promptAudio: file,
      text: text.trim(),
      speed,
      ...advanced,
    };

    if (mode === 'streaming') {
      setStreamChunks([]);
      setIsStreaming(true);
      setStreamStage('encoding');
      setResultUrl(null);

      try {
        await streamSpeech(params, {
          onStatus: (stage) => {
            setStreamStage(stage);
          },
          onChunk: (chunk) => {
            setStreamStage('generating');
            setStreamChunks((prev) => [...prev, chunk]);
          },
          onDone: () => {
            setIsStreaming(false);
            setStreamStage(null);
            setIsGenerating(false);
          },
          onError: (err) => {
            setError(err.message);
            setIsStreaming(false);
            setStreamStage(null);
            setIsGenerating(false);
          },
        });
      } catch (e) {
        setError(e.message);
        setIsStreaming(false);
        setStreamStage(null);
        setIsGenerating(false);
      }
    } else {
      setStreamChunks([]);
      try {
        const blob = await generateSpeech(params);
        if (resultUrl) URL.revokeObjectURL(resultUrl);
        setResultUrl(URL.createObjectURL(blob));
      } catch (e) {
        setError(e.message);
      } finally {
        setIsGenerating(false);
      }
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      {/* Voice Source */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Voice Source</h3>
        <AudioDropZone
          file={file}
          onFileSelect={setFile}
          onRemove={() => setFile(null)}
        />
      </div>

      {/* Text & Parameters */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-5 space-y-4">
        <div>
          <h3 className="text-sm font-medium text-gray-300 mb-2">Text to Synthesize</h3>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter text to speak..."
            rows={4}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-gray-100 placeholder-gray-600 resize-none focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <p className="text-xs text-gray-600 text-right mt-1">{text.length} chars</p>
        </div>

        <ParameterSlider
          label="Speed"
          value={speed}
          onChange={setSpeed}
          min={0.5}
          max={2.0}
          step={0.1}
          unit="x"
          tooltip="Playback speed multiplier"
        />

        <AdvancedPanel isOpen={showAdvanced} onToggle={() => setShowAdvanced(!showAdvanced)}>
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2 ml-3">Prompt Encoding</p>
          <div className="ml-3 space-y-3">
            <ParameterSlider
              label="Duration"
              value={advanced.duration}
              onChange={(v) => updateAdvanced('duration', v)}
              min={1}
              max={30}
              step={1}
              unit="s"
              tooltip="Seconds to extract from prompt audio"
            />
            <ParameterSlider
              label="RMS"
              value={advanced.rms}
              onChange={(v) => updateAdvanced('rms', v)}
              min={0.001}
              max={0.1}
              step={0.001}
              tooltip="Volume normalization (0.01 recommended)"
            />
          </div>

          <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2 mt-4 ml-3">Quality</p>
          <div className="ml-3 space-y-3">
            <ParameterSlider
              label="Steps"
              value={advanced.numSteps}
              onChange={(v) => updateAdvanced('numSteps', v)}
              min={1}
              max={16}
              step={1}
              tooltip="Higher = better quality, slower generation"
            />
            <ParameterSlider
              label="Guidance"
              value={advanced.guidanceScale}
              onChange={(v) => updateAdvanced('guidanceScale', v)}
              min={0.5}
              max={5.0}
              step={0.1}
              tooltip="How closely to match the voice"
            />
            <ParameterSlider
              label="T-Shift"
              value={advanced.tShift}
              onChange={(v) => updateAdvanced('tShift', v)}
              min={0}
              max={1.0}
              step={0.05}
              tooltip="Lower = fewer errors, less quality"
            />
          </div>

          <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2 mt-4 ml-3">Output</p>
          <div className="ml-3">
            <ParameterToggle
              label="Smooth 24kHz"
              value={advanced.returnSmooth}
              onChange={(v) => updateAdvanced('returnSmooth', v)}
              tooltip="Smoother but lower sample rate (24kHz vs 48kHz)"
            />
          </div>
        </AdvancedPanel>
      </div>

      {/* Mode Toggle + Generate Button */}
      <div className="flex items-center gap-3">
        <ModeToggle mode={mode} onChange={setMode} />
        <button
          onClick={handleGenerate}
          disabled={!canGenerate}
          className={`flex-1 py-3 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-colors ${
            canGenerate
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

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* Output */}
      {resultUrl && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Generated Audio</h3>
          <AudioPlayer src={resultUrl} />
        </div>
      )}

      {(streamChunks.length > 0 || isStreaming) && (
        <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-3">
            {isStreaming ? 'Streaming Audio' : 'Streamed Audio'}
          </h3>
          <StreamingAudioPlayer chunks={streamChunks} isStreaming={isStreaming} stage={streamStage} />
        </div>
      )}
    </div>
  );
}

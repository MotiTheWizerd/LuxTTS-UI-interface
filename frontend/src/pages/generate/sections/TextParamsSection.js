import ParameterSlider from '../../../components/ParameterSlider';
import ParameterToggle from '../../../components/ParameterToggle';
import AdvancedPanel from '../../../components/AdvancedPanel';

export default function TextParamsSection({
  text, onTextChange,
  speed, onSpeedChange,
  showAdvanced, onToggleAdvanced,
  advanced, onAdvancedChange,
}) {
  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-5 space-y-4">
      <div>
        <h3 className="text-sm font-medium text-gray-300 mb-2">Text to Synthesize</h3>
        <textarea
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
          placeholder="Enter text to speak..."
          rows={4}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-gray-100 placeholder-gray-600 resize-none focus:outline-none focus:border-indigo-500 transition-colors"
        />
        <p className="text-xs text-gray-600 text-right mt-1">{text.length} chars</p>
      </div>

      <ParameterSlider
        label="Speed" value={speed} onChange={onSpeedChange}
        min={0.5} max={2.0} step={0.1} unit="x"
        tooltip="Playback speed multiplier"
      />

      <AdvancedPanel isOpen={showAdvanced} onToggle={onToggleAdvanced}>
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2 ml-3">Prompt Encoding</p>
        <div className="ml-3 space-y-3">
          <ParameterSlider
            label="Duration" value={advanced.duration}
            onChange={(v) => onAdvancedChange('duration', v)}
            min={1} max={30} step={1} unit="s"
            tooltip="Seconds to extract from prompt audio"
          />
          <ParameterSlider
            label="RMS" value={advanced.rms}
            onChange={(v) => onAdvancedChange('rms', v)}
            min={0.001} max={0.1} step={0.001}
            tooltip="Volume normalization (0.01 recommended)"
          />
        </div>

        <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2 mt-4 ml-3">Quality</p>
        <div className="ml-3 space-y-3">
          <ParameterSlider
            label="Steps" value={advanced.numSteps}
            onChange={(v) => onAdvancedChange('numSteps', v)}
            min={1} max={16} step={1}
            tooltip="Higher = better quality, slower generation"
          />
          <ParameterSlider
            label="Guidance" value={advanced.guidanceScale}
            onChange={(v) => onAdvancedChange('guidanceScale', v)}
            min={0.5} max={5.0} step={0.1}
            tooltip="How closely to match the voice"
          />
          <ParameterSlider
            label="T-Shift" value={advanced.tShift}
            onChange={(v) => onAdvancedChange('tShift', v)}
            min={0} max={1.0} step={0.05}
            tooltip="Lower = fewer errors, less quality"
          />
        </div>

        <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-2 mt-4 ml-3">Output</p>
        <div className="ml-3">
          <ParameterToggle
            label="Smooth 24kHz" value={advanced.returnSmooth}
            onChange={(v) => onAdvancedChange('returnSmooth', v)}
            tooltip="Smoother but lower sample rate (24kHz vs 48kHz)"
          />
        </div>
      </AdvancedPanel>
    </div>
  );
}

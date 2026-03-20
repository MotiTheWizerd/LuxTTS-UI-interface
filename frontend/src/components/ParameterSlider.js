import { useState } from 'react';
import { HiQuestionMarkCircle } from 'react-icons/hi';

export default function ParameterSlider({ label, value, onChange, min, max, step, tooltip, unit }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="flex items-center gap-3">
      <div className="w-32 flex items-center gap-1 shrink-0">
        <span className="text-sm text-gray-300">{label}</span>
        {tooltip && (
          <div className="relative">
            <HiQuestionMarkCircle
              className="text-gray-500 hover:text-gray-300 cursor-help text-sm"
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            />
            {showTooltip && (
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-gray-700 text-xs text-gray-200 rounded-md whitespace-nowrap z-10">
                {tooltip}
              </div>
            )}
          </div>
        )}
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="flex-1 accent-indigo-500 h-1.5 bg-gray-700 rounded-full appearance-none cursor-pointer range-slider"
      />
      <span className="w-16 text-right text-sm text-gray-400 font-mono shrink-0">
        {value}{unit || ''}
      </span>
    </div>
  );
}

import { useState } from 'react';
import { HiQuestionMarkCircle } from 'react-icons/hi';

export default function ParameterToggle({ label, value, onChange, tooltip }) {
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
      <button
        onClick={() => onChange(!value)}
        className={`relative w-10 h-5 rounded-full transition-colors ${
          value ? 'bg-indigo-600' : 'bg-gray-600'
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
            value ? 'translate-x-5' : ''
          }`}
        />
      </button>
      <span className="text-sm text-gray-400">{value ? 'On' : 'Off'}</span>
    </div>
  );
}

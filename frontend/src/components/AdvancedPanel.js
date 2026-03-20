import { HiChevronRight } from 'react-icons/hi';

export default function AdvancedPanel({ isOpen, onToggle, children }) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
      >
        <HiChevronRight
          className={`transition-transform ${isOpen ? 'rotate-90' : ''}`}
        />
        Advanced Settings
      </button>
      {isOpen && (
        <div className="mt-3 pl-2 space-y-3 border-l border-gray-700 ml-1.5">
          {children}
        </div>
      )}
    </div>
  );
}

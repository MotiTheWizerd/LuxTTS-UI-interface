import AudioDropZone from '../../../components/AudioDropZone';

export default function VoiceSourceSection({ file, onFileSelect, onRemove }) {
  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-5">
      <h3 className="text-sm font-medium text-gray-300 mb-3">Voice Source</h3>
      <AudioDropZone file={file} onFileSelect={onFileSelect} onRemove={onRemove} />
    </div>
  );
}

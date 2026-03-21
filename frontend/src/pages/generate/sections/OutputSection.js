import AudioPlayer from '../../../components/AudioPlayer';
import StreamingAudioPlayer from '../../../components/StreamingAudioPlayer';

export default function OutputSection({
  error, resultUrl,
  streamChunks, isStreaming, streamStage,
}) {
  return (
    <>
      {error && (
        <div className="bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

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
    </>
  );
}

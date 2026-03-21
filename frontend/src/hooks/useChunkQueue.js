import { useRef, useEffect, useCallback } from 'react';

/**
 * Manages incoming audio chunks — deduplicates, queues for playback,
 * and collects all blobs for download.
 */
export default function useChunkQueue(chunks, onNewChunk) {
  const queueRef = useRef([]);
  const allBlobsRef = useRef([]);
  const processedCountRef = useRef(0);

  useEffect(() => {
    if (!chunks || chunks.length === 0) return;
    if (processedCountRef.current >= chunks.length) return;

    const latest = chunks[chunks.length - 1];
    processedCountRef.current = chunks.length;
    queueRef.current.push(latest);
    allBlobsRef.current.push(latest.audio);

    onNewChunk?.();
  }, [chunks, onNewChunk]);

  const dequeue = useCallback(() => {
    return queueRef.current.shift() ?? null;
  }, []);

  const hasQueued = useCallback(() => {
    return queueRef.current.length > 0;
  }, []);

  const reset = useCallback(() => {
    queueRef.current = [];
    allBlobsRef.current = [];
    processedCountRef.current = 0;
  }, []);

  return { dequeue, hasQueued, allBlobs: allBlobsRef };
}

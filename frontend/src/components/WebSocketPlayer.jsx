import React, { useEffect, useRef, useState } from 'react';

/**
 * WebSocket player that streams MJPEG frames directly from the backend.
 * Bypasses the browser's 6 HTTP connection limit and avoids WHEP WebRTC negotiation issues.
 */
export default function WebSocketPlayer({ cameraId, preview = 0, style = {}, placeholderSrc }) {
  const imgRef = useRef(null);
  const [status, setStatus] = useState('connecting'); // connecting, playing, error
  const wsRef = useRef(null);
  const objectUrlRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    let retryCount = 0;
    let retryTimer = null;

    const connect = () => {
      if (cancelled) return;
      
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const wsUrl = baseUrl.replace(/^http/, 'ws') + `/api/cameras/${cameraId}/ws-stream?preview=${preview}`;
      
      setStatus('connecting');
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.binaryType = 'blob';

      ws.onopen = () => {
        if (cancelled) return;
        setStatus('playing');
        retryCount = 0;
      };

      ws.onmessage = (event) => {
        if (cancelled || !imgRef.current) return;
        
        // Clean up previous blob URL to avoid memory leaks
        if (objectUrlRef.current) {
          URL.revokeObjectURL(objectUrlRef.current);
        }
        
        const blobUrl = URL.createObjectURL(event.data);
        objectUrlRef.current = blobUrl;
        imgRef.current.src = blobUrl;
      };

      ws.onclose = () => {
        if (cancelled) return;
        setStatus('error');
        // Exponential backoff
        const delay = Math.min(2000 * Math.pow(2, retryCount), 30000);
        retryCount++;
        retryTimer = setTimeout(connect, delay);
      };
      
      ws.onerror = () => {
        if (cancelled) return;
        setStatus('error');
      }
    };

    connect();

    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
      }
      if (imgRef.current) {
        imgRef.current.src = '';
      }
    };
  }, [cameraId, preview]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', background: '#000', ...style }}>
      {placeholderSrc && status !== 'playing' && (
        <img 
          src={placeholderSrc} 
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover', zIndex: 1 }} 
          alt="Loading..."
        />
      )}
      
      {status === 'error' && !placeholderSrc && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: 10, gap: '8px' }}>
          <div style={{ color: '#ff4444', fontSize: '18px', fontWeight: 'bold' }}>UNABLE TO STREAM</div>
          <div style={{ color: '#888', fontSize: '12px' }}>Retrying connection...</div>
        </div>
      )}
      
      {status === 'connecting' && !placeholderSrc && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: 10, gap: '8px' }}>
          <div style={{ color: '#0ea5e9', fontSize: '14px' }}>Connecting...</div>
        </div>
      )}
      
      <img
        ref={imgRef}
        alt={`Live stream for ${cameraId}`}
        style={{
          width: '100%',
          height: '100%',
          objectFit: style.objectFit || 'cover',
          display: status === 'playing' ? 'block' : 'none',
          zIndex: 2,
          position: 'relative'
        }}
      />
    </div>
  );
}

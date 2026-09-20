import React, { useEffect, useRef, useState } from 'react';

/**
 * WebRTC (WHEP) player that routes through the backend proxy at
 * /api/cameras/{id}/webrtc so Sentinel auth credentials stay server-side.
 *
 * Features:
 *  • Exponential backoff reconnection (2 s → cap 30 s)
 *  • Graceful fallback UI on error
 *  • Cleans up PeerConnection on unmount
 */
export default function WebRTCPlayer({ cameraId, delay = 0, autoPlay = true, muted = true, style = {}, onStatusChange, placeholderSrc }) {
  const videoRef = useRef(null);
  const pcRef = useRef(null);
  const retryRef = useRef(null);
  const [status, setStatus] = useState('connecting'); // connecting, playing, error

  useEffect(() => {
    let cancelled = false;
    let retryCount = 0;

    const connect = async () => {
      if (cancelled) return;

      if (pcRef.current) {
        try { pcRef.current.close(); } catch (_) {}
      }

      const pc = new RTCPeerConnection();
      pcRef.current = pc;

      pc.addTransceiver('video', { direction: 'recvonly' });
      pc.addTransceiver('audio', { direction: 'recvonly' });

      pc.ontrack = (event) => {
        if (videoRef.current && videoRef.current.srcObject !== event.streams[0]) {
          videoRef.current.srcObject = event.streams[0];
          videoRef.current.play().catch((e) => console.log('Autoplay blocked or failed:', e));
        }
      };

      pc.onconnectionstatechange = () => {
        if (cancelled) return;
        if (pc.connectionState === 'connected') {
          setStatus('playing');
          retryCount = 0;
          if (onStatusChange) onStatusChange('online');
        } else if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
          setStatus('error');
          if (onStatusChange) onStatusChange('offline');
          const delay = Math.min(2000 * Math.pow(2, retryCount), 30000);
          retryCount++;
          retryRef.current = setTimeout(connect, delay);
        }
      };

      try {
        setStatus('connecting');
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        await new Promise((resolve) => {
          if (pc.iceGatheringState === 'complete') {
            resolve();
          } else {
            const checkState = () => {
              if (pc.iceGatheringState === 'complete') {
                pc.removeEventListener('icegatheringstatechange', checkState);
                resolve();
              }
            };
            pc.addEventListener('icegatheringstatechange', checkState);
            setTimeout(() => {
              pc.removeEventListener('icegatheringstatechange', checkState);
              resolve();
            }, 1500);
          }
        });

        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/api/cameras/${cameraId}/webrtc`, {
          method: 'POST',
          body: pc.localDescription.sdp,
          headers: {
            'Content-Type': 'application/sdp'
          }
        });

        if (!response.ok) {
          throw new Error(`WHEP proxy returned ${response.status}`);
        }

        const answerSdp = await response.text();
        await pc.setRemoteDescription(new RTCSessionDescription({
          type: 'answer',
          sdp: answerSdp
        }));

      } catch (err) {
        console.error("WebRTC Error for", cameraId, err);
        if (!cancelled) {
          setStatus('error');
          if (onStatusChange) onStatusChange('offline');
          const delay = Math.min(2000 * Math.pow(2, retryCount), 30000);
          retryCount++;
          retryRef.current = setTimeout(connect, delay);
        }
      }
    };

    let initTimer;
    if (delay > 0) {
      initTimer = setTimeout(connect, delay);
    } else {
      connect();
    }

    return () => {
      cancelled = true;
      if (initTimer) clearTimeout(initTimer);
      if (retryRef.current) clearTimeout(retryRef.current);
      if (pcRef.current) {
        try { pcRef.current.close(); } catch (_) {}
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, [cameraId, delay]);

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
      
      <video
        ref={videoRef}
        autoPlay={autoPlay}
        muted={muted}
        playsInline
        onPlaying={() => setStatus('playing')}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          display: status === 'playing' ? 'block' : 'none',
          zIndex: 2,
          position: 'relative'
        }}
      />
    </div>
  );
}

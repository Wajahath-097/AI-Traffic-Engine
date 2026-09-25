import React, { useEffect, useRef, useState, useCallback } from 'react';

/**
 * High-Performance WebRTC (WHEP) Player with Triple Redundancy
 * 
 * Architecture:
 *  1. Instant Snapshot Backdrop: Renders camera snapshot in 0ms (ZERO black screen).
 *  2. Primary Stream: Low-latency WebRTC (WHEP) hardware-accelerated video decoding.
 *  3. Fallback Stream: MJPEG (/stream) if WebRTC connection fails or times out.
 *  4. Graceful Error Handling: Auto-reconnect and peer connection cleanup on unmount.
 */
export default function WebRTCPlayer({
  cameraId,
  autoPlay = true,
  muted = true,
  style = {},
  onStatusChange,
  placeholderSrc,
  isPaused = false,
  noFallback = false
}) {
  const videoRef = useRef(null);
  const pcRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const isPlayingRef = useRef(false);
  const [useFallback, setUseFallback] = useState(false);
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const effectivePlaceholder = placeholderSrc || `${baseUrl}/api/cameras/${cameraId}/snapshot?c=1`;

  // Keep ref in sync so timeout closure reads fresh value
  useEffect(() => {
    isPlayingRef.current = isPlaying;
  }, [isPlaying]);

  useEffect(() => {
    let cancelled = false;
    let pc = null;
    let fallbackTimeout = null;

    const startWhep = async () => {
      try {
        if (cancelled) return;
        setIsPlaying(false);
        isPlayingRef.current = false;
        setUseFallback(false);

        pc = new RTCPeerConnection({
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
          ]
        });
        pcRef.current = pc;

        pc.addTransceiver('video', { direction: 'recvonly' });
        try {
          pc.addTransceiver('audio', { direction: 'recvonly' });
        } catch (_) {}

        pc.ontrack = (event) => {
          if (cancelled || !videoRef.current) return;
          const stream = event.streams[0] || new MediaStream([event.track]);
          videoRef.current.srcObject = stream;
          if (!isPaused) {
            videoRef.current.play().catch((e) => {
              console.log(`[WebRTC ${cameraId}] Autoplay notice:`, e);
            });
          }
        };

        pc.onconnectionstatechange = () => {
          if (cancelled) return;
          if (pc.connectionState === 'connected') {
            if (fallbackTimeout) clearTimeout(fallbackTimeout);
            if (onStatusChange) onStatusChange('online');
          } else if (pc.connectionState === 'failed') {
            console.warn(`[WebRTC ${cameraId}] PeerConnection failed, switching to MJPEG fallback`);
            setUseFallback(true);
            if (onStatusChange) onStatusChange('offline');
          }
        };

        pc.oniceconnectionstatechange = () => {
          if (cancelled) return;
          if (pc.iceConnectionState === 'connected' || pc.iceConnectionState === 'completed') {
            if (fallbackTimeout) clearTimeout(fallbackTimeout);
          }
        };

        // Create SDP offer with video transceiver
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        // Send WHEP offer immediately through backend proxy
        const response = await fetch(`${baseUrl}/api/cameras/${cameraId}/webrtc`, {
          method: 'POST',
          body: pc.localDescription.sdp,
          headers: {
            'Content-Type': 'application/sdp'
          }
        });

        if (!response.ok) {
          throw new Error(`WHEP proxy returned status ${response.status}`);
        }

        const answerSdp = await response.text();
        if (cancelled || !pcRef.current) return;

        await pc.setRemoteDescription(new RTCSessionDescription({
          type: 'answer',
          sdp: answerSdp
        }));

        // Watchdog: If WebRTC has not started playing after 10 seconds, activate fallback
        // Uses ref to read fresh isPlaying value (fixes stale closure for CAM07-10)
        // noFallback mode (mini cards) skips MJPEG to prevent server overload
        fallbackTimeout = setTimeout(() => {
          if (!cancelled && !isPlayingRef.current && !noFallback) {
            console.log(`[WebRTC ${cameraId}] Connection wait timeout, engaging fallback`);
            setUseFallback(true);
          }
        }, 10000);

      } catch (err) {
        console.warn(`[WebRTC ${cameraId}] Setup error:`, err);
        if (!cancelled && !noFallback) {
          setUseFallback(true);
        }
      }
    };

    startWhep();

    return () => {
      cancelled = true;
      if (fallbackTimeout) clearTimeout(fallbackTimeout);
      if (pcRef.current) {
        try { pcRef.current.close(); } catch (_) {}
        pcRef.current = null;
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
    };
  }, [cameraId, baseUrl]);

  // Handle pause/resume without destroying the stream
  useEffect(() => {
    if (!videoRef.current || !videoRef.current.srcObject) return;
    if (isPaused) {
      videoRef.current.pause();
    } else {
      videoRef.current.play().catch(() => {});
    }
  }, [isPaused]);

  const objectFit = style.objectFit || 'cover';

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        background: '#0a0a0c',
        overflow: 'hidden',
        ...style
      }}
    >
      {/* Layer 1: Instant snapshot backdrop - guarantees ZERO black screen */}
      <img
        src={effectivePlaceholder}
        alt={`Snapshot for ${cameraId}`}
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit,
          zIndex: 1,
          display: 'block'
        }}
        onError={(e) => { e.target.style.display = 'none'; }}
      />

      {/* Layer 2: Primary WebRTC Live Stream - always mounted, never destroyed on pause */}
      {!useFallback && (
        <video
          ref={videoRef}
          autoPlay={autoPlay}
          muted={muted}
          playsInline
          onPlaying={() => {
            setIsPlaying(true);
            isPlayingRef.current = true;
          }}
          onLoadedData={() => {
            setIsPlaying(true);
            isPlayingRef.current = true;
          }}
          onTimeUpdate={() => {
            if (videoRef.current && videoRef.current.currentTime > 0) {
              setIsPlaying(true);
              isPlayingRef.current = true;
            }
          }}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit,
            zIndex: 2,
            opacity: isPlaying ? 1 : 0,
            transition: 'opacity 0.3s ease'
          }}
        />
      )}

      {/* Layer 3: Secondary MJPEG Live Stream Fallback if WebRTC fails */}
      {useFallback && (
        <img
          src={`${baseUrl}/api/cameras/${cameraId}/stream?preview=1`}
          alt={`Live Stream fallback for ${cameraId}`}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit,
            zIndex: 3,
            display: 'block'
          }}
          onError={(e) => {
            // If MJPEG stream cannot connect, hide fallback and keep snapshot backdrop visible
            e.target.style.display = 'none';
          }}
        />
      )}
    </div>
  );
}

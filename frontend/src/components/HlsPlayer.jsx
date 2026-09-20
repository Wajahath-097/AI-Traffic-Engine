import React, { useEffect, useRef, useState } from 'react';

/**
 * Direct HLS Player that bypasses the backend and streams directly from cctv.corp8.cloud.
 * Uses hls.js dynamically loaded from CDN for cross-browser support on Windows.
 */
export default function HlsPlayer({ cameraId, style = {}, placeholderSrc, autoPlay = true, muted = true }) {
  const videoRef = useRef(null);
  const [status, setStatus] = useState('connecting');

  useEffect(() => {
    let cancelled = false;
    let hls = null;
    const video = videoRef.current;
    if (!video) return;

    setStatus('connecting');
    const hlsUrl = `https://cctv.corp8.cloud/${cameraId.toLowerCase()}/index.m3u8`;

    const initializePlayer = () => {
      if (cancelled) return;

      if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (Safari)
        video.src = hlsUrl;
        video.addEventListener('loadedmetadata', () => {
          if (!cancelled && autoPlay) video.play().catch(e => console.log('Autoplay prevented:', e));
        });
      } else if (window.Hls) {
        if (!window.Hls.isSupported()) {
          setStatus('error');
          return;
        }

        hls = new window.Hls({
          maxBufferLength: 10,
          maxMaxBufferLength: 20,
          liveSyncDuration: 3,
          liveMaxLatencyDuration: 10,
          enableWorker: true
        });

        hls.loadSource(hlsUrl);
        hls.attachMedia(video);

        hls.on(window.Hls.Events.MANIFEST_PARSED, () => {
          if (!cancelled && autoPlay) video.play().catch(e => console.log('Autoplay prevented:', e));
        });

        hls.on(window.Hls.Events.ERROR, (event, data) => {
          if (data.fatal) {
            switch (data.type) {
              case window.Hls.ErrorTypes.NETWORK_ERROR:
                console.log('Fatal network error encountered, trying to recover...');
                hls.startLoad();
                break;
              case window.Hls.ErrorTypes.MEDIA_ERROR:
                console.log('Fatal media error encountered, trying to recover...');
                hls.recoverMediaError();
                break;
              default:
                console.error('Fatal HLS error', data);
                hls.destroy();
                if (!cancelled) setStatus('error');
                break;
            }
          }
        });
      }
    };

    if (window.Hls !== undefined || video.canPlayType('application/vnd.apple.mpegurl')) {
      initializePlayer();
    } else {
      // Load hls.js dynamically
      const scriptId = 'hls-js-script';
      let script = document.getElementById(scriptId);

      if (!script) {
        script = document.createElement('script');
        script.id = scriptId;
        script.src = 'https://cdn.jsdelivr.net/npm/hls.js@1';
        script.async = true;
        document.head.appendChild(script);
      }

      script.addEventListener('load', initializePlayer);
    }

    return () => {
      cancelled = true;
      if (hls) {
        hls.destroy();
      }
      if (video) {
        video.removeAttribute('src');
        video.load();
      }
    };
  }, [cameraId, autoPlay]);

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
          <div style={{ color: '#888', fontSize: '12px' }}>Stream unavailable</div>
        </div>
      )}
      
      {status === 'connecting' && !placeholderSrc && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', zIndex: 10, gap: '8px' }}>
          <div style={{ color: '#0ea5e9', fontSize: '14px' }}>Loading stream...</div>
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
          objectFit: style.objectFit || 'cover',
          display: status === 'playing' ? 'block' : 'none',
          zIndex: 2,
          position: 'relative'
        }}
      />
    </div>
  );
}

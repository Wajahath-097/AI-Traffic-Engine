import React, { useEffect, useState, useRef } from 'react'
import { apiGet } from '../services/api'
import { AlertTriangle, Play, Pause, ZoomIn, ZoomOut, CheckCircle, XCircle } from 'lucide-react'
import Layout from '../layouts/Layout'

export default function CameraWall() {
  const [cameras, setCameras] = useState(() => {
    try {
      const cached = localStorage.getItem('cached_cameras_list');
      return cached ? JSON.parse(cached) : [];
    } catch (e) {
      return [];
    }
  })
  const [loading, setLoading] = useState(() => {
    return !localStorage.getItem('cached_cameras_list');
  })
  const [error, setError] = useState('')
  const [selectedCamera, setSelectedCamera] = useState(null)
  const [liveDetections, setLiveDetections] = useState([])
  const [isPlaying, setIsPlaying] = useState(true)
  const [zoomLevel, setZoomLevel] = useState(1)
  const [gridKey, setGridKey] = useState(Date.now())
  const [modalStreamKey, setModalStreamKey] = useState(Date.now())
  const [isFullscreen, setIsFullscreen] = useState(false)
  const videoContainerRef = useRef(null)

  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const toggleFullscreen = () => {
    const elem = videoContainerRef.current;
    if (!elem) return;

    const isCurrentFull = !!(
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.mozFullScreenElement ||
      document.msFullscreenElement
    );

    if (!isCurrentFull && !isFullscreen) {
      if (elem.requestFullscreen) {
        elem.requestFullscreen().catch((err) => {
          console.warn("Fullscreen request error, falling back to CSS:", err);
          setIsFullscreen(true);
        });
      } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
      } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
      } else {
        setIsFullscreen(true);
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      const isFull = !!(
        document.fullscreenElement ||
        document.webkitFullscreenElement ||
        document.mozFullScreenElement ||
        document.msFullscreenElement
      );
      setIsFullscreen(isFull);
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        const isFull = !!(
          document.fullscreenElement ||
          document.webkitFullscreenElement ||
          document.mozFullScreenElement ||
          document.msFullscreenElement
        );
        if (isFull) {
          if (document.exitFullscreen) {
            document.exitFullscreen().catch(() => {});
          } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
          }
        }
        setIsFullscreen(false);
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
      document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    if (!selectedCamera && isFullscreen) {
      if (document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
      setIsFullscreen(false);
    }
  }, [selectedCamera, isFullscreen]);

  const fetchCameras = async () => {
    try {
      const response = await apiGet('/api/cameras/')
      if (response.data && response.data.length > 0) {
        setCameras(response.data)
        setError('')
        localStorage.setItem('cached_cameras_list', JSON.stringify(response.data))
      }
    } catch (err) {
      console.error("Failed to load cameras:", err)
      const cached = localStorage.getItem('cached_cameras_list')
      if (!cached) {
        setError(err?.response?.data?.detail || 'Unable to load cameras.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCameras()
    const intervalId = setInterval(fetchCameras, 45000);
    return () => clearInterval(intervalId);
  }, [])

  // Poll real live detections when modal is open
  useEffect(() => {
    let interval;
    if (selectedCamera) {
      setModalStreamKey(Date.now());
      setIsPlaying(true);
      setZoomLevel(1);

      const fetchDetections = async () => {
        try {
          const res = await apiGet(`/api/cameras/${selectedCamera.camera_id}/live-detections`);
          setLiveDetections(res.data || []);
        } catch(e) {
          console.error("Failed to fetch live detections");
        }
      };
      
      fetchDetections();
      interval = setInterval(fetchDetections, 2000);
    } else {
      setLiveDetections([]);
    }
    return () => clearInterval(interval);
  }, [selectedCamera])

  function CameraGridCard({ camera, onSelect, baseUrl }) {
    return (
      <div
        className="camera-card card"
        onClick={() => onSelect(camera)}
        style={{ cursor: 'pointer', transition: 'transform 0.2s', position: 'relative' }}
      >
        <div className="camera-visual" style={{ position: 'relative', background: '#0a0a0c', borderRadius: '4px 4px 0 0', overflow: 'hidden', height: '240px' }}>
          {camera.status === 'offline' ? (
            <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff', fontSize: '18px', fontWeight: 'bold' }}>
              UNABLE TO STREAM
            </div>
          ) : (
            <img 
              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              src={`${baseUrl}/api/cameras/${camera.camera_id}/snapshot`}
              alt={`Snapshot for ${camera.camera_id}`}
              loading="lazy"
              onError={(e) => {
                const fallback = e.target.parentElement?.querySelector('.snapshot-fallback');
                if (fallback) fallback.style.display = 'flex';
              }}
            />
          )}

          <div className="snapshot-fallback" style={{ display: 'none', position: 'absolute', inset: 0, alignItems: 'center', justifyContent: 'center', color: '#0ea5e9', fontSize: '14px', fontStyle: 'italic', background: '#111' }}>
            Connecting to feed...
          </div>

          <div style={{ position: 'absolute', top: '12px', left: '12px', color: 'white', textShadow: '1px 1px 3px black', fontWeight: '600', zIndex: 20 }}>
            {camera.camera_id}
          </div>
          <span id={`badge-${camera.camera_id}`} className={`status-badge ${camera.status}`} style={{ position: 'absolute', top: '12px', right: '12px', zIndex: 20 }}>
            {camera.status}
          </span>
        </div>
        <div className="camera-info" style={{ padding: '16px 0 0' }}>
          <h3>{camera.name}</h3>
          <p>{camera.location || 'Unknown location'}</p>
          <small>{camera.protocol.toUpperCase()} • {camera.enabled ? 'Enabled' : 'Disabled'}</small>
        </div>
      </div>
    );
  }

  if (loading && cameras.length === 0) return <div className="loading">Loading camera network...</div>

  if (error && cameras.length === 0) {
    return (
      <div className="camera-wall">
        <div className="page-header">
          <div>
            <p className="eyebrow">Coverage</p>
            <h1>Camera Network</h1>
          </div>
        </div>
        <div className="alert alert-danger" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px' }}>
          <span>{error}</span>
          <button 
            onClick={() => { setLoading(true); setError(''); fetchCameras(); }}
            style={{ background: '#2563eb', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 18px', cursor: 'pointer', fontWeight: 'bold' }}
          >
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="camera-wall">
      <div className="page-header">
        <div>
          <p className="eyebrow">Coverage</p>
          <h1>Camera Network</h1>
        </div>
      </div>

      <div className="grid grid-2">
        {cameras.map((camera) => (
          <CameraGridCard
            key={camera.id}
            camera={camera}
            onSelect={setSelectedCamera}
            baseUrl={baseUrl}
          />
        ))}
      </div>

      {selectedCamera && (
        <div className="modal-overlay" onClick={() => setSelectedCamera(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ background: 'var(--color-surface)', width: '100%', maxWidth: '1400px', borderRadius: '12px', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '82vh' }}>
            <div className="modal-header" style={{ padding: '18px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
              <div>
                <h2 style={{ display: 'inline-block', marginRight: '16px', color: 'var(--color-text)', margin: 0 }}>{selectedCamera.name}</h2>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '14px' }}>({selectedCamera.camera_id})</span>
              </div>
              <button onClick={() => setSelectedCamera(null)} style={{ background: 'transparent', border: 'none', fontSize: '28px', color: 'var(--color-text)', cursor: 'pointer' }}>&times;</button>
            </div>
            
            <div className="modal-body" style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
              {/* Video Player */}
              <div 
                ref={videoContainerRef}
                style={{ 
                  flex: '1', 
                  background: '#000', 
                  position: isFullscreen ? 'fixed' : 'relative',
                  inset: isFullscreen ? 0 : 'auto',
                  width: isFullscreen ? '100vw' : '100%',
                  height: isFullscreen ? '100vh' : '100%',
                  zIndex: isFullscreen ? 99999 : 1,
                  overflow: 'hidden', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center' 
                }}
              >
                {selectedCamera.status === 'offline' ? (
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#555', fontSize: '24px' }}>
                    OFFLINE - NO SIGNAL
                  </div>
                ) : (
                  <>
                    <img 
                      key={`${selectedCamera.camera_id}-${modalStreamKey}`}
                      src={isPlaying 
                        ? `${baseUrl}/api/cameras/${selectedCamera.camera_id}/stream?_t=${modalStreamKey}`
                        : `${baseUrl}/api/cameras/${selectedCamera.camera_id}/snapshot?c=1`
                      }
                      alt={`Live Stream for ${selectedCamera.camera_id}`}
                      style={{ 
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        transform: `scale(${zoomLevel})`,
                        transition: 'transform 0.25s ease',
                        display: 'block'
                      }}
                      onError={(e) => {
                        // Fallback gracefully to snapshot if stream reconnects
                        e.target.src = `${baseUrl}/api/cameras/${selectedCamera.camera_id}/snapshot?fallback=1`;
                      }}
                    />

                    {/* Controls Overlay */}
                    <div style={{ position: 'absolute', bottom: '20px', left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: '20px', alignItems: 'center', background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(6px)', padding: '10px 24px', borderRadius: '30px', zIndex: 10, border: '1px solid rgba(255,255,255,0.15)' }}>
                      <button 
                        onClick={() => { 
                          if (!isPlaying) setModalStreamKey(Date.now());
                          setIsPlaying(!isPlaying); 
                        }} 
                        style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                        title={isPlaying ? "Pause" : "Play"}
                      >
                        {isPlaying ? (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
                        ) : (
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                        )}
                      </button>
                      <div style={{ width: '1px', height: '22px', background: 'rgba(255,255,255,0.2)' }}></div>
                      <button onClick={() => setZoomLevel(z => Math.max(1, z - 0.25))} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '18px', fontWeight: 'bold' }} title="Zoom Out">-</button>
                      <span style={{ color: '#fff', display: 'flex', alignItems: 'center', fontSize: '13px', minWidth: '40px', justifyContent: 'center' }}>{Math.round(zoomLevel * 100)}%</span>
                      <button onClick={() => setZoomLevel(z => Math.min(3, z + 0.25))} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '18px', fontWeight: 'bold' }} title="Zoom In">+</button>
                    </div>

                    {/* Fullscreen Button on Bottom Right */}
                    <button 
                      id="camera-fullscreen-btn"
                      className="camera-fullscreen-btn"
                      onClick={toggleFullscreen}
                      title={isFullscreen ? "Exit Fullscreen (Esc)" : "Fullscreen"}
                      aria-label={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                    >
                      {isFullscreen ? (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
                        </svg>
                      ) : (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M15 3h6v6" />
                          <path d="M9 21H3v-6" />
                          <path d="M21 3l-7 7" />
                          <path d="M3 21l7-7" />
                        </svg>
                      )}
                    </button>
                  </>
                )}
              </div>
              
              {/* Live Detections Sidebar */}
              <div style={{ width: '350px', background: 'var(--color-surface)', borderLeft: '1px solid var(--color-border)', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '16px', borderBottom: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
                  <h3 style={{ margin: 0, fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ display: 'inline-block', width: '8px', height: '8px', background: '#ef4444', borderRadius: '50%', animation: 'pulse 2s infinite' }}></span>
                    Vehicles Detected
                  </h3>
                </div>
                <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {liveDetections.length === 0 ? (
                    <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', marginTop: '40px' }}>Waiting for vehicles...</div>
                  ) : (
                    liveDetections.map((det) => (
                      <div key={det.id} style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: '8px', padding: '12px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                        <div>
                          <div style={{ fontWeight: '600', textTransform: 'capitalize', fontSize: '15px' }}>
                            {det.vehicle_color || ''} {det.vehicle_class || 'Vehicle'}
                          </div>
                          <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                            {new Date(det.detected_at).toLocaleTimeString()}
                          </div>
                        </div>
                        {det.plate_number && (
                          <div style={{ background: '#facc15', color: '#000', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold', fontSize: '13px', border: '1px solid #eab308' }}>
                            {det.plate_number}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

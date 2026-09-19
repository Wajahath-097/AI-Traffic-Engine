import React, { useEffect, useState, useRef } from 'react'
import { apiGet } from '../services/api'

export default function CameraWall() {
  const [cameras, setCameras] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCamera, setSelectedCamera] = useState(null)
  const [liveDetections, setLiveDetections] = useState([])
  const [isPlaying, setIsPlaying] = useState(true)
  const [zoomLevel, setZoomLevel] = useState(1)
  const [videoTime, setVideoTime] = useState(0)
  const videoRef = useRef(null)

  const getVideoSrc = (camera) => {
    if (camera.status === 'offline') return null;
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return `${baseUrl}/api/cameras/${camera.camera_id}/stream`;
  };

  const getSnapshotSrc = (camera) => {
    if (camera.status === 'offline') return null;
    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return `${baseUrl}/api/cameras/${camera.camera_id}/snapshot`;
  };

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const response = await apiGet('/api/cameras/')
        setCameras(response.data || [])
      } catch (err) {
        setError(err?.response?.data?.detail || 'Unable to load cameras.')
      } finally {
        setLoading(false)
      }
    }

    fetchCameras()
  }, [])

  useEffect(() => {
    let interval;
    if (selectedCamera) {
      // Poll real live detections
      const fetchDetections = async () => {
        try {
          const res = await apiGet(`/api/cameras/${selectedCamera.camera_id}/live-detections`);
          setLiveDetections(res.data || []);
        } catch(e) {
          console.error("Failed to fetch live detections");
        }
      };
      
      fetchDetections();
      interval = setInterval(fetchDetections, 1500);
      
    } else {
      setLiveDetections([]);
    }
    return () => clearInterval(interval);
  }, [selectedCamera])

  if (loading) return <div className="loading">Loading camera network...</div>
  if (error) return <div className="alert alert-danger">{error}</div>

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
          <div key={camera.id} className="camera-card card" onClick={() => setSelectedCamera(camera)} style={{ cursor: 'pointer', transition: 'transform 0.2s' }}>
            <div className="camera-visual" style={{ position: 'relative', background: '#000', borderRadius: '4px 4px 0 0', overflow: 'hidden', height: '240px' }}>
              {getSnapshotSrc(camera) ? (
                <img 
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  src={getSnapshotSrc(camera)}
                  alt={`Stream for ${camera.camera_id}`}
                />
              ) : (
                <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ffffff', fontSize: '18px', fontWeight: 'bold' }}>
                  NO SIGNAL
                </div>
              )}
              <div style={{ position: 'absolute', top: '12px', left: '12px', color: 'white', textShadow: '1px 1px 2px black', fontWeight: '600' }}>
                {camera.camera_id}
              </div>
              <span className={`status-badge ${camera.status}`} style={{ position: 'absolute', top: '12px', right: '12px' }}>
                {camera.status}
              </span>
            </div>
            <div className="camera-info" style={{ padding: '16px 0 0' }}>
              <h3>{camera.name}</h3>
              <p>{camera.location || 'Unknown location'}</p>
              <small>{camera.protocol.toUpperCase()} • {camera.enabled ? 'Enabled' : 'Disabled'}</small>
            </div>
          </div>
        ))}
      </div>

      {selectedCamera && (
        <div className="modal-overlay" onClick={() => setSelectedCamera(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ background: 'var(--color-surface)', width: '100%', maxWidth: '1400px', borderRadius: '12px', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '80vh' }}>
            <div className="modal-header" style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
              <div>
                <h2 style={{ display: 'inline-block', marginRight: '16px', color: 'var(--color-text)', margin: 0 }}>{selectedCamera.name}</h2>
              </div>
              <button onClick={() => setSelectedCamera(null)} style={{ background: 'transparent', border: 'none', fontSize: '28px', color: 'var(--color-text)', cursor: 'pointer' }}>&times;</button>
            </div>
            
            <div className="modal-body" style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
              {/* Video Player */}
              <div style={{ flex: '1', background: '#000', position: 'relative', overflow: 'hidden' }}>
                {getVideoSrc(selectedCamera) ? (
                  <>
                    <img 
                      src={isPlaying ? `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/cameras/${selectedCamera.camera_id}/stream` : getSnapshotSrc(selectedCamera)}
                      style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'contain', 
                        transform: `scale(${zoomLevel})`,
                        transition: 'transform 0.3s ease',
                        opacity: isPlaying ? 1 : 0.7
                      }}
                      alt="Live Stream"
                    />
                    
                    {/* Controls Overlay */}
                    <div style={{ position: 'absolute', bottom: '20px', left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: '20px', alignItems: 'center', background: 'rgba(0,0,0,0.7)', padding: '10px 24px', borderRadius: '30px', zIndex: 10 }}>
                      <button onClick={() => setIsPlaying(!isPlaying)} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                        {isPlaying ? (
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
                        ) : (
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                        )}
                      </button>
                      <div style={{ width: '1px', height: '24px', background: 'rgba(255,255,255,0.2)' }}></div>
                      <button onClick={() => setZoomLevel(z => Math.max(1, z - 0.25))} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '20px', fontWeight: 'bold' }}>-</button>
                      <span style={{ color: '#fff', display: 'flex', alignItems: 'center', fontSize: '14px', minWidth: '40px', justifyContent: 'center' }}>{Math.round(zoomLevel * 100)}%</span>
                      <button onClick={() => setZoomLevel(z => Math.min(3, z + 0.25))} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '20px', fontWeight: 'bold' }}>+</button>
                    </div>
                  </>
                ) : (
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#555', fontSize: '24px' }}>
                    OFFLINE - NO SIGNAL
                  </div>
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

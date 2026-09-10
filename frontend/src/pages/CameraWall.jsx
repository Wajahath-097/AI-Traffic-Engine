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
    if (camera.camera_id === 'CAM-001') return `${baseUrl}/api/media/offline_videos/13020032_3840_2160_30fps.mp4?v=1`;
    if (camera.camera_id === 'CAM-002') return `${baseUrl}/api/media/offline_videos/13105476_3840_2160_30fps.mp4?v=1`;
    return `${baseUrl}/api/media/offline_videos/14985169_1920_1080_25fps.mp4?v=1`;
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
              {getVideoSrc(camera) ? (
                <video 
                  autoPlay 
                  muted 
                  playsInline
                  preload="auto"
                  crossOrigin="anonymous"
                  onEnded={(e) => {
                    e.target.currentTime = 0;
                    e.target.play().catch(() => {});
                  }}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', pointerEvents: 'none' }}
                  src={getVideoSrc(camera)}
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
                <h2 style={{ display: 'inline-block', marginRight: '16px', color: 'var(--color-text)', margin: 0 }}>{selectedCamera.name} ({selectedCamera.camera_id})</h2>
                <span className="badge badge-primary" style={{ background: '#e63946', color: 'white' }}>LIVE OCR ACTIVE</span>
              </div>
              <button onClick={() => setSelectedCamera(null)} style={{ background: 'transparent', border: 'none', fontSize: '28px', color: 'var(--color-text)', cursor: 'pointer' }}>&times;</button>
            </div>
            
            <div className="modal-body" style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
              {/* Video Player */}
              <div style={{ flex: '1 1 70%', background: '#000', position: 'relative', overflow: 'hidden' }}>
                {getVideoSrc(selectedCamera) ? (
                  <>
                    <img 
                      src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/cameras/${selectedCamera.camera_id}/stream`}
                      style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'contain', 
                        transform: `scale(${zoomLevel})`,
                        transition: 'transform 0.3s ease'
                      }}
                      alt="Live Stream"
                    />
                    
                    {/* Camera Recording Overlay */}
                    <div style={{ position: 'absolute', top: '20px', right: '20px', display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(0,0,0,0.6)', padding: '6px 12px', borderRadius: '4px', zIndex: 10 }}>
                      <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ff0000', animation: 'pulse 1.5s infinite' }}></div>
                      <span style={{ color: '#fff', fontFamily: 'monospace', fontSize: '14px', letterSpacing: '1px' }}>
                        LIVE AI STREAM
                      </span>
                    </div>

                    {/* Controls Overlay */}
                    <div style={{ position: 'absolute', bottom: '20px', left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: '16px', background: 'rgba(0,0,0,0.7)', padding: '10px 24px', borderRadius: '30px', zIndex: 10 }}>
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

              {/* Live Metadata Sidebar */}
              <div style={{ flex: '1 1 30%', minWidth: '320px', background: 'var(--color-surface-hover)', borderLeft: '1px solid var(--color-border)', overflowY: 'auto', padding: '16px' }}>
                <h3 style={{ margin: '0 0 16px 0', fontSize: '15px', color: 'var(--color-text)', borderBottom: '1px solid var(--color-border)', paddingBottom: '8px' }}>
                  Live Recognition Feed
                </h3>
                
                {liveDetections.length === 0 ? (
                  <div style={{ color: 'var(--color-text-light)', fontSize: '14px', textAlign: 'center', marginTop: '40px' }}>Waiting for vehicles...</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {liveDetections.map((det, i) => (
                      <div key={det.id || i} style={{ background: 'var(--color-bg)', padding: '12px', borderRadius: '8px', borderLeft: '4px solid #00f2fe', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                          <span style={{ fontWeight: 'bold', fontSize: '16px', color: 'var(--color-text)', letterSpacing: '1px' }}>
                            {det.plate_number || 'UNKNOWN'}
                          </span>
                          <span style={{ fontSize: '12px', color: 'var(--color-text-light)' }}>
                            {det.detected_at ? new Date(det.detected_at).toLocaleTimeString() : new Date().toLocaleTimeString()}
                          </span>
                        </div>
                        
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          <span style={{ background: 'rgba(0,242,254,0.15)', padding: '4px 10px', borderRadius: '4px', fontSize: '12px', color: '#00f2fe', border: '1px solid rgba(0,242,254,0.3)', fontWeight: '600' }}>
                            {det.vehicle_class ? det.vehicle_class.toUpperCase() : 'VEHICLE'}
                          </span>
                          <span style={{ background: 'rgba(255,255,255,0.08)', padding: '4px 10px', borderRadius: '4px', fontSize: '12px', color: 'var(--color-text)', border: '1px solid var(--color-border)' }}>
                            {det.vehicle_color ? det.vehicle_color.toUpperCase() : 'UNKNOWN COLOR'}
                          </span>
                          <span style={{ 
                              padding: '4px 10px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold',
                              background: det.verification_status === 'VERIFIED' ? 'rgba(0,255,0,0.15)' : det.verification_status === 'MISMATCH' ? 'rgba(255,0,0,0.15)' : 'rgba(255,255,255,0.1)',
                              color: det.verification_status === 'VERIFIED' ? '#00ff00' : det.verification_status === 'MISMATCH' ? '#ff4444' : '#aaaaaa',
                              border: `1px solid ${det.verification_status === 'VERIFIED' ? '#00ff00' : det.verification_status === 'MISMATCH' ? '#ff4444' : '#555'}`
                          }}>
                            {det.verification_status || 'UNVERIFIED'}
                          </span>
                        </div>
                        
                        <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--color-text-light)', display: 'flex', justifyContent: 'space-between' }}>
                          <span>Conf: {det.confidence}%</span>
                          {det.evidence_url && <span style={{color: '#00f2fe'}} title={det.evidence_url}>Cloud Saved ☁️</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

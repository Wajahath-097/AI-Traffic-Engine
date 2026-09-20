import React, { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { apiGet } from '../services/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, BarChart, Bar } from 'recharts'
import { Activity, Camera, AlertTriangle, Cloud, Server, Zap, ChevronRight, Car, Info, XCircle, Map as MapIcon } from 'lucide-react'
import { GoogleMap, TrafficLayer, HeatmapLayer, useJsApiLoader } from '@react-google-maps/api'
import skylineImg from '../assets/skyline.jpg'
import './Dashboard.css'

const libraries = ['visualization'];

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [rawHeatmap, setRawHeatmap] = useState([])
  const [onlineCameras, setOnlineCameras] = useState(() => {
    return parseInt(localStorage.getItem('cached_online_cameras') || '0', 10);
  })
  const [totalCameras, setTotalCameras] = useState(() => {
    return parseInt(localStorage.getItem('cached_total_cameras') || '0', 10);
  })
  const [ocrStats, setOcrStats] = useState(null)
  const [detectionStats, setDetectionStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [recentAlerts, setRecentAlerts] = useState([])

  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: "AIzaSyA6OMTdf0GLlzaZUE7S_LnpVdRVOfb3nMw",
    version: "3.64",
    libraries: libraries,
    language: "en",
    region: "US"
  })

  useEffect(() => {
    let isMounted = true;
    let intervalId = null;
    const fetchDashboard = async () => {
      try {
        const [dashRes, heatRes, camRes, ocrRes, detRes, alertsRes] = await Promise.all([
          apiGet('/api/analytics/dashboard').catch(() => ({ data: {} })),
          apiGet('/api/analytics/heatmap').catch(() => ({ data: [] })),
          apiGet('/api/cameras/').catch(() => ({ data: [] })),
          apiGet('/api/analytics/ocr-accuracy').catch(() => null),
          apiGet('/api/analytics/detections').catch(() => null),
          apiGet('/api/alerts/?status_filter=open&limit=5').catch(() => ({ data: [] }))
        ]);

        if (isMounted) {
          setData(dashRes.data);

          if (Array.isArray(heatRes.data)) {
            setRawHeatmap(heatRes.data);
          }

          if (dashRes.data?.total_cameras !== undefined) {
            const tot = Number(dashRes.data.total_cameras) || 0;
            const onl = Number(dashRes.data.online_cameras) || 0;
            setTotalCameras(tot);
            setOnlineCameras(onl);
            localStorage.setItem('cached_total_cameras', String(tot));
            localStorage.setItem('cached_online_cameras', String(onl));
          } else if (Array.isArray(camRes?.data) && camRes.data.length > 0) {
            const onlineCount = camRes.data.filter(c => c.status === 'online').length;
            setOnlineCameras(onlineCount);
            setTotalCameras(camRes.data.length);
            localStorage.setItem('cached_online_cameras', String(onlineCount));
            localStorage.setItem('cached_total_cameras', String(camRes.data.length));
          }

          if (ocrRes?.data) setOcrStats(ocrRes.data);
          if (detRes?.data) setDetectionStats(detRes.data);
          if (Array.isArray(alertsRes?.data)) setRecentAlerts(alertsRes.data);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load dashboard:', err)
          setError('Unable to load dashboard data.')
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    fetchDashboard()
    // Poll every 15 seconds for continuous live updates (avoids DB connection limit)
    intervalId = setInterval(fetchDashboard, 15000);

    return () => {
      isMounted = false;
      if (intervalId) clearInterval(intervalId);
    }
  }, [])

  const heatmapData = useMemo(() => {
    if (!isLoaded) return [];
    return rawHeatmap.map(pt => ({
      lat: pt.lat || pt.latitude,
      lng: pt.lng || pt.longitude,
      weight: Math.max(pt.intensity || pt.weight || 1, 1)
    }))
  }, [isLoaded, rawHeatmap])

  const defaultCenter = useMemo(() => ({ lat: 17.3850, lng: 78.4867 }), [])

  if (loading) return <div className="loading">Loading dashboard...</div>
  if (error) return <div className="alert alert-danger">{error}</div>

  const totalDetections = data?.total_5m ?? 0
  const openAlerts = data?.alert_summary?.by_status?.open ?? 0
  const activeCameras = onlineCameras

  const vehicleClassData = detectionStats && detectionStats.vehicle_classes ? [
    { name: 'Two Wheelers', value: detectionStats.vehicle_classes.bike ?? 0 },
    { name: 'Cars', value: detectionStats.vehicle_classes.car ?? 0 },
    { name: 'Auto Rickshaws', value: detectionStats.vehicle_classes.other ?? 0 },
    { name: 'Buses/Trucks', value: detectionStats.vehicle_classes.truck ?? 0 }
  ] : [
    { name: 'Two Wheelers', value: 0 },
    { name: 'Cars', value: 0 },
    { name: 'Auto Rickshaws', value: 0 },
    { name: 'Buses/Trucks', value: 0 }
  ];
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']



  return (
    <div className="dashboard-v2">
      <div className="hero-banner" style={{ backgroundImage: `url(${skylineImg})` }}>
        <div className="hero-content">
          <h1>Good Afternoon, Admin</h1>
          <p>Here's what's happening on the roads today.</p>
        </div>
      </div>

      <div className="dashboard-main-content">
        <div className="center-panels">
          {/* Stats Cards Row */}
          <div className="stats-grid">
            <Link to="/cameras" className="stat-card glass-panel" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="stat-icon-wrapper purple"><Camera size={22} /></div>
              <div className="stat-info">
                <p>Total Cameras</p>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>{totalCameras} <span style={{ fontSize: '10px', color: '#10b981', fontWeight: '600' }}>● Online: {activeCameras}</span> <span style={{ fontSize: '10px', color: '#ef4444', fontWeight: '600' }}>● Offline: {totalCameras - activeCameras}</span></h3>
              </div>
            </Link>
            <div className="stat-card glass-panel">
              <div className="stat-icon-wrapper green"><Car size={22} /></div>
              <div className="stat-info">
                <p>Active Vehicles (Today)</p>
                <h3>{data?.total_24h?.toLocaleString() ?? 0}</h3>
              </div>
              <div style={{ marginLeft: 'auto', color: '#10b981', fontSize: '12px', fontWeight: '700' }}>↑ Live</div>
            </div>
            <Link to="/analytics" className="stat-card glass-panel" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="stat-icon-wrapper blue"><Activity size={22} /></div>
              <div className="stat-info">
                <p>ANPR Matches</p>
                <h3>{detectionStats?.with_plates?.toLocaleString() ?? 0}</h3>
              </div>
              <div style={{ marginLeft: 'auto', color: '#10b981', fontSize: '12px', fontWeight: '700' }}>↑ Live</div>
            </Link>
            <Link to="/alerts" className="stat-card glass-panel" style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="stat-icon-wrapper red"><AlertTriangle size={22} /></div>
              <div className="stat-info">
                <p>Active Alerts</p>
                <h3>{openAlerts}</h3>
              </div>
              <div style={{ marginLeft: 'auto', color: '#ef4444', fontSize: '12px', fontWeight: '700' }}>↑ 75%</div>
            </Link>
          </div>

          {/* Map - fills rest of left column */}
          <div className="map-panel glass-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', borderBottom: '1px solid #e2e8f0', background: 'white', zIndex: 10 }}>
              <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '700', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MapIcon size={18} /> Live Traffic Map – Hyderabad
              </h3>
              <div style={{ display: 'flex', gap: '16px', fontSize: '12px', fontWeight: '600', color: '#64748b' }}>
                <span style={{ color: '#10b981' }}>● Live Traffic</span>
                <span style={{ color: '#3b82f6' }}>● Cameras</span>
              </div>
            </div>
            <div style={{ flex: 1, position: 'relative' }}>
              {isLoaded && window.google ? (
                <GoogleMap
                  mapContainerStyle={{ width: '100%', height: '100%' }}
                  center={{ lat: 23.2156, lng: 72.6369 }}
                  zoom={12}
                  options={{
                    disableDefaultUI: true,
                    zoomControl: true,
                  }}
                >
                  <TrafficLayer />
                  {heatmapData.length > 0 && (
                    <HeatmapLayer
                      data={heatmapData.map(pt => ({
                        location: new window.google.maps.LatLng(parseFloat(pt.lat), parseFloat(pt.lng)),
                        weight: pt.weight
                      }))}
                      options={{ radius: 30, opacity: 0.75, maxIntensity: 10 }}
                    />
                  )}
                </GoogleMap>
              ) : (
                <div style={{ padding: '20px' }}>Loading Map...</div>
              )}
            </div>
          </div>
        </div>

        <div className="right-panels">
          <div className="chart-panel glass-panel">
            <h3>Traffic Volume (Last 24 Hours)</h3>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.detections_by_hour || []}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="hour" tickFormatter={(val) => val.split(' ')[1]} stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <RechartsTooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                  <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel glass-panel">
            <h3>Vehicle Breakdown (Today)</h3>
            <div style={{ display: 'flex', height: '140px', alignItems: 'center' }}>
              <div style={{ flex: 1, height: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={vehicleClassData}
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {vehicleClassData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '11px', fontWeight: '600', color: '#64748b' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: COLORS[0] }}>● Two Wheelers</span> <span>{detectionStats ? Math.round(((detectionStats.vehicle_classes?.bike || 0) / Math.max(detectionStats.total_detections, 1)) * 100) : 0}%</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: COLORS[1] }}>● Cars</span> <span>{detectionStats ? Math.round(((detectionStats.vehicle_classes?.car || 0) / Math.max(detectionStats.total_detections, 1)) * 100) : 0}%</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: COLORS[2] }}>● Auto Rickshaws</span> <span>{detectionStats ? Math.round(((detectionStats.vehicle_classes?.auto || 0) / Math.max(detectionStats.total_detections, 1)) * 100) : 0}%</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: COLORS[3] }}>● Buses/Trucks</span> <span>{detectionStats ? Math.round(((detectionStats.vehicle_classes?.truck || 0) / Math.max(detectionStats.total_detections, 1)) * 100) : 0}%</span></div>
              </div>
            </div>
          </div>

          <div className="panel glass-panel">
            <h3>Environment &amp; Status</h3>
            <div className="system-status-widget">
              <div className="status-item">
                <Cloud size={18} color="#3b82f6" />
                <strong>Weather 28°C</strong>
                <span>Partly Cloudy</span>
              </div>
              <div className="status-item">
                <Activity size={18} color="#8b5cf6" />
                <strong>Air Quality Good</strong>
                <span>AQI 42</span>
              </div>
              <div className="status-item">
                <Server size={18} color="#10b981" />
                <strong>Network Online</strong>
                <span>All Systems</span>
              </div>
            </div>
          </div>

          <div className="panel glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '180px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ margin: 0 }}>Recent Alerts</h3>
              <a href="/alerts" style={{ fontSize: '11px', color: '#3b82f6', fontWeight: '600' }}>View All</a>
            </div>
            <div className="alerts-list" style={{ overflowY: 'auto', flex: 1 }}>
              {recentAlerts.length === 0 ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#64748b', fontSize: '13px' }}>No active alerts</div>
              ) : (
                recentAlerts.map(alert => (
                  <div key={alert.id} className="alert-item">
                    <div className={`alert-item-icon ${alert.severity === 'critical' ? 'red' : 'info'}`} style={{ color: alert.severity === 'critical' ? '#ef4444' : '#3b82f6' }}>
                      <AlertTriangle size={14} />
                    </div>
                    <div className="alert-item-content">
                      <h4 style={{ textTransform: 'capitalize' }}>{alert.alert_type.replace(/_/g, ' ')}</h4>
                      <p>{alert.message}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

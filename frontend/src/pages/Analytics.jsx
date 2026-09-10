import React, { useState, useEffect } from 'react'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import api, { apiGet } from '../services/api'
import './Analytics.css'

export default function Analytics() {
  const [data, setData] = useState(null)
  const [odPatterns, setOdPatterns] = useState([])
  const [loading, setLoading] = useState(true)



  useEffect(() => {
    async function loadData() {
      try {
        const [dashRes, odRes] = await Promise.all([
          apiGet('/api/analytics/dashboard'),
          api.get('/api/analytics/origin-destination')
        ])
        setData(dashRes.data)
        setOdPatterns(odRes.data.patterns)
      } catch (error) {
        console.error("Failed to load analytics", error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  if (loading) return <div className="loading-state">Loading Analytics...</div>
  if (!data) return <div className="error-state">Failed to load data</div>



  return (
    <div className="analytics-page">
      <div className="page-header">
        <h1>Macro Traffic Flow & Movement Analytics</h1>
        <p>City-wide aggregated patterns and bottleneck visualizations</p>
      </div>

      {data && (
        <div className="analytics-stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '24px' }}>
          <div className="stat-card glass-panel" style={{ padding: '20px', textAlign: 'center' }}>
            <h3 style={{ fontSize: '14px', color: 'var(--color-text-light)', marginBottom: '8px' }}>Detections (24h)</h3>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--color-primary)' }}>{data.total_24h?.toLocaleString() || 0}</div>
          </div>
          <div className="stat-card glass-panel" style={{ padding: '20px', textAlign: 'center' }}>
            <h3 style={{ fontSize: '14px', color: 'var(--color-text-light)', marginBottom: '8px' }}>Detections (7 Days)</h3>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--color-primary)' }}>{data.total_7d?.toLocaleString() || 0}</div>
          </div>
          <div className="stat-card glass-panel" style={{ padding: '20px', textAlign: 'center' }}>
            <h3 style={{ fontSize: '14px', color: 'var(--color-text-light)', marginBottom: '8px' }}>Detections (30 Days)</h3>
            <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--color-primary)' }}>{data.total_30d?.toLocaleString() || 0}</div>
          </div>
        </div>
      )}

      <div className="charts-grid">
        <div className="chart-card wide">
          <h3>24h Traffic Density Trend</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.detections_by_hour} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="hour" tickFormatter={(val) => val.split(' ')[1]} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="count" name="Detections" stroke="#3b82f6" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <h3>Top Origin-Destination Routes</h3>
          <div className="od-list">
            {odPatterns.length > 0 ? odPatterns.slice(0, 5).map((route, i) => (
              <div key={i} className="od-item">
                <div className="od-route">
                  <span className="origin">{route.origin}</span>
                  <span className="arrow">→</span>
                  <span className="dest">{route.destination}</span>
                </div>
                <div className="od-count">{route.count} journeys</div>
              </div>
            )) : <div className="empty-state">No route data available</div>}
          </div>
        </div>

        <div className="chart-card">
          <h3>Top Congestion Bottlenecks</h3>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.top_cameras} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" />
                <YAxis dataKey="camera_name" type="category" width={100} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="detection_count" name="Volume" fill="#ef4444" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>


    </div>
  )
}

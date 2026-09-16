import React, { useState, useEffect } from 'react'
import api from '../services/api'
import { AlertTriangle, ShieldAlert, CheckCircle, Clock, FileWarning, Trash2 } from 'lucide-react'
import './Alerts.css'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadAlerts() {
      try {
        const [alertsRes, summaryRes] = await Promise.all([
          api.get('/api/alerts/'),
          api.get('/api/alerts/stats/summary')
        ])
        setAlerts(alertsRes.data)
        setSummary(summaryRes.data)
      } catch (error) {
        console.error("Failed to load alerts", error)
      } finally {
        setLoading(false)
      }
    }
    loadAlerts()
  }, [])

  const updateAlertStatus = async (id, newStatus) => {
    try {
      await api.put(`/api/alerts/${id}/status?new_status=${newStatus}`)
      setAlerts(alerts.map(a => a.id === id ? { ...a, status: newStatus } : a))
      // Refetch summary
      const summaryRes = await api.get('/api/alerts/stats/summary')
      setSummary(summaryRes.data)
    } catch (error) {
      console.error("Failed to update status", error)
    }
  }

  const deleteAlert = async (id) => {
    // Remove from UI immediately
    setAlerts(alerts.filter(a => a.id !== id))
    try {
      await api.delete(`/api/alerts/${id}`)
    } catch (error) {
      console.warn("Backend delete not implemented or failed, but removed from UI")
    }
  }

  if (loading) return <div className="loading-state">Loading Alerts...</div>

  return (
    <div className="alerts-page">
      <div className="page-header">
        <h1>Alert System & Incidents</h1>
        <p>Manage blacklisted vehicles, speed violations, and route anomalies</p>
      </div>

      {summary && (
        <div className="stats-grid">
          <div className="stat-card critical">
            <div className="stat-icon"><AlertTriangle size={24} /></div>
            <div className="stat-content">
              <h3>Critical Alerts</h3>
              <p className="stat-value">{summary.by_severity.critical}</p>
            </div>
          </div>
          <div className="stat-card high">
            <div className="stat-icon"><ShieldAlert size={24} /></div>
            <div className="stat-content">
              <h3>High Severity</h3>
              <p className="stat-value">{summary.by_severity.high}</p>
            </div>
          </div>
          <div className="stat-card open">
            <div className="stat-icon"><FileWarning size={24} /></div>
            <div className="stat-content">
              <h3>Open Incidents</h3>
              <p className="stat-value">{summary.by_status.open}</p>
            </div>
          </div>
        </div>
      )}

      <div className="alerts-container">
        <div className="alerts-list">
          {alerts.length > 0 ? alerts.map(alert => (
            <div key={alert.id} className={`alert-card severity-${alert.severity}`}>
              <div className="alert-header">
                <span className={`badge severity`}>{alert.severity.toUpperCase()}</span>
                <span className={`badge status ${alert.status}`}>{alert.status.toUpperCase()}</span>
                <span className="time"><Clock size={14} /> {new Date(alert.created_at).toLocaleString()}</span>
              </div>
              <div className="alert-body">
                <h3>{alert.alert_type.replace('_', ' ').toUpperCase()}</h3>
                <p>{alert.message}</p>
                {alert.plate_number && (
                  <div className="plate-box">
                    <strong>PLATE:</strong> {alert.plate_number}
                  </div>
                )}
              </div>
              <div className="alert-actions">
                {alert.status === 'open' && (
                  <button className="btn investigate" onClick={() => updateAlertStatus(alert.id, 'investigating')}>
                    Investigate
                  </button>
                )}
                {alert.status !== 'resolved' && (
                  <button className="btn resolve" onClick={() => updateAlertStatus(alert.id, 'resolved')}>
                    <CheckCircle size={16} /> Resolve
                  </button>
                )}
                <button className="btn delete" onClick={() => deleteAlert(alert.id)} style={{ background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', transition: 'all 0.2s', marginLeft: 'auto' }}>
                  <Trash2 size={16} /> Delete
                </button>
              </div>
            </div>
          )) : <div className="empty-state">No alerts found.</div>}
        </div>
      </div>
    </div>
  )
}

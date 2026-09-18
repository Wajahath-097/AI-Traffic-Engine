import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiGet } from '../services/api';
import './FindVehicle.css';
import { Search, Filter, RefreshCw, Car } from 'lucide-react';

export default function FindVehicle() {
  const [searchParams] = useSearchParams();
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState(searchParams.get('q') || '');

  const fetchVehicles = async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch unique detections (latest per plate)
      const res = await apiGet('/api/detections/with-camera');
      if (res && Array.isArray(res.data)) {
        setVehicles(res.data);
      } else {
        setVehicles([]);
      }
    } catch (err) {
      console.error('Error fetching vehicles:', err);
      setError('Failed to fetch vehicle history.');
      setVehicles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVehicles();
  }, []);

  useEffect(() => {
    const q = searchParams.get('q');
    if (q !== null) {
      setSearchTerm(q);
    }
  }, [searchParams]);

  const filteredVehicles = vehicles.filter(v => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase().replace(/\s+/g, '');
    return (
      (v.plate_number && v.plate_number.toLowerCase().replace(/\s+/g, '').includes(term)) ||
      (v.vehicle_class && v.vehicle_class.toLowerCase().includes(term)) ||
      (v.vehicle_color && v.vehicle_color.toLowerCase().includes(term)) ||
      (v.vehicle_model && v.vehicle_model.toLowerCase().includes(term))
    );
  });

  return (
    <div className="find-vehicle-container">
      <div className="fv-header">
        <h1>
          <Car size={28} className="fv-header-icon" /> 
          Vehicle Detection Log
        </h1>
        <p>Comprehensive history of all detected vehicles across the camera network.</p>
      </div>

      <div className="fv-controls glass-panel">
        <div className="search-bar">
          <Search size={20} className="search-icon" />
          <input 
            type="text" 
            placeholder="Search by plate, color, type..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <button className="btn-refresh" onClick={fetchVehicles} disabled={loading}>
          <RefreshCw size={18} className={loading ? 'spinning' : ''} />
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="fv-error">
          {error}
        </div>
      )}

      <div className="fv-table-container glass-panel">
        <table className="fv-table">
          <thead>
            <tr>
              <th>S.No</th>
              <th>Vehicle Type</th>
              <th>Colour</th>
              <th>Number Plate</th>
              <th>Location</th>
              <th>Time</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {loading && vehicles.length === 0 ? (
              <tr>
                <td colSpan="7" className="fv-empty">Loading vehicles...</td>
              </tr>
            ) : filteredVehicles.length === 0 ? (
              <tr>
                <td colSpan="7" className="fv-empty">No vehicles found.</td>
              </tr>
            ) : (
              filteredVehicles.map((v, index) => (
                <tr key={v.id || index}>
                  <td>{index + 1}</td>
                  <td className="capitalize">{v.vehicle_class || 'Unknown'}</td>
                  <td className="capitalize">{v.vehicle_color || '-'}</td>
                  <td className="plate-cell">
                    {v.plate_number ? (
                      <span className="plate-badge">{v.plate_number}</span>
                    ) : (
                      <span className="no-plate">None</span>
                    )}
                  </td>
                  <td>{v.camera_camera_id ? `${v.camera_camera_id} - ${v.camera_name || 'Unknown'}` : (v.camera_name || 'Unknown')}</td>
                  <td>{new Date(v.detected_at).toLocaleString()}</td>
                  <td>
                    {v.vehicle_confidence ? (
                      <div className="confidence-bar">
                        <div 
                          className="confidence-fill" 
                          style={{ width: `${Math.round(v.vehicle_confidence * 100)}%`, background: v.vehicle_confidence > 0.8 ? '#4ade80' : '#facc15' }}
                        ></div>
                        <span>{Math.round(v.vehicle_confidence * 100)}%</span>
                      </div>
                    ) : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

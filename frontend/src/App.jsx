import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './layouts/Layout'
import Dashboard from './pages/Dashboard'
import CameraWall from './pages/CameraWall'
import TrackVehicle from './pages/TrackVehicle'
import Login from './pages/Login'
import Analytics from './pages/Analytics'
import Alerts from './pages/Alerts'
import LiveMap from './pages/LiveMap'
import Blacklist from './pages/Blacklist'
import FindVehicle from './pages/FindVehicle'

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Dashboard />} />
            <Route path="/cameras" element={<CameraWall />} />
            <Route path="/find-vehicle" element={<FindVehicle />} />
            <Route path="/track" element={<TrackVehicle />} />
          <Route path="/map" element={<LiveMap />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/blacklist" element={<Blacklist />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App

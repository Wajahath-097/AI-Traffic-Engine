import React from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Menu, LogOut, LayoutDashboard, Camera, Search as SearchIcon, BarChart2, AlertTriangle, Map, Shield } from 'lucide-react'
import { logout } from '../services/api'
import logoImg from '../assets/Logo.png'
import './Layout.css'

export default function Layout() {
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const [darkMode, setDarkMode] = React.useState(false)
  const [dropdownOpen, setDropdownOpen] = React.useState(false)

  React.useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
    }
  }, [darkMode])

  // Close dropdown on outside click
  React.useEffect(() => {
    const handleOutsideClick = (e) => {
      if (!e.target.closest('.user-dropdown-container')) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('click', handleOutsideClick)
    return () => document.removeEventListener('click', handleOutsideClick)
  }, [])

  const user = React.useMemo(() => {
    const storedUser = localStorage.getItem('user')
    return storedUser ? JSON.parse(storedUser) : { name: 'Officer' }
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const navLinkClass = ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`

  return (
    <div className="layout" data-sidebar-open={sidebarOpen}>
      <nav className="sidebar" data-open={sidebarOpen}>
        <div className="sidebar-header">
          <img src={logoImg} alt="Traffic Police Logo" className="gov-seal" />
          <h2>Traffic Police Hyderabad</h2>
          <small>Traffic Operations</small>
        </div>

        <ul className="nav-menu">
          <li>
            <NavLink to="/" className={navLinkClass}>
              <LayoutDashboard size={20} />
              <span>Dashboard</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/cameras" className={navLinkClass}>
              <Camera size={20} />
              <span>Cameras</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/map" className={navLinkClass}>
              <Map size={20} />
              <span>Live Map</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/track" className={navLinkClass}>
              <SearchIcon size={20} />
              <span>Track Vehicle</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/analytics" className={navLinkClass}>
              <BarChart2 size={20} />
              <span>Analytics</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/find-vehicle" className={navLinkClass}>
              <SearchIcon size={20} />
              <span>Find Vehicle</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/alerts" className={navLinkClass}>
              <AlertTriangle size={20} />
              <span>Alerts</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/blacklist" className={navLinkClass}>
              <Shield size={20} />
              <span>Blacklist</span>
            </NavLink>
          </li>
        </ul>

        <div className="nav-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </nav>

      <main className="main-content">
        <header className="top-bar">
          <div className="top-bar-left">
            <button
              className="sidebar-toggle"
              onClick={() => setSidebarOpen((open) => !open)}
              aria-label="Toggle sidebar"
            >
              <Menu size={24} />
            </button>
            <div className="breadcrumb">Official Traffic Portal</div>
          </div>
          <div className="user-info" style={{ display: 'flex', alignItems: 'center', gap: '12px', position: 'relative' }}>
            <div className="user-dropdown-container">
              <div 
                className="user-avatar" 
                onClick={() => setDropdownOpen(!dropdownOpen)}
                title="Account Settings"
              >
                {user?.name ? user.name.charAt(0).toUpperCase() : user?.officer_id ? user.officer_id.charAt(0).toUpperCase() : 'A'}
              </div>
              
              {dropdownOpen && (
                <div className="dropdown-menu glass-panel" style={{ position: 'absolute', top: '100%', right: 0, marginTop: '8px', minWidth: '200px', display: 'flex', flexDirection: 'column', gap: '4px', zIndex: 1000 }}>
                  <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--color-border)', marginBottom: '4px' }}>
                    <strong>{user?.name || 'Administrator'}</strong>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-light)' }}>{user?.officer_id || 'ADMIN'}</div>
                  </div>
                  <button 
                    onClick={() => { setDarkMode(!darkMode); setDropdownOpen(false); }} 
                    style={{ textAlign: 'left', padding: '10px 16px', background: 'transparent', color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: '8px' }}
                  >
                    {darkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
                  </button>
                  <button 
                    onClick={handleLogout} 
                    style={{ textAlign: 'left', padding: '10px 16px', background: 'transparent', color: 'var(--color-danger)', display: 'flex', alignItems: 'center', gap: '8px' }}
                  >
                    Log Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <section className="page-content">
          <Outlet />
        </section>
      </main>
    </div>
  )
}

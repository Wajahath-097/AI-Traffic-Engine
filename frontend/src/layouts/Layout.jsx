import React, { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Menu, LogOut, LayoutDashboard, Camera, Search as SearchIcon, BarChart2, AlertTriangle, Map, Shield, Bell } from 'lucide-react'
import { logout } from '../services/api'
import logoImg from '../assets/logo.png'
import headerLogo from '../assets/logo_new.jpg'
import charminarImg from '../assets/hyderabad_traffic_logo.jpg'
import './Layout.css'

export default function Layout() {
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [darkMode, setDarkMode] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const [alerts, setAlerts] = useState([
    {
      id: 1,
      text: <span>Blacklisted vehicle <strong>MH12AB3456</strong> spotted on <strong>CAM-001</strong></span>,
      time: 'Just now'
    },
    {
      id: 2,
      text: <span>Overspeeding detected on <strong>CAM-002</strong> (NH 65)</span>,
      time: '5 minutes ago'
    }
  ])
  const [searchQuery, setSearchQuery] = useState('')

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

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/find-vehicle?q=${encodeURIComponent(searchQuery.replace(/\s+/g, ''))}`);
    }
  }

  const navLinkClass = ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`

  const userRole = React.useMemo(() => {
    try {
      const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
      return storedUser?.role?.name || 'Super Admin';
    } catch {
      return 'Super Admin';
    }
  }, []);

  const hasAccess = (allowedRoles) => {
    if (userRole === 'Super Admin') return true;
    return allowedRoles.includes(userRole);
  };

  return (
    <div className="layout" data-sidebar-open={sidebarOpen}>
      <nav className="sidebar" data-open={sidebarOpen}>
        <div className="sidebar-header">
          <img src={logoImg} alt="Traffic Police Logo" className="gov-seal" />
          <h2>Traffic Police Department</h2>
          <small>Government of Telangana</small>
        </div>

        <ul className="nav-menu">
          <li>
            <NavLink to="/" className={navLinkClass}>
              <LayoutDashboard size={20} />
              <span>Dashboard</span>
            </NavLink>
          </li>
          {hasAccess(['Traffic Officer', 'Control Room']) && (
            <li>
              <NavLink to="/cameras" className={navLinkClass}>
                <Camera size={20} />
                <span>Cameras</span>
              </NavLink>
            </li>
          )}
          {hasAccess(['Control Room']) && (
            <li>
              <NavLink to="/map" className={navLinkClass}>
                <Map size={20} />
                <span>Live Map</span>
              </NavLink>
            </li>
          )}
          {hasAccess(['Traffic Officer', 'Analyst']) && (
            <li>
              <NavLink to="/track" className={navLinkClass}>
                <SearchIcon size={20} />
                <span>Know Trajectory</span>
              </NavLink>
            </li>
          )}
          {hasAccess(['Analyst']) && (
            <li>
              <NavLink to="/analytics" className={navLinkClass}>
                <BarChart2 size={20} />
                <span>Analytics</span>
              </NavLink>
            </li>
          )}
          {hasAccess(['Traffic Officer']) && (
            <li>
              <NavLink to="/find-vehicle" className={navLinkClass}>
                <SearchIcon size={20} />
                <span>Find Vehicle</span>
              </NavLink>
            </li>
          )}
          {hasAccess(['Control Room']) && (
            <li>
              <NavLink to="/alerts" className={navLinkClass}>
                <AlertTriangle size={20} />
                <span>Alerts</span>
              </NavLink>
            </li>
          )}
          {hasAccess(['Traffic Officer']) && (
            <li>
              <NavLink to="/blacklist" className={navLinkClass}>
                <Shield size={20} />
                <span>Blacklist</span>
              </NavLink>
            </li>
          )}
        </ul>

        <div style={{ marginTop: 'auto', padding: '16px', marginBottom: '0', pointerEvents: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ width: '100%', marginBottom: '4px', display: 'flex', justifyContent: 'center' }}>
            <img src={charminarImg} alt="Charminar" style={{ width: '225px', height: '170px', objectFit: 'cover', objectPosition: 'top', mixBlendMode: 'lighten', opacity: 0.9, WebkitMaskImage: 'radial-gradient(circle at 50% 45%, black 40%, transparent 70%)', maskImage: 'radial-gradient(circle at 50% 45%, black 40%, transparent 70%)' }} />
          </div>
          <div style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '13px', fontWeight: '700', color: '#e2e8f0', letterSpacing: '0.5px', margin: '0 0 4px 0', textTransform: 'uppercase' }}>Hyderabad</h3>
            <p style={{ fontSize: '10px', color: '#94a3b8', margin: 0, fontWeight: '500', letterSpacing: '0.2px' }}>Traffic Management System</p>
            <div style={{ fontSize: '8px', color: '#64748b', marginTop: '6px' }}>Safe City • Smart Mobility • Better Tomorrow</div>
          </div>
        </div>

        <div className="nav-footer" style={{ marginTop: 0 }}>
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
            <div className="top-bar-branding">

              <div className="app-title-block">
                <h1>AI Traffic Engine</h1>
                <span>Smarter Roads. Safer Tomorrow.</span>
              </div>
            </div>
          </div>
          
          <div className="top-bar-right">
            <form className="global-search" onSubmit={handleSearchSubmit}>
              <SearchIcon size={18} className="search-icon" />
              <input 
                type="text" 
                placeholder="Search vehicle number, location, camera..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </form>

            <div className="system-status">
              <div className="status-dot online"></div>
              <div className="status-text">
                <strong>System Online</strong>
                <span>Last Updated: {new Date().toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
              </div>
            </div>

            <div className="notifications-container" style={{ position: 'relative' }}>
              <button 
                className="icon-btn" 
                onClick={() => { setNotificationsOpen(!notificationsOpen); setDropdownOpen(false); }}
              >
                <Bell size={20} />
                {alerts.length > 0 && <span className="badge-notification">{alerts.length}</span>}
              </button>

              {notificationsOpen && (
                <div className="dropdown-menu glass-panel" style={{ position: 'absolute', top: '100%', right: '-10px', marginTop: '16px', width: '320px', display: 'flex', flexDirection: 'column', zIndex: 1000, boxShadow: '0 10px 25px rgba(0,0,0,0.1)', padding: 0, overflow: 'hidden' }}>
                  <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)', background: 'var(--color-surface)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ fontSize: '14px', color: 'var(--color-text)' }}>Alerts</strong>
                    {alerts.length > 0 && (
                      <span onClick={() => { setAlerts([]); setNotificationsOpen(false); }} style={{ fontSize: '11px', color: '#3b82f6', cursor: 'pointer', fontWeight: '600' }}>Mark all as read</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', maxHeight: '300px', overflowY: 'auto' }}>
                    {alerts.length === 0 ? (
                      <div style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-light)', fontSize: '13px' }}>
                        No new alerts
                      </div>
                    ) : (
                      alerts.map(alert => (
                        <div key={alert.id} onClick={() => { navigate('/alerts'); setNotificationsOpen(false); }} style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)', cursor: 'pointer', background: 'rgba(239, 68, 68, 0.05)' }} className="notification-item">
                          <div style={{ display: 'flex', gap: '12px' }}>
                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444', marginTop: '6px', flexShrink: 0 }}></div>
                            <div>
                              <div style={{ fontSize: '13px', color: 'var(--color-text)', fontWeight: '500', lineHeight: '1.4' }}>{alert.text}</div>
                              <div style={{ fontSize: '11px', color: 'var(--color-text-light)', marginTop: '4px' }}>{alert.time}</div>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                  <div onClick={() => { navigate('/alerts'); setNotificationsOpen(false); }} style={{ padding: '10px', textAlign: 'center', background: 'var(--color-surface)', borderTop: '1px solid var(--color-border)', fontSize: '12px', color: 'var(--color-primary)', cursor: 'pointer', fontWeight: '600' }}>
                    View All Alerts
                  </div>
                </div>
              )}
            </div>

            <div className="user-info" style={{ display: 'flex', alignItems: 'center', gap: '12px', position: 'relative' }}>
              <div className="user-dropdown-container" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div 
                  className="user-avatar" 
                  onClick={() => { setDropdownOpen(!dropdownOpen); setNotificationsOpen(false); }}
                  title="Account Settings"
                >
                  {userRole.charAt(0).toUpperCase()}
                </div>
                <div className="user-name-display" onClick={() => { setDropdownOpen(!dropdownOpen); setNotificationsOpen(false); }} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '14px', fontWeight: '600' }}>
                  {userRole}
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6"/></svg>
                </div>
              
              {dropdownOpen && (
                <div className="dropdown-menu glass-panel" style={{ position: 'absolute', top: '100%', right: 0, marginTop: '8px', minWidth: '200px', display: 'flex', flexDirection: 'column', gap: '4px', zIndex: 1000 }}>
                  <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--color-border)', marginBottom: '4px' }}>
                    <strong>{userRole}</strong>
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
          </div>
        </header>

        <section className="page-content">
          <Outlet />
        </section>
      </main>
    </div>
  )
}

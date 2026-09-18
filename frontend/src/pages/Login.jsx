import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../services/api'
import { User, Lock, Eye, EyeOff, ArrowRight, BarChart2, ShieldCheck, Zap, AlertCircle, ArrowLeft, Shield, Users, Monitor, FileText, FileSearch, ChevronDown, ChevronUp } from 'lucide-react'
import logoImg from '../assets/logo_new.jpg'
import './Login.css'

export default function Login() {
  const navigate = useNavigate()
  const [selectedRole, setSelectedRole] = useState(null)
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false)
  const [officerId, setOfficerId] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (localStorage.getItem('token')) {
      navigate('/', { replace: true })
    }
  }, [navigate])

  const handleRoleSelect = (role, defaultUsername) => {
    setSelectedRole(role)
    setOfficerId(defaultUsername)
    setPassword('')
    setError('')
    setRoleDropdownOpen(false)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      await login({ officer_id: officerId, password })
      // Enforce selected role to ensure sidebar renders correctly
      const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
      storedUser.role = { name: selectedRole };
      localStorage.setItem('user', JSON.stringify(storedUser));
      navigate('/', { replace: true })
    } catch (err) {
      setError(err?.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const roles = [
    { name: 'Super Admin', icon: <Shield size={20} />, username: 'superadmin' },
    { name: 'Traffic Officer', icon: <Users size={20} />, username: 'officer' },
    { name: 'Control Room', icon: <Monitor size={20} />, username: 'control' },
    { name: 'Analyst', icon: <FileText size={20} />, username: 'analyst' },
  ]

  return (
    <div className="login-container">
      <div className="login-hero">
        <div className="login-hero-logo">
          <img src={logoImg} alt="AI Traffic Engine Logo" />
          <div>
            <h2>AI Traffic Engine</h2>
            <span>Smarter Traffic • Better Decisions</span>
          </div>
        </div>

        <h1>
          Turn data into<br />
          <span>smarter journeys.</span>
        </h1>
        <p>
          AI Traffic Engine helps you analyze, predict and optimize traffic — so you can make faster, smarter and more confident decisions for your city.
        </p>

        <div className="login-features">
          <div className="login-feature">
            <div className="login-feature-icon">
              <BarChart2 size={24} />
            </div>
            <div className="login-feature-text">Smarter<br />Insights</div>
          </div>
          <div className="login-feature">
            <div className="login-feature-icon">
              <ShieldCheck size={24} />
            </div>
            <div className="login-feature-text">Better<br />Decisions</div>
          </div>
          <div className="login-feature">
            <div className="login-feature-icon">
              <Zap size={24} />
            </div>
            <div className="login-feature-text">Smoother<br />Traffic</div>
          </div>
        </div>
      </div>

      <div className="login-form-wrapper">
        <div className="login-card">
          {!selectedRole ? (
            <div className="role-selection">
              <div className="login-card-header">
                <img src={logoImg} alt="Logo" />
                <h3>Welcome Back</h3>
                <p>Please select your role to continue</p>
              </div>

              <div className="role-dropdown-container">
                <button
                  className="role-dropdown-btn"
                  onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
                >
                  <span>Select a role</span>
                  {roleDropdownOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>

                {roleDropdownOpen && (
                  <div className="role-dropdown-list">
                    {roles.map((r) => (
                      <button
                        key={r.name}
                        className="role-dropdown-item"
                        onClick={() => handleRoleSelect(r.name, r.username)}
                      >
                        <span className="role-dropdown-icon">{r.icon}</span>
                        {r.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="login-form-inner">
              <button className="back-btn" onClick={() => {
                setSelectedRole(null)
                setRoleDropdownOpen(true)
              }}>
                <ArrowLeft size={18} /> Back to roles
              </button>

              <div className="login-card-header" style={{ marginTop: '1rem' }}>
                <h3>{selectedRole} Login</h3>
                <p>Sign in to your account</p>
              </div>

              <form onSubmit={handleSubmit} className="login-form">
                {error && (
                  <div className="login-error">
                    <AlertCircle size={16} />
                    {error}
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="officerId">Username</label>
                  <div className="input-with-icon">
                    <User size={18} className="input-icon" />
                    <input
                      id="officerId"
                      type="text"
                      value={officerId}
                      onChange={(event) => setOfficerId(event.target.value)}
                      placeholder="Enter username"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="password">Password</label>
                  <div className="input-with-icon">
                    <Lock size={18} className="input-icon" />
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      placeholder="Enter your password"
                      required
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowPassword(!showPassword)}
                      title={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                <div className="form-options">
                  <label className="remember-me">
                    <input type="checkbox" />
                    <span>Remember me</span>
                  </label>
                  <a href="#" className="forgot-password">Forgot password?</a>
                </div>

                <button type="submit" className="btn-primary" disabled={loading}>
                  {loading ? 'Signing in...' : 'Sign In'}
                  {!loading && <ArrowRight size={18} />}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

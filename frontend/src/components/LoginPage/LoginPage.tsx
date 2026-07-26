import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../store/AuthContext';
import { ShieldIcon, EyeIcon, EyeOffIcon, UserIcon, MailIcon, AlertTriangleIcon, CheckCircleIcon, RefreshCwIcon, LogInIcon, UserPlusIcon } from 'lucide-react';

type AuthMode = 'login' | 'register';

export default function LoginPage() {
  const { login, register, error, authEnabled } = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const usernameRef = useRef<HTMLInputElement>(null);

  // Focus username input on mount
  useEffect(() => {
    usernameRef.current?.focus();
  }, []);

  // Clear local error when switching modes
  useEffect(() => {
    setLocalError(null);
  }, [mode]);

  const displayError = localError || error;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim() || submitting) return;
    setSubmitting(true);
    setSuccess(false);
    setLocalError(null);
    const result = await login(username.trim(), password);
    if (result) {
      setSuccess(true);
    }
    setSubmitting(false);
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setLocalError(null);

    if (!username.trim() || username.trim().length < 3) {
      setLocalError('Username must be at least 3 characters.');
      return;
    }
    if (!email.trim() || !email.includes('@')) {
      setLocalError('Please enter a valid email address.');
      return;
    }
    if (!password.trim() || password.length < 6) {
      setLocalError('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    setSuccess(false);
    const result = await register(username.trim(), email.trim(), password);
    if (result.success) {
      setSuccess(true);
    } else {
      setLocalError(result.error || 'Registration failed.');
    }
    setSubmitting(false);
  };

  return (
    <div className="login-page">
      <div className="login-bg-gradient" />
      <div className="login-particles">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="login-orb" style={{
            '--orb-x': `${Math.random() * 100}%`,
            '--orb-y': `${Math.random() * 100}%`,
            '--orb-size': `${80 + Math.random() * 180}px`,
            '--orb-duration': `${20 + Math.random() * 30}s`,
            '--orb-delay': `${Math.random() * 15}s`,
            '--orb-opacity': 0.02 + Math.random() * 0.05,
          } as React.CSSProperties} />
        ))}
      </div>

      <div className="login-grid" />

      <div className="login-card">
        <div className="login-card-glow" />
        <div className="login-card-inner">
          {/* Logo */}
          <div className="login-logo">
            <div className="login-logo-icon">
              <ShieldIcon size={28} />
            </div>
            <div className="login-logo-text">
              <span className="login-logo-name">TRINETRA</span>
              <span className="login-logo-subtitle">OSINT Dashboard</span>
            </div>
          </div>

          <div className="login-divider" />

          {/* Tab Switcher */}
          <div className="login-tabs">
            <button
              className={`login-tab ${mode === 'login' ? 'active' : ''}`}
              onClick={() => setMode('login')}
            >
              <LogInIcon size={14} />
              Sign In
            </button>
            <button
              className={`login-tab ${mode === 'register' ? 'active' : ''}`}
              onClick={() => setMode('register')}
            >
              <UserPlusIcon size={14} />
              Register
            </button>
          </div>

          {/* Title */}
          {mode === 'login' ? (
            <>
              <h1 className="login-title">Welcome Back</h1>
              <p className="login-subtitle">
                Sign in to access the OSINT intelligence dashboard.
              </p>
            </>
          ) : (
            <>
              <h1 className="login-title">Create Account</h1>
              <p className="login-subtitle">
                Register to get started with the OSINT intelligence dashboard.
              </p>
            </>
          )}

          {/* Form */}
          <form onSubmit={mode === 'login' ? handleLogin : handleRegister} className="login-form">
            {/* Username */}
            <div className="login-input-wrapper">
              <div className="login-input-icon">
                <UserIcon size={16} />
              </div>
              <input
                ref={usernameRef}
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Username"
                className="login-input"
                disabled={submitting || success}
                autoComplete="username"
                spellCheck={false}
              />
            </div>

            {/* Email (register only) */}
            {mode === 'register' && (
              <div className="login-input-wrapper">
                <div className="login-input-icon">
                  <MailIcon size={16} />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="Email address"
                  className="login-input"
                  disabled={submitting || success}
                  autoComplete="email"
                />
              </div>
            )}

            {/* Password */}
            <div className="login-input-wrapper">
              <div className="login-input-icon">
                <ShieldIcon size={15} />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder={mode === 'register' ? 'Password (min. 6 characters)' : 'Password'}
                className="login-input"
                disabled={submitting || success}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
              <button
                type="button"
                className="login-toggle-vis"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOffIcon size={15} /> : <EyeIcon size={15} />}
              </button>
            </div>

            {/* Confirm Password (register only) */}
            {mode === 'register' && (
              <div className="login-input-wrapper">
                <div className="login-input-icon">
                  <ShieldIcon size={15} />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="Confirm password"
                  className="login-input"
                  disabled={submitting || success}
                  autoComplete="new-password"
                />
              </div>
            )}

            {/* Error */}
            {displayError && (
              <div className="login-error">
                <AlertTriangleIcon size={13} />
                <span>{displayError}</span>
              </div>
            )}

            {/* Success */}
            {success && (
              <div className="login-success">
                <CheckCircleIcon size={14} />
                <span>{mode === 'login' ? 'Signed in! Loading dashboard...' : 'Account created! Loading dashboard...'}</span>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              className="login-submit-btn"
              disabled={submitting || success}
            >
              {submitting ? (
                <>
                  <RefreshCwIcon size={14} className="login-spinner" />
                  {mode === 'login' ? 'Signing in...' : 'Creating account...'}
                </>
              ) : success ? (
                <>
                  <CheckCircleIcon size={14} />
                  {mode === 'login' ? 'Welcome' : 'Account Created'}
                </>
              ) : mode === 'login' ? (
                <>
                  <LogInIcon size={15} />
                  Sign In
                </>
              ) : (
                <>
                  <UserPlusIcon size={15} />
                  Create Account
                </>
              )}
            </button>
          </form>

          {/* Switch mode link */}
          <div className="login-switch-mode">
            {mode === 'login' ? (
              <span>
                Don't have an account?{' '}
                <button className="login-link-btn" onClick={() => setMode('register')}>
                  Register here
                </button>
              </span>
            ) : (
              <span>
                Already have an account?{' '}
                <button className="login-link-btn" onClick={() => setMode('login')}>
                  Sign in
                </button>
              </span>
            )}
          </div>

          {/* Footer */}
          <div className="login-footer">
            <span className="login-footer-dot" />
            <span>Registration open</span>
          </div>
        </div>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { useApp } from './store/AppContext';
import { useAuth } from './store/AuthContext';
import SearchBar from './components/SearchBar/SearchBar';
import Sidebar from './components/Sidebar/Sidebar';
import IndiaMap from './components/Map/IndiaMap';
import ReportView from './components/ReportView/ReportView';
import GraphView from './components/GraphView/GraphView';
import WatchPanel from './components/WatchPanel/WatchPanel';
import ToastNotification from './components/ToastNotification/ToastNotification';
import DashboardStats from './components/DashboardStats/DashboardStats';
import LiveFeed from './components/LiveFeed/LiveFeed';
import ScanProgress from './components/ScanProgress/ScanProgress';
import LoginPage from './components/LoginPage/LoginPage';
import LandingPage from './components/LandingPage/LandingPage';
import ChatBot from './components/ChatBot/ChatBot';
import CommandPalette from './components/CommandPalette/CommandPalette';
import { ShieldIcon, SearchIcon, EyeIcon, BoltIcon, LogOutIcon, KeyIcon } from './components/Icons/Icons';

function DashboardContent() {
  const { state, dispatch } = useApp();
  const { authEnabled, logout, username } = useAuth();
  const isIdle = !state.isSearching && state.results.length === 0;
  const [showLogoutMenu, setShowLogoutMenu] = useState(false);

  return (
    <div className="app-container">
      {/* Top Bar */}
      <header className={`top-bar ${isIdle ? 'top-bar-compact' : ''}`}>
        <div
          className="logo"
          onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'search' })}
          style={{ cursor: 'pointer' }}
        >
          <div className="logo-icon">
            <ShieldIcon size={18} color="white" />
          </div>
          <div className="logo-text">
            <span className="logo-name">TRINETRA</span>
            <span className="logo-subtitle">OSINT Dashboard</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${state.activeTab === 'search' ? 'active' : ''}`}
            onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'search' })}
          >
            <SearchIcon size={14} /> Search
          </button>
          <button
  className={`nav-tab ${state.activeTab === 'feed' ? 'active' : ''}`}
  onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'feed' })}
>
  <BoltIcon size={14} /> Live Feed
</button>
          <button
            className={`nav-tab ${state.activeTab === 'watches' ? 'active' : ''}`}
            onClick={() => dispatch({ type: 'SET_ACTIVE_TAB', payload: 'watches' })}
          >
            <EyeIcon size={14} /> Watches
          </button>
        </nav>

        {state.activeTab === 'search' && <SearchBar />}

        {/* Auth indicator & logout */}
        {authEnabled && (
          <div className="auth-badge-container">
            <button
              className="auth-badge-btn"
              onClick={() => setShowLogoutMenu(!showLogoutMenu)}
              title="Authentication settings"
            >
              <KeyIcon size={13} />
            </button>
            {showLogoutMenu && (
              <>
                <div className="auth-dropdown-backdrop" onClick={() => setShowLogoutMenu(false)} />
                <div className="auth-dropdown">
                  <div className="auth-dropdown-header">
                    <KeyIcon size={12} />
                    <span>{username || 'Authenticated'}</span>
                  </div>
                  <button
                    className="auth-dropdown-logout"
                    onClick={() => { setShowLogoutMenu(false); logout(); }}
                  >
                    <LogOutIcon size={12} />
                    <span>Disconnect</span>
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </header>

      {/* Dashboard Stats — only show during/after scan */}
      {state.activeTab === 'search' && !isIdle && <DashboardStats />}

      {/* Scan Progress */}
      {state.activeTab === 'search' && <ScanProgress />}

      {/* Toast Notifications */}
      <ToastNotification />

      {/* Main Content */}
      <div className="main-content">
        {state.activeTab === 'search' ? (
          <>
            {!isIdle && (
  <div className="search-sidebar-wrapper">
    <Sidebar />
  </div>
)}
            <IndiaMap />
            <ReportView />
            <GraphView />
          </>
        ) : state.activeTab === 'feed' ? (
  <LiveFeed />
        ) : (
          <WatchPanel />
        )}
      </div>

      <ChatBot />
      <CommandPalette />
    </div>
  );
}

function AuthGate() {
  const { isAuthenticated, isLoading, error, checkAuth } = useAuth();

  // Still loading auth status
  if (isLoading && isAuthenticated === null) {
    return (
      <div className="login-page">
        <div className="login-bg-gradient" />
        <div className="login-card">
          <div className="login-card-glow" />
          <div className="login-card-inner">
            <div className="login-logo">
              <div className="login-logo-icon">
                <ShieldIcon size={28} color="white" />
              </div>
              <div className="login-logo-text">
                <span className="login-logo-name">TRINETRA</span>
                <span className="login-logo-subtitle">OSINT Dashboard</span>
              </div>
            </div>
            <div className="login-loading">
              <div className="login-loading-spinner" />
              <span>Connecting to server...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error connecting to backend
  if (error && isAuthenticated === null) {
    return (
      <div className="login-page">
        <div className="login-bg-gradient" />
        <div className="login-card">
          <div className="login-card-glow" />
          <div className="login-card-inner">
            <div className="login-logo">
              <div className="login-logo-icon">
                <ShieldIcon size={28} color="white" />
              </div>
              <div className="login-logo-text">
                <span className="login-logo-name">TRINETRA</span>
                <span className="login-logo-subtitle">OSINT Dashboard</span>
              </div>
            </div>
            <div className="login-error" style={{ marginBottom: 12 }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              <span>{error}</span>
            </div>
            <button className="login-submit-btn" onClick={checkAuth}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Not authenticated — show login page
  if (!isAuthenticated) {
    return <LoginPage />;
  }

  // Authenticated — show dashboard
  return <DashboardContent />;
}

export default function App() {
  const [showLanding, setShowLanding] = useState(true);

  if (showLanding) {
    return (
      <LandingPage
        onEnterAuth={() => setShowLanding(false)}
        onOpenDashboard={() => setShowLanding(false)}
      />
    );
  }

  return <AuthGate />;
}
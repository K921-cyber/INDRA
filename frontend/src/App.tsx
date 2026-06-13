import React from 'react';
import { useApp } from './store/AppContext';
import SearchBar from './components/SearchBar/SearchBar';
import Sidebar from './components/Sidebar/Sidebar';
import IndiaMap from './components/Map/IndiaMap';
import ReportView from './components/ReportView/ReportView';
import GraphView from './components/GraphView/GraphView';
import WatchPanel from './components/WatchPanel/WatchPanel';
import LiveFeed from './components/LiveFeed/LiveFeed';
import ToastNotification from './components/ToastNotification/ToastNotification';
import DashboardStats from './components/DashboardStats/DashboardStats';
import ScanProgress from './components/ScanProgress/ScanProgress';
import TargetIntelPanel from './components/TargetIntelPanel/TargetIntelPanel';
import { ShieldIcon, SearchIcon, EyeIcon, BoltIcon } from './components/Icons/Icons';

export default function App() {
  const { state, dispatch } = useApp();
  const isIdle = !state.isSearching && state.results.length === 0;

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
                <TargetIntelPanel />
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
    </div>
  );
}

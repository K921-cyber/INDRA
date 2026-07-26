import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AppProvider } from './store/AppContext';
import { ThreatProvider } from './store/ThreatContext';
import { AuthProvider } from './store/AuthContext';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <AppProvider>
        <ThreatProvider>
          <App />
        </ThreatProvider>
      </AppProvider>
    </AuthProvider>
  </React.StrictMode>
);

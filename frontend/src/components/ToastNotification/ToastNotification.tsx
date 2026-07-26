import React, { useCallback } from 'react';
import { useApp } from '../../store/AppContext';

export default function ToastNotification() {
  const { state, dispatch } = useApp();

  const removeToast = useCallback((id: number) => {
    dispatch({ type: 'REMOVE_TOAST', payload: id });
  }, [dispatch]);

  if (state.toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {state.toasts.map((toast) => (
        <div
          key={toast.id}
          className={`toast-item toast-${toast.type}`}
          onClick={() => removeToast(toast.id)}
        >
          <span className="toast-icon">{toast.icon}</span>
          <span className="toast-message">{toast.message}</span>
          <button className="toast-close" onClick={(e) => { e.stopPropagation(); removeToast(toast.id); }}>×</button>
        </div>
      ))}
    </div>
  );
}

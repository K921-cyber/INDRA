import React from 'react';
import { AlertTriangleIcon, RefreshIcon } from '../Icons/Icons';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  compact?: boolean;
}

/** Shared error state used across panels — keeps every failure looking
 *  intentional instead of a raw error string. */
export default function ErrorState({ message, onRetry, compact }: ErrorStateProps) {
  return (
    <div className={`error-state ${compact ? 'error-state-compact' : ''}`}>
      <AlertTriangleIcon size={compact ? 13 : 16} color="var(--accent-red)" />
      <span className="error-state-message">{message}</span>
      {onRetry && (
        <button className="error-state-retry" onClick={onRetry} title="Retry">
          <RefreshIcon size={12} />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
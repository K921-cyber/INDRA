import React from 'react';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  message: string;
  ctaLabel?: string;
  ctaIcon?: React.ReactNode;
  onCta?: () => void;
  compact?: boolean;
}

/** Shared empty state used across panels (Watches, Live Feed, Graph View, etc.)
 *  — keeps every "nothing here yet" moment looking intentional and actionable
 *  instead of a blank box. Mirrors the visual language of ErrorState. */
export default function EmptyState({
  icon,
  title,
  message,
  ctaLabel,
  ctaIcon,
  onCta,
  compact,
}: EmptyStateProps) {
  return (
    <div className={`empty-state ${compact ? 'empty-state-compact' : ''}`}>
      <div className="empty-state-icon">{icon}</div>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-message">{message}</p>
      {ctaLabel && onCta && (
        <button className="empty-state-cta" onClick={onCta} type="button">
          {ctaIcon}
          <span>{ctaLabel}</span>
        </button>
      )}
    </div>
  );
}
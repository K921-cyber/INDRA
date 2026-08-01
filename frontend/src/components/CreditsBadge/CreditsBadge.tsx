import React, { useState } from 'react';
import { useAuth } from '../../store/AuthContext';
import { CreditCardIcon, PlusIcon, RefreshIcon } from '../Icons/Icons';

interface CreditsBadgeProps {
  onBuyCredits?: () => void;
}

export default function CreditsBadge({ onBuyCredits }: CreditsBadgeProps) {
  const { credits, refreshCredits, paymentConfigured } = useAuth();
  const [refreshing, setRefreshing] = useState(false);

  // Don't show if payment isn't configured or credits haven't loaded
  if (!paymentConfigured || credits === null) {
    return null;
  }

  const handleRefresh = async () => {
    setRefreshing(true);
    await refreshCredits();
    setRefreshing(false);
  };

  // Each search costs 10 credits — highlight the badge when the balance
  // is below one full search.
  const isLow = credits < 10;
  const isZero = credits === 0;

  return (
    <div className={`credits-badge ${isLow ? 'credits-badge-low' : ''} ${isZero ? 'credits-badge-empty' : ''}`}>
      <button
        className="credits-badge-inner"
        onClick={handleRefresh}
        title="Click to refresh credits"
      >
        <CreditCardIcon size={12} />
        <span className="credits-badge-count">
          {credits}
        </span>
        <span className="credits-badge-label">
          {credits === 1 ? 'credit' : 'credits'}
        </span>
        <RefreshIcon size={10} className={refreshing ? 'credits-refresh-spinning' : ''} />
      </button>
      {onBuyCredits && (
        <button className="credits-badge-buy" onClick={onBuyCredits} title="Buy more credits">
          <PlusIcon size={10} />
        </button>
      )}
    </div>
  );
}

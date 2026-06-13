import React, { useState, useCallback } from 'react';
import { useApp } from '../../store/AppContext';
import { detectSearchType } from '../../utils/detectSearchType';
import { SearchType } from '../../types';
import { SearchIcon } from '../Icons/Icons';

const typeLabels: Record<SearchType, string> = {
  domain: 'DOMAIN',
  ip: 'IP ADDRESS',
  email: 'EMAIL',
  phone: 'PHONE',
  username: 'USERNAME',
  name: 'PERSON',
  unknown: 'DETECTING...',
};

export default function SearchBar() {
  const { state, dispatch, runSearch } = useApp();
  const [inputValue, setInputValue] = useState('');
  const [detectedType, setDetectedType] = useState<SearchType>('unknown');

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputValue(val);
    if (val.trim()) {
      setDetectedType(detectSearchType(val.trim()));
    } else {
      setDetectedType('unknown');
    }
  }, []);

  const handleSearch = useCallback(async () => {
    const query = inputValue.trim();
    if (!query) return;
    dispatch({ type: 'SET_SEARCH_TYPE', payload: detectedType });
    await runSearch(query);
  }, [inputValue, detectedType, dispatch, runSearch]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  }, [handleSearch]);

  const badgeClass = `search-badge badge-${detectedType}`;

  return (
    <div className="search-container">
      <div className="search-wrapper">
        <span className="search-icon">
          <SearchIcon size={15} />
        </span>
        <input
          id="search-input"
          className="search-input"
          type="text"
          placeholder="Search domain, IP, email, phone, or name..."
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
        />
        {inputValue.trim() && detectedType !== 'unknown' && (
          <span className={badgeClass}>
            {typeLabels[detectedType]}
          </span>
        )}
        <button className="search-btn" onClick={handleSearch} disabled={!inputValue.trim()}>
          {state.isSearching
            ? `${state.completedPlugins}/${state.totalPlugins || '?'}...`
            : 'Scan'}
        </button>
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useApp } from '../../store/AppContext';
import { AppTab } from '../../types';
import { SearchIcon, BoltIcon, EyeIcon, CrosshairIcon, CloseIcon } from '../Icons/Icons';

interface Command {
  id: string;
  label: string;
  hint?: string;
  icon: React.ComponentType<{ size?: number; color?: string }>;
  action: () => void;
  group: 'navigate' | 'search';
}

/** Global command palette. Toggle with Ctrl+K / Cmd+K, or Escape to close. */
export default function CommandPalette() {
  const { dispatch, runSearch } = useApp();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global keyboard shortcut to open/close
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toLowerCase().includes('mac');
      const modKey = isMac ? e.metaKey : e.ctrlKey;
      if (modKey && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen(o => !o);
      } else if (e.key === 'Escape') {
        setOpen(false);
      }
    };
    const onExternalOpen = () => setOpen(true);
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('trinetra:open-command-palette', onExternalOpen);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('trinetra:open-command-palette', onExternalOpen);
    };
  }, []);

  // Focus input when opened, reset state when closed
  useEffect(() => {
    if (open) {
      setQuery('');
      setActiveIndex(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  const goTo = (tab: AppTab) => {
    dispatch({ type: 'SET_ACTIVE_TAB', payload: tab });
    setOpen(false);
  };

  const commands = useMemo<Command[]>(() => {
    const base: Command[] = [
      { id: 'nav-search', label: 'Go to Search', icon: SearchIcon, action: () => goTo('search'), group: 'navigate' },
      { id: 'nav-feed', label: 'Go to Live Feed', icon: BoltIcon, action: () => goTo('feed'), group: 'navigate' },
      { id: 'nav-watches', label: 'Go to Watches', icon: EyeIcon, action: () => goTo('watches'), group: 'navigate' },
    ];

    const trimmed = query.trim();
    if (trimmed.length > 0) {
      base.push({
        id: 'run-search',
        label: `Search for "${trimmed}"`,
        hint: 'Enter',
        icon: CrosshairIcon,
        action: () => {
          goTo('search');
          runSearch(trimmed);
        },
        group: 'search',
      });
    }

    if (!trimmed) return base;
    return base.filter(c => c.label.toLowerCase().includes(trimmed.toLowerCase()) || c.id === 'run-search');
  }, [query]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  const onKeyDownInput = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(i => Math.min(i + 1, commands.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      commands[activeIndex]?.action();
    }
  };

  if (!open) return null;

  return (
    <div className="cmdk-backdrop" onClick={() => setOpen(false)}>
      <div className="cmdk-panel" onClick={e => e.stopPropagation()}>
        <div className="cmdk-input-row">
          <SearchIcon size={15} color="var(--text-muted)" />
          <input
            ref={inputRef}
            className="cmdk-input"
            placeholder="Search a target, or jump to a section..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={onKeyDownInput}
          />
          <button className="cmdk-close" onClick={() => setOpen(false)}>
            <CloseIcon size={13} />
          </button>
        </div>

        <div className="cmdk-list">
          {commands.length === 0 && (
            <div className="cmdk-empty">No matches</div>
          )}
          {commands.map((cmd, i) => (
            <button
              key={cmd.id}
              className={`cmdk-item ${i === activeIndex ? 'cmdk-item-active' : ''}`}
              onMouseEnter={() => setActiveIndex(i)}
              onClick={cmd.action}
            >
              <cmd.icon size={14} color="var(--accent-blue)" />
              <span className="cmdk-item-label">{cmd.label}</span>
              {cmd.hint && <span className="cmdk-item-hint">{cmd.hint}</span>}
            </button>
          ))}
        </div>

        <div className="cmdk-footer">
          <span><kbd>↑</kbd><kbd>↓</kbd> navigate</span>
          <span><kbd>↵</kbd> select</span>
          <span><kbd>esc</kbd> close</span>
        </div>
      </div>
    </div>
  );
}
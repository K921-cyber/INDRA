import React, { useEffect, useState } from 'react';
import {
  ShieldIcon,
  SearchIcon,
  EyeIcon,
  BoltIcon,
  GraphIcon,
  GlobeIcon,
  CrosshairIcon,
  TerminalIcon,
  ChevronRightIcon,
} from '../Icons/Icons';

interface LandingPageProps {
  /** Called when the user wants to proceed to login/register */
  onEnterAuth: () => void;
  /** Called when the user wants to jump straight to the dashboard
   *  (if already authenticated this skips straight in, otherwise it
   *  behaves the same as onEnterAuth — AuthGate decides what to show) */
  onOpenDashboard: () => void;
}

const FEATURES = [
  {
    icon: SearchIcon,
    title: 'Unified OSINT Search',
    desc: 'Query usernames, emails, phone numbers and domains across dozens of open-source intelligence plugins from a single search bar.',
  },
  {
    icon: TerminalIcon,
    title: 'AI Threat Analyst',
    desc: 'A built-in conversational assistant that reads your scan results and answers questions, surfaces risk signals, and drafts summaries on demand.',
  },
  {
  icon: BoltIcon,
  title: 'Live Threat Feed',
  desc: 'Real-time stream of emerging indicators and activity, so analysts can react as new intelligence surfaces instead of polling for updates.',
},
  {
    icon: GraphIcon,
    title: 'Correlation Graphs',
    desc: 'Visualize how identities, infrastructure and artifacts connect with an interactive relationship graph built for investigative pivoting.',
  },
  {
    icon: GlobeIcon,
    title: 'Geospatial Mapping',
    desc: 'Plot indicators and incidents on an interactive map to spot regional patterns and concentration of activity at a glance.',
  },
  {
    icon: EyeIcon,
    title: 'Persistent Watchlists',
    desc: 'Track targets of interest over time and get notified the moment something changes across monitored sources.',
  },
];

const STEPS = [
  { n: '01', title: 'Search a target', desc: 'Enter a username, email, phone number, or domain to kick off a multi-source scan.' },
  { n: '02', title: 'Correlate & visualize', desc: 'Review results on the map, in the report view, or as a connected graph of entities.' },
  { n: '03', title: 'Ask the AI analyst', desc: 'Use the built-in chatbot to interrogate findings, get context, and speed up triage.' },
  { n: '04', title: 'Watch & get alerted', desc: 'Add targets to a watchlist and get notified when new intelligence appears.' },
];

export default function LandingPage({ onEnterAuth, onOpenDashboard }: LandingPageProps) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToFeatures = () => {
    document.getElementById('landing-features')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="landing-page">
      <div className="landing-bg-gradient" />
      <div className="landing-grid-overlay" />

      {/* Nav */}
      <header className={`landing-nav ${scrolled ? 'landing-nav-scrolled' : ''}`}>
        <div className="landing-nav-brand">
          <div className="landing-nav-logo-icon">
            <ShieldIcon size={18} color="white" />
          </div>
          <div className="landing-nav-logo-text">
            <span className="landing-nav-logo-name">TRINETRA</span>
            <span className="landing-nav-logo-subtitle">OSINT Platform</span>
          </div>
        </div>
        <nav className="landing-nav-links">
          <button className="landing-nav-link" onClick={scrollToFeatures}>Features</button>
          <a className="landing-nav-link" href="#landing-how-it-works">How it works</a>
        </nav>
        <div className="landing-nav-actions">
          <button className="landing-btn-ghost" onClick={onEnterAuth}>Sign in</button>
          <button className="landing-btn-primary" onClick={onEnterAuth}>
            Get started <ChevronRightIcon size={14} />
          </button>
        </div>
      </header>

      {/* Hero */}
      <section className="landing-hero">
        <div className="landing-hero-badge">
          <span className="landing-hero-badge-dot" />
          Live intelligence platform
        </div>
        <div className="landing-hero-meta-item">
  <BoltIcon size={13} /> Real-time feed
</div>
        <div className="landing-hero-logo-icon">
          <ShieldIcon size={40} color="white" />
        </div>
        <h1 className="landing-hero-title">
          See every signal.<br />Miss nothing.
        </h1>
        <p className="landing-hero-subtitle">
          Trinetra is an open-source intelligence platform for security analysts —
          unified OSINT search, live threat feeds, correlation graphs, geospatial
          mapping, and an AI analyst that helps you triage faster.
        </p>
        <div className="landing-hero-actions">
          <button className="landing-btn-primary landing-btn-lg" onClick={onOpenDashboard}>
            Open Dashboard <ChevronRightIcon size={16} />
          </button>
          <button className="landing-btn-secondary landing-btn-lg" onClick={onEnterAuth}>
            Sign up / Register
          </button>
        </div>
        <div className="landing-hero-meta">
          <div className="landing-hero-meta-item">
            <CrosshairIcon size={13} /> Multi-source OSINT correlation
          </div>
          <div className="landing-hero-meta-item">
            <ShieldIcon size={13} /> Built for analysts
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="landing-features" className="landing-section">
        <div className="landing-section-header">
          <span className="landing-section-eyebrow">Capabilities</span>
          <h2 className="landing-section-title">Everything an analyst needs, in one console</h2>
          <p className="landing-section-subtitle">
            Every module below is live in your workspace — search, mapping, graphing,
            watchlists, and the AI chatbot all run on your existing OSINT and chat APIs.
          </p>
        </div>
        
        <div className="landing-features-grid">
          {FEATURES.map((f, i) => (
            <div className="landing-feature-card" key={i}>
              <div className="landing-feature-icon">
                <f.icon size={20} color="var(--accent-blue)" />
              </div>
              <h3 className="landing-feature-title">{f.title}</h3>
              <p className="landing-feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="landing-how-it-works" className="landing-section landing-section-alt">
        <div className="landing-section-header">
          <span className="landing-section-eyebrow">Workflow</span>
          <h2 className="landing-section-title">How Trinetra works</h2>
        </div>
        <div className="landing-steps-grid">
          {STEPS.map((s) => (
            <div className="landing-step-card" key={s.n}>
              <span className="landing-step-num">{s.n}</span>
              <h3 className="landing-step-title">{s.title}</h3>
              <p className="landing-step-desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="landing-cta">
        <div className="landing-cta-inner">
          <h2 className="landing-cta-title">Ready to start investigating?</h2>
          <p className="landing-cta-subtitle">
            Create an account or sign in to open your dashboard.
          </p>
          <div className="landing-hero-actions">
            <button className="landing-btn-primary landing-btn-lg" onClick={onEnterAuth}>
              Sign up / Register <ChevronRightIcon size={16} />
            </button>
            <button className="landing-btn-secondary landing-btn-lg" onClick={onOpenDashboard}>
              Open Dashboard
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-nav-brand">
          <div className="landing-nav-logo-icon">
            <ShieldIcon size={16} color="white" />
          </div>
          <span className="landing-nav-logo-name">TRINETRA</span>
        </div>
        <span className="landing-footer-note">OSINT Intelligence Dashboard</span>
      </footer>
    </div>
  );
}
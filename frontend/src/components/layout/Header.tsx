import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { api } from '../../api/client';
import type { HealthResponse } from '../../types/analysis';
import { Icon } from '../common/Icon';
import './Header.css';

export function Header() {
  const location = useLocation();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        const res = await api.health();
        if (mounted) {
          setHealth(res);
          setOffline(false);
        }
      } catch {
        if (mounted) setOffline(true);
      }
    };
    check();
    const interval = window.setInterval(check, 30_000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <header className="header">
      <div className="container header__inner">
        <Link to="/" className="header__brand" aria-label="AI Resume Analyzer home">
          <div className="header__logo">
            <Icon name="sparkles" size={20} />
          </div>
          <span className="header__brand-title">
            Resume<span className="gradient-text">Match</span> AI
          </span>
        </Link>

        <nav className="header__nav" aria-label="Main Navigation">
          <Link
            to="/"
            className={`header__link ${location.pathname === '/' ? 'is-active' : ''}`}
          >
            <Icon name="plus" size={14} /> New Analysis
          </Link>
          <Link
            to="/history"
            className={`header__link ${location.pathname.startsWith('/history') ? 'is-active' : ''}`}
          >
            <Icon name="history" size={14} /> History
          </Link>

          {health && (
            <div
              className="header__status-badge"
              title={`Provider: ${health.llm_provider} (${health.llm_model})\nDatabase: ${health.database}`}
            >
              <span
                className={`header__status-dot ${
                  offline ? 'header__status-dot--offline' : health.status !== 'ok' ? 'header__status-dot--degraded' : ''
                }`}
              />
              <span>{health.llm_provider.toUpperCase()}</span>
            </div>
          )}

          {offline && (
            <div className="header__status-badge" title="Cannot reach backend API">
              <span className="header__status-dot header__status-dot--offline" />
              <span>API Offline</span>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

import type { ReactNode } from 'react';
import { Header } from './Header';

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header />
      <main className="container" style={{ flex: 1, padding: 'var(--sp-6) var(--sp-5)' }}>
        {children}
      </main>
      <footer className="footer">
        <div className="container footer__inner">
          <p>© {new Date().getFullYear()} AI Resume Analyzer — Local First, Privacy Preserved.</p>
          <div className="footer__links">
            <a href="/api/docs" target="_blank" rel="noreferrer">
              API Docs
            </a>
            <a href="/api/openapi.json" target="_blank" rel="noreferrer">
              OpenAPI JSON
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

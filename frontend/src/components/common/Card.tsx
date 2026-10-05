import type { ReactNode } from 'react';
import { Icon, type IconName } from './Icon';

interface CardProps {
  title: string;
  icon?: IconName;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
  children: ReactNode;
  delay?: number;
}

/** Glass section card used throughout the dashboard. */
export function Card({ title, icon, subtitle, action, className = '', children, delay = 0 }: CardProps) {
  const headingId = `card-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
  return (
    <section className={`card ${className}`} aria-labelledby={headingId} style={{ animationDelay: `${delay}ms` }}>
      <header className="card__header">
        <div>
          <h2 className="card__title" id={headingId}>
            {icon && (
              <span className="card__icon">
                <Icon name={icon} size={16} />
              </span>
            )}
            {title}
          </h2>
          {subtitle && <p className="card__subtitle">{subtitle}</p>}
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}

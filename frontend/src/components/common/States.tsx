import type { ReactNode } from 'react';
import { Icon, type IconName } from './Icon';
import './States.css';

interface EmptyStateProps {
  icon?: IconName;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon = 'sparkles', title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">
        <Icon name={icon} size={28} />
      </div>
      <h3>{title}</h3>
      {description && <p className="muted">{description}</p>}
      {action && <div className="empty-state__action">{action}</div>}
    </div>
  );
}

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorAlert({ title = 'Something went wrong', message, onRetry, onDismiss }: ErrorAlertProps) {
  return (
    <div className="alert alert--error" role="alert">
      <Icon name="alert" size={20} />
      <div className="alert__body">
        <p className="alert__title">{title}</p>
        <p>{message}</p>
      </div>
      {onRetry && (
        <button type="button" className="btn btn--ghost btn--sm" onClick={onRetry}>
          Retry
        </button>
      )}
      {onDismiss && (
        <button type="button" className="btn btn--ghost btn--sm btn--icon" onClick={onDismiss} aria-label="Dismiss error">
          <Icon name="x" size={14} />
        </button>
      )}
    </div>
  );
}

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return (
    <span className="spinner" role="status">
      <span className="sr-only">{label}</span>
    </span>
  );
}

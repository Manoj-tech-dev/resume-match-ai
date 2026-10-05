export type ScoreTone = 'excellent' | 'good' | 'fair' | 'poor';

export function scoreTone(score: number): ScoreTone {
  if (score >= 80) return 'excellent';
  if (score >= 65) return 'good';
  if (score >= 45) return 'fair';
  return 'poor';
}

const TONE_LABEL: Record<ScoreTone, string> = {
  excellent: 'Strong match',
  good: 'Good match',
  fair: 'Partial match',
  poor: 'Weak match',
};

const TONE_COLOR: Record<ScoreTone, string> = {
  excellent: 'var(--success)',
  good: 'var(--info)',
  fair: 'var(--warning)',
  poor: 'var(--danger)',
};

export const scoreLabel = (score: number) => TONE_LABEL[scoreTone(score)];
export const scoreColor = (score: number) => TONE_COLOR[scoreTone(score)];

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export function formatRelative(iso: string, now: number = Date.now()): string {
  const diff = (now - new Date(iso).getTime()) / 1000;
  if (Number.isNaN(diff)) return iso;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)}d ago`;
  return formatDate(iso);
}

export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

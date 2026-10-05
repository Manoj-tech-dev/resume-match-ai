import { describe, expect, it } from 'vitest';
import {
  capitalize,
  formatBytes,
  formatRelative,
  scoreColor,
  scoreLabel,
  scoreTone,
} from '../lib/format';

describe('format helpers', () => {
  it('classifies score tones accurately', () => {
    expect(scoreTone(92)).toBe('excellent');
    expect(scoreTone(80)).toBe('excellent');
    expect(scoreTone(75)).toBe('good');
    expect(scoreTone(65)).toBe('good');
    expect(scoreTone(55)).toBe('fair');
    expect(scoreTone(45)).toBe('fair');
    expect(scoreTone(30)).toBe('poor');
    expect(scoreTone(0)).toBe('poor');
  });

  it('provides human readable score labels and colors', () => {
    expect(scoreLabel(85)).toBe('Strong match');
    expect(scoreLabel(20)).toBe('Weak match');
    expect(scoreColor(85)).toContain('success');
    expect(scoreColor(20)).toContain('danger');
  });

  it('formats byte sizes nicely', () => {
    expect(formatBytes(500)).toBe('500 B');
    expect(formatBytes(2048)).toBe('2.0 KB');
    expect(formatBytes(1.5 * 1024 * 1024)).toBe('1.5 MB');
  });

  it('formats relative timestamps', () => {
    const now = new Date('2026-10-05T12:00:00Z').getTime();
    expect(formatRelative('2026-10-05T11:59:30Z', now)).toBe('just now');
    expect(formatRelative('2026-10-05T11:45:00Z', now)).toBe('15m ago');
    expect(formatRelative('2026-10-05T09:00:00Z', now)).toBe('3h ago');
    expect(formatRelative('2026-10-03T12:00:00Z', now)).toBe('2d ago');
  });

  it('capitalizes strings', () => {
    expect(capitalize('technical')).toBe('Technical');
    expect(capitalize('')).toBe('');
  });
});

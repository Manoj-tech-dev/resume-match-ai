import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ScoreRing } from '../components/dashboard/ScoreRing';

describe('ScoreRing component', () => {
  it('renders score with proper accessible label', () => {
    render(<ScoreRing score={85} />);
    const gauge = screen.getByRole('img');
    expect(gauge).toHaveAttribute('aria-label', expect.stringContaining('85 out of 100'));
    expect(gauge).toHaveAttribute('aria-label', expect.stringContaining('Strong match'));
  });

  it('clamps scores outside 0-100 bounds', () => {
    const { unmount } = render(<ScoreRing score={150} />);
    expect(screen.getByRole('img')).toHaveAttribute('aria-label', expect.stringContaining('100 out of 100'));
    unmount();

    render(<ScoreRing score={-10} />);
    expect(screen.getByRole('img')).toHaveAttribute('aria-label', expect.stringContaining('0 out of 100'));
  });
});

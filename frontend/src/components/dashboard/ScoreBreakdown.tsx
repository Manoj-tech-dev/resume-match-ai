import { scoreColor } from '../../lib/format';
import type { ScoreBreakdown as Breakdown } from '../../types/analysis';

const LABELS: Record<keyof Breakdown, string> = {
  skills: 'Skills',
  keywords: 'Keywords',
  experience: 'Experience',
  education: 'Education',
  projects: 'Projects',
};

export function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-bar">
      <div className="score-bar__row">
        <span>{label}</span>
        <strong style={{ color: scoreColor(value) }}>{value}</strong>
      </div>
      <div
        className="score-bar__track"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value}
      >
        <div className="score-bar__fill" style={{ width: `${value}%`, background: scoreColor(value) }} />
      </div>
    </div>
  );
}

export function ScoreBreakdown({ breakdown }: { breakdown: Breakdown }) {
  return (
    <div className="score-breakdown">
      {(Object.keys(LABELS) as (keyof Breakdown)[]).map((key) => (
        <ScoreBar key={key} label={LABELS[key]} value={breakdown[key]} />
      ))}
    </div>
  );
}

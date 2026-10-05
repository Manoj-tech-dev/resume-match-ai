import { useEffect, useState } from 'react';
import { Icon, type IconName } from '../common/Icon';

const STEPS: { label: string; icon: IconName; after: number }[] = [
  { label: 'Uploading resume', icon: 'upload', after: 0 },
  { label: 'Extracting text from PDF', icon: 'file', after: 900 },
  { label: 'Matching skills & keywords', icon: 'target', after: 2200 },
  { label: 'Generating AI insights', icon: 'sparkles', after: 3800 },
  { label: 'Building your report', icon: 'layers', after: 6500 },
];

interface AnalysisProgressProps {
  onCancel?: () => void;
}

/**
 * The analysis is a single request, so the stages are time-based estimates that
 * give the user a sense of progress; the last stage stays active until the
 * response arrives.
 */
export function AnalysisProgress({ onCancel }: AnalysisProgressProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const timer = window.setInterval(() => setElapsed(Date.now() - start), 200);
    return () => window.clearInterval(timer);
  }, []);

  const activeIndex = STEPS.reduce((acc, step, i) => (elapsed >= step.after ? i : acc), 0);
  const percent = Math.min(95, Math.round((1 - Math.exp(-elapsed / 4000)) * 100));

  return (
    <div className="progress card" role="status" aria-live="polite" aria-label="Analysis in progress">
      <div className="progress__orb" aria-hidden="true">
        <Icon name="sparkles" size={30} />
      </div>
      <h2 className="progress__title">Analyzing your resume</h2>
      <p className="muted">This usually takes a few seconds.</p>

      <div
        className="progress__bar"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-label="Estimated progress"
      >
        <div className="progress__fill" style={{ width: `${percent}%` }} />
      </div>

      <ol className="progress__steps">
        {STEPS.map((step, i) => {
          const state = i < activeIndex ? 'done' : i === activeIndex ? 'active' : 'pending';
          return (
            <li key={step.label} className={`progress__step progress__step--${state}`}>
              <span className="progress__step-icon">
                {state === 'done' ? <Icon name="check" size={14} /> : <Icon name={step.icon} size={14} />}
              </span>
              {step.label}
            </li>
          );
        })}
      </ol>

      {onCancel && (
        <button type="button" className="btn btn--ghost btn--sm" onClick={onCancel}>
          Cancel
        </button>
      )}
    </div>
  );
}

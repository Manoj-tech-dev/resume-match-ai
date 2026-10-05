import { useEffect, useState } from 'react';
import { scoreColor, scoreLabel } from '../../lib/format';

interface ScoreRingProps {
  score: number;
  size?: number;
  stroke?: number;
  label?: string;
}

/** Animated circular score gauge. */
export function ScoreRing({ score, size = 180, stroke = 14, label = 'ATS score' }: ScoreRingProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));
  const [shown, setShown] = useState(0);

  useEffect(() => {
    let frame = 0;
    const start = performance.now();
    const duration = 1100;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setShown(Math.round(clamped * eased));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [clamped]);

  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - shown / 100);
  const color = scoreColor(clamped);
  const gradientId = `ring-${size}-${clamped}`;

  return (
    <div
      className="score-ring"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`${label}: ${clamped} out of 100, ${scoreLabel(clamped)}`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={color} />
            <stop offset="100%" stopColor="hsl(258 90% 66%)" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="hsla(0,0%,100%,0.07)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ filter: `drop-shadow(0 0 10px ${color})` }}
        />
      </svg>
      <div className="score-ring__center" aria-hidden="true">
        <span className="score-ring__value">{shown}</span>
        <span className="score-ring__max">/ 100</span>
      </div>
    </div>
  );
}

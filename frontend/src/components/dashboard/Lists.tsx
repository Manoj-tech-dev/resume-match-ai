import { useState } from 'react';
import { capitalize } from '../../lib/format';
import type {
  BulletRewrite,
  InterviewQuestion,
  ProjectRecommendation,
  QuestionCategory,
  Suggestion,
} from '../../types/analysis';
import { Icon } from '../common/Icon';
import { useToast } from '../common/Toast';

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 } as const;

export function SuggestionList({ suggestions }: { suggestions: Suggestion[] }) {
  if (suggestions.length === 0) return <p className="muted small">No suggestions — nice work.</p>;
  const sorted = [...suggestions].sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]);
  return (
    <ol className="suggestions">
      {sorted.map((s, i) => (
        <li key={`${s.title}-${i}`} className="suggestion">
          <span className="suggestion__index">{i + 1}</span>
          <div>
            <div className="suggestion__head">
              <h3>{s.title}</h3>
              <span className={`badge badge--${s.priority}`}>{s.priority}</span>
            </div>
            <p className="muted">{s.detail}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

export function BulletRewrites({ bullets }: { bullets: BulletRewrite[] }) {
  const { notify } = useToast();
  const [copied, setCopied] = useState<number | null>(null);

  if (bullets.length === 0) return <p className="muted small">No bullet points could be identified for rewriting.</p>;

  const copy = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(index);
      notify('Bullet point copied to clipboard');
      window.setTimeout(() => setCopied((c) => (c === index ? null : c)), 1500);
    } catch {
      notify('Could not copy to clipboard', 'error');
    }
  };

  return (
    <ul className="rewrites">
      {bullets.map((b, i) => (
        <li key={`${b.original}-${i}`} className="rewrite">
          <div className="rewrite__before">
            <span className="rewrite__tag">Before</span>
            <p>{b.original}</p>
          </div>
          <div className="rewrite__after">
            <span className="rewrite__tag rewrite__tag--after">After</span>
            <p>{b.improved}</p>
            <button
              type="button"
              className="btn btn--ghost btn--sm rewrite__copy"
              onClick={() => copy(b.improved, i)}
              aria-label={`Copy improved bullet ${i + 1}`}
            >
              <Icon name={copied === i ? 'check' : 'file'} size={14} /> {copied === i ? 'Copied' : 'Copy'}
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}

export function ProjectList({ projects }: { projects: ProjectRecommendation[] }) {
  if (projects.length === 0) return <p className="muted small">No project recommendations.</p>;
  return (
    <ul className="projects">
      {projects.map((p) => (
        <li key={p.title} className="project">
          <span className="project__icon">
            <Icon name="rocket" size={18} />
          </span>
          <h3>{p.title}</h3>
          <p className="muted">{p.description}</p>
          {p.skills.length > 0 && (
            <ul className="chip-list">
              {p.skills.map((s) => (
                <li key={s} className="chip chip--info">
                  {s}
                </li>
              ))}
            </ul>
          )}
        </li>
      ))}
    </ul>
  );
}

const CATEGORY_LABEL: Record<QuestionCategory, string> = {
  technical: 'Technical',
  behavioral: 'Behavioral',
  experience: 'Experience',
  gap: 'Skill gap',
};

export function InterviewQuestions({ questions }: { questions: InterviewQuestion[] }) {
  const categories = Array.from(new Set(questions.map((q) => q.category)));
  const [active, setActive] = useState<QuestionCategory | 'all'>('all');

  if (questions.length === 0) return <p className="muted small">No interview questions generated.</p>;
  const visible = active === 'all' ? questions : questions.filter((q) => q.category === active);

  return (
    <div>
      <div className="segmented segmented--wrap" role="group" aria-label="Filter questions by category">
        {(['all', ...categories] as const).map((c) => (
          <button
            key={c}
            type="button"
            className={`segmented__btn ${active === c ? 'is-active' : ''}`}
            aria-pressed={active === c}
            onClick={() => setActive(c)}
          >
            {c === 'all' ? 'All' : CATEGORY_LABEL[c] ?? capitalize(c)}
          </button>
        ))}
      </div>
      <ol className="questions">
        {visible.map((q, i) => (
          <li key={`${q.question}-${i}`} className="question">
            <details>
              <summary>
                <span className={`question__cat question__cat--${q.category}`}>{CATEGORY_LABEL[q.category]}</span>
                <span className="question__text">{q.question}</span>
              </summary>
              {q.rationale && (
                <p className="question__why">
                  <Icon name="info" size={14} /> Why this may be asked: {q.rationale}
                </p>
              )}
            </details>
          </li>
        ))}
      </ol>
    </div>
  );
}

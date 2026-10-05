import { useState } from 'react';
import { formatRelative, scoreColor } from '../../lib/format';
import type { AnalysisSummary } from '../../types/analysis';
import { Icon } from '../common/Icon';
import './History.css';

interface HistoryListProps {
  items: AnalysisSummary[];
  onSelect: (id: string) => void;
  onDelete: (id: string) => Promise<void>;
}

export function HistoryList({ items, onSelect, onDelete }: HistoryListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (deletingId) return;
    setDeletingId(id);
    try {
      await onDelete(id);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <ul className="history-list" aria-label="Analysis History">
      {items.map((item) => {
        const color = scoreColor(item.overall_score);
        const isDeleting = deletingId === item.id;

        return (
          <li key={item.id} className="history-item">
            <div
              className="history-item__main"
              onClick={() => onSelect(item.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelect(item.id);
                }
              }}
              aria-label={`Open analysis for ${item.job_title}`}
            >
              <div
                className="history-item__score-badge"
                style={{ borderColor: color, color }}
                title={`Score: ${item.overall_score}/100`}
              >
                <span className="history-item__score-num">{item.overall_score}</span>
              </div>

              <div className="history-item__details">
                <span className="history-item__title">{item.job_title}</span>
                <div className="history-item__meta">
                  <span>
                    <Icon name="file" size={12} /> {item.resume_filename}
                  </span>
                  <span>•</span>
                  <span>{formatRelative(item.created_at)}</span>
                  <span>•</span>
                  <span className="badge badge--low" style={{ textTransform: 'capitalize' }}>
                    {item.provider}
                  </span>
                </div>
              </div>
            </div>

            <div className="history-item__actions">
              <button
                type="button"
                className="btn btn--ghost btn--sm"
                onClick={() => onSelect(item.id)}
                aria-label="View analysis details"
              >
                View Report <Icon name="arrowRight" size={14} />
              </button>
              <button
                type="button"
                className="btn btn--danger btn--sm btn--icon"
                onClick={(e) => handleDelete(e, item.id)}
                disabled={isDeleting}
                aria-label={`Delete analysis for ${item.job_title}`}
                title="Delete analysis"
              >
                {isDeleting ? <span className="spinner" style={{ width: 14, height: 14 }} /> : <Icon name="trash" size={14} />}
              </button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

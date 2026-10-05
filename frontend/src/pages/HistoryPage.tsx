import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, errorMessage } from '../api/client';
import { Icon } from '../components/common/Icon';
import { EmptyState, ErrorAlert } from '../components/common/States';
import { useToast } from '../components/common/Toast';
import { HistoryList } from '../components/history/HistoryList';
import type { AnalysisSummary } from '../types/analysis';

export function HistoryPage() {
  const navigate = useNavigate();
  const { notify } = useToast();
  const [items, setItems] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listAnalyses();
      setItems(res.items);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await api.deleteAnalysis(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      notify('Analysis deleted', 'success');
    } catch (err) {
      notify(errorMessage(err), 'error');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--sp-3)' }}>
        <div>
          <h1 style={{ fontSize: 'var(--fs-2xl)', fontWeight: 800 }}>Analysis History</h1>
          <p className="muted" style={{ fontSize: 'var(--fs-sm)' }}>
            Review past resume evaluations, track improvements, or remove old records.
          </p>
        </div>
        <button type="button" className="btn btn--primary btn--sm" onClick={() => navigate('/')}>
          <Icon name="plus" size={14} /> New Analysis
        </button>
      </div>

      {error && <ErrorAlert message={error} onRetry={fetchHistory} />}

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
          <div className="skeleton" style={{ height: 80 }} />
          <div className="skeleton" style={{ height: 80 }} />
          <div className="skeleton" style={{ height: 80 }} />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon="history"
          title="No analyses yet"
          description="Upload your first resume and compare it against a target job posting to see your ATS compatibility report."
          action={
            <button type="button" className="btn btn--primary" onClick={() => navigate('/')}>
              <Icon name="sparkles" /> Start your first analysis
            </button>
          }
        />
      ) : (
        <HistoryList
          items={items}
          onSelect={(id) => navigate(`/analyses/${id}`)}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}

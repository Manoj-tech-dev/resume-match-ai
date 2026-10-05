import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { api, errorMessage } from '../api/client';
import { Icon } from '../components/common/Icon';
import { ErrorAlert } from '../components/common/States';
import { useToast } from '../components/common/Toast';
import { ResultsDashboard } from '../components/dashboard/ResultsDashboard';
import type { AnalysisRecord } from '../types/analysis';

export function ResultPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { notify } = useToast();

  const preloadedRecord = (location.state as { record?: AnalysisRecord })?.record;
  const [record, setRecord] = useState<AnalysisRecord | null>(preloadedRecord ?? null);
  const [loading, setLoading] = useState<boolean>(!preloadedRecord);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (preloadedRecord && preloadedRecord.id === id) {
      setRecord(preloadedRecord);
      setLoading(false);
      return;
    }

    if (!id) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    api
      .getAnalysis(id)
      .then((data) => {
        if (mounted) setRecord(data);
      })
      .catch((err) => {
        if (mounted) setError(errorMessage(err));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [id, preloadedRecord]);

  const handleDelete = async () => {
    if (!id || !window.confirm('Are you sure you want to delete this analysis?')) return;
    try {
      await api.deleteAnalysis(id);
      notify('Analysis deleted', 'success');
      navigate('/history');
    } catch (err) {
      notify(errorMessage(err), 'error');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
        <div className="skeleton" style={{ height: 200, width: '100%' }} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-5)' }}>
          <div className="skeleton" style={{ height: 300 }} />
          <div className="skeleton" style={{ height: 300 }} />
        </div>
      </div>
    );
  }

  if (error || !record) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)', maxWidth: 600, margin: '0 auto' }}>
        <ErrorAlert
          title="Could not load analysis"
          message={error ?? 'The requested analysis could not be found.'}
        />
        <button type="button" className="btn btn--primary" onClick={() => navigate('/')}>
          <Icon name="arrowLeft" /> Back to Analyzer
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-5)' }}>
      {/* Top action bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 'var(--sp-3)' }}>
        <button type="button" className="btn btn--ghost btn--sm" onClick={() => navigate('/')}>
          <Icon name="arrowLeft" size={14} /> New Analysis
        </button>
        <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => navigate('/history')}>
            <Icon name="history" size={14} /> View All History
          </button>
          <button type="button" className="btn btn--danger btn--sm" onClick={handleDelete} title="Delete this analysis">
            <Icon name="trash" size={14} /> Delete
          </button>
        </div>
      </div>

      <ResultsDashboard record={record} />
    </div>
  );
}

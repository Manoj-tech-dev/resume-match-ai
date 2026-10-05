import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, errorMessage } from '../api/client';
import { AnalysisProgress } from '../components/analyze/AnalysisProgress';
import { AnalyzeForm } from '../components/analyze/AnalyzeForm';
import { ErrorAlert } from '../components/common/States';
import { useToast } from '../components/common/Toast';

export function AnalyzePage() {
  const navigate = useNavigate();
  const { notify } = useToast();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setSubmitting(false);
    notify('Analysis cancelled', 'info');
  };

  const handleSubmit = async (file: File, jobDescription: string) => {
    setError(null);
    setSubmitting(true);
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const record = await api.analyze(file, jobDescription, controller.signal);
      notify('Analysis complete!', 'success');
      navigate(`/analyses/${record.id}`, { state: { record } });
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-6)' }}>
      {/* Hero Header */}
      <section style={{ textAlign: 'center', maxWidth: 680, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
        <h1 style={{ fontSize: 'var(--fs-3xl)', fontWeight: 800 }}>
          Supercharge your <span className="gradient-text">ATS Resume Score</span>
        </h1>
        <p className="muted" style={{ fontSize: 'var(--fs-lg)' }}>
          Upload your resume in PDF, Word (.docx), PowerPoint (.pptx), image, or text format and paste a job description. Our AI evaluates ATS compatibility, identifies missing skills, rewrites bullet points, and prepares interview questions.
        </p>
      </section>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {submitting ? (
        <AnalysisProgress onCancel={handleCancel} />
      ) : (
        <AnalyzeForm onSubmit={handleSubmit} submitting={submitting} maxSizeMb={5} />
      )}
    </div>
  );
}

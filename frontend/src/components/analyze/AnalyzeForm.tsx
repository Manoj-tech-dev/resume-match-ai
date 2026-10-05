import { useState, type FormEvent } from 'react';
import { validateJobDescription, validateResumeFile } from '../../lib/validation';
import { Icon } from '../common/Icon';
import { FileDropzone } from './FileDropzone';
import { JobDescriptionInput } from './JobDescriptionInput';
import './Analyze.css';

interface AnalyzeFormProps {
  onSubmit: (file: File, jobDescription: string) => void;
  submitting: boolean;
  maxSizeMb: number;
}

export function AnalyzeForm({ onSubmit, submitting, maxSizeMb }: AnalyzeFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [touched, setTouched] = useState(false);

  const fileError = validateResumeFile(file, maxSizeMb);
  const jdError = validateJobDescription(jobDescription);
  // Show the file error as soon as a bad file is chosen; otherwise only after submit.
  const showFileError = (touched || file !== null) ? fileError : null;
  const showJdError = touched ? jdError : null;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (fileError || jdError || !file) return;
    onSubmit(file, jobDescription.trim());
  };

  return (
    <form className="analyze-form card" onSubmit={handleSubmit} noValidate aria-busy={submitting}>
      <div className="analyze-form__grid">
        <FileDropzone
          file={file}
          onFileChange={setFile}
          error={showFileError}
          disabled={submitting}
          maxSizeMb={maxSizeMb}
        />
        <div className="analyze-form__tips">
          <p className="analyze-form__tips-title">
            <Icon name="lightbulb" size={16} /> For the best results
          </p>
          <ul>
            <li>Upload resumes in PDF, Word (.docx), PowerPoint (.pptx), image, or text format.</li>
            <li>Paste the complete job posting, including requirements.</li>
            <li>Your resume text is analyzed but never stored — only the results are saved.</li>
          </ul>
        </div>
      </div>

      <JobDescriptionInput
        value={jobDescription}
        onChange={setJobDescription}
        error={showJdError}
        disabled={submitting}
      />

      <div className="analyze-form__footer">
        <p className="field__hint">
          <Icon name="shield" size={12} /> Files are validated and processed in memory.
        </p>
        <button id="analyze-submit" type="submit" className="btn btn--primary btn--lg" disabled={submitting}>
          {submitting ? (
            <>
              <span className="spinner" aria-hidden="true" /> Analyzing…
            </>
          ) : (
            <>
              <Icon name="sparkles" /> Analyze resume
            </>
          )}
        </button>
      </div>
    </form>
  );
}

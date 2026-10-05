import { useId } from 'react';
import { MAX_JOB_DESCRIPTION_CHARS } from '../../lib/validation';
import { Icon } from '../common/Icon';

interface JobDescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: string | null;
  disabled?: boolean;
}

export function JobDescriptionInput({ value, onChange, error, disabled = false }: JobDescriptionInputProps) {
  const id = useId();
  const errorId = `${id}-error`;
  const count = value.trim().length;
  const over = count > MAX_JOB_DESCRIPTION_CHARS;

  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        Job description
        <span className="field__hint" style={over ? { color: 'var(--danger)' } : undefined}>
          {count.toLocaleString()} / {MAX_JOB_DESCRIPTION_CHARS.toLocaleString()}
        </span>
      </label>
      <textarea
        id={id}
        className="textarea"
        placeholder="Paste the full job posting here — title, responsibilities, requirements and nice-to-haves…"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
      />
      {error && (
        <p className="field__error" id={errorId}>
          <Icon name="alert" size={14} /> {error}
        </p>
      )}
    </div>
  );
}

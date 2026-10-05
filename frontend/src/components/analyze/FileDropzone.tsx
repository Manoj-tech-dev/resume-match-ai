import { useId, useRef, useState, type DragEvent, type KeyboardEvent } from 'react';
import { formatBytes } from '../../lib/format';
import { Icon } from '../common/Icon';

interface FileDropzoneProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  error?: string | null;
  disabled?: boolean;
  maxSizeMb: number;
}

export function FileDropzone({ file, onFileChange, error, disabled = false, maxSizeMb }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const inputId = useId();
  const errorId = `${inputId}-error`;

  const openPicker = () => !disabled && inputRef.current?.click();

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    if (disabled) return;
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) onFileChange(dropped);
  };

  const handleKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      openPicker();
    }
  };

  const clear = () => {
    onFileChange(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="field">
      <label className="field__label" htmlFor={inputId}>
        Resume <span className="field__hint">PDF · max {maxSizeMb} MB</span>
      </label>

      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept="application/pdf,.pdf"
        className="sr-only"
        disabled={disabled}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        data-testid="resume-input"
        onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
      />

      {file ? (
        <div className={`file-pill ${error ? 'file-pill--error' : ''}`}>
          <span className="file-pill__icon">
            <Icon name="file" size={22} />
          </span>
          <div className="file-pill__meta">
            <p className="file-pill__name" title={file.name}>
              {file.name}
            </p>
            <p className="field__hint">{formatBytes(file.size)}</p>
          </div>
          <button type="button" className="btn btn--ghost btn--sm" onClick={openPicker} disabled={disabled}>
            Replace
          </button>
          <button
            type="button"
            className="btn btn--ghost btn--sm btn--icon"
            onClick={clear}
            disabled={disabled}
            aria-label="Remove file"
          >
            <Icon name="x" size={14} />
          </button>
        </div>
      ) : (
        <div
          role="button"
          tabIndex={disabled ? -1 : 0}
          aria-disabled={disabled}
          aria-label="Upload resume PDF: drag and drop or press to browse"
          className={`dropzone ${dragging ? 'dropzone--active' : ''} ${error ? 'dropzone--error' : ''}`}
          onClick={openPicker}
          onKeyDown={handleKey}
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <div className="dropzone__icon">
            <Icon name="upload" size={26} />
          </div>
          <p className="dropzone__title">
            <strong>Drop your resume here</strong> or <span className="gradient-text">browse</span>
          </p>
          <p className="field__hint">Text-based PDFs work best (not scanned images)</p>
        </div>
      )}

      {error && (
        <p className="field__error" id={errorId}>
          <Icon name="alert" size={14} /> {error}
        </p>
      )}
    </div>
  );
}

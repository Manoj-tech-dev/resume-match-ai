import { describe, expect, it } from 'vitest';
import {
  MAX_JOB_DESCRIPTION_CHARS,
  MIN_JOB_DESCRIPTION_CHARS,
  validateJobDescription,
  validateResumeFile,
} from '../lib/validation';

describe('validateResumeFile', () => {
  it('rejects null file', () => {
    expect(validateResumeFile(null)).toMatch(/upload your resume/i);
  });

  it('accepts valid PDF', () => {
    const file = new File(['%PDF-1.4 dummy content'], 'resume.pdf', { type: 'application/pdf' });
    expect(validateResumeFile(file)).toBeNull();
  });

  it('rejects non-pdf extension', () => {
    const file = new File(['content'], 'resume.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    expect(validateResumeFile(file)).toMatch(/only pdf files/i);
  });

  it('rejects empty file', () => {
    const file = new File([], 'resume.pdf', { type: 'application/pdf' });
    expect(validateResumeFile(file)).toMatch(/file is empty/i);
  });

  it('rejects file exceeding max size', () => {
    const big = new Uint8Array(2 * 1024 * 1024);
    const file = new File([big], 'resume.pdf', { type: 'application/pdf' });
    expect(validateResumeFile(file, 1)).toMatch(/maximum size is 1 mb/i);
  });
});

describe('validateJobDescription', () => {
  it('rejects empty text', () => {
    expect(validateJobDescription('')).toMatch(/please paste the job description/i);
    expect(validateJobDescription('   \n\t')).toMatch(/please paste the job description/i);
  });

  it('rejects text shorter than minimum', () => {
    expect(validateJobDescription('Junior dev')).toContain(`minimum ${MIN_JOB_DESCRIPTION_CHARS}`);
  });

  it('accepts valid job description', () => {
    const valid = 'We are looking for a Senior Software Engineer with strong Python and React skills to join our platform team.';
    expect(validateJobDescription(valid)).toBeNull();
  });

  it('rejects text longer than maximum', () => {
    const huge = 'a'.repeat(MAX_JOB_DESCRIPTION_CHARS + 10);
    expect(validateJobDescription(huge)).toContain('too long');
  });
});

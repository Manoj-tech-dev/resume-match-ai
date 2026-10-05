// Client-side validation mirrors the backend rules for fast feedback.
// The backend remains the source of truth and re-validates everything.

export const DEFAULT_MAX_UPLOAD_MB = 5;
export const MIN_JOB_DESCRIPTION_CHARS = 30;
export const MAX_JOB_DESCRIPTION_CHARS = 20_000;

export const SUPPORTED_EXTENSIONS = [
  '.pdf',
  '.docx',
  '.doc',
  '.pptx',
  '.ppt',
  '.png',
  '.jpg',
  '.jpeg',
  '.webp',
  '.bmp',
  '.tiff',
  '.txt',
  '.md',
  '.rtf',
];

export function validateResumeFile(file: File | null, maxMb: number = DEFAULT_MAX_UPLOAD_MB): string | null {
  if (!file) return 'Please upload your resume (PDF, Word, PPTX, image, or text file).';

  const name = file.name.toLowerCase();
  const hasValidExt = SUPPORTED_EXTENSIONS.some((ext) => name.endsWith(ext));
  if (!hasValidExt) {
    return 'Unsupported file format. Please upload a PDF, Word (.docx), PowerPoint (.pptx), image (.png, .jpg), or text file.';
  }

  if (file.size === 0) return 'This file is empty.';
  if (file.size > maxMb * 1024 * 1024) return `File is too large. Maximum size is ${maxMb} MB.`;
  return null;
}

export function validateJobDescription(text: string): string | null {
  const trimmed = text.trim();
  if (!trimmed) return 'Please paste the job description.';
  if (trimmed.length < MIN_JOB_DESCRIPTION_CHARS)
    return `Job description is too short (minimum ${MIN_JOB_DESCRIPTION_CHARS} characters).`;
  if (trimmed.length > MAX_JOB_DESCRIPTION_CHARS)
    return `Job description is too long (maximum ${MAX_JOB_DESCRIPTION_CHARS.toLocaleString()} characters).`;
  return null;
}

import type {
  AnalysisListResponse,
  AnalysisRecord,
  ApiErrorBody,
  HealthResponse,
} from '../types/analysis';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '') + '/api';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

function isErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === 'object' &&
    value !== null &&
    'error' in value &&
    typeof (value as ApiErrorBody).error?.message === 'string'
  );
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err;
    throw new ApiError(0, 'network_error', 'Cannot reach the server. Is the backend running?');
  }

  if (response.status === 204) return undefined as T;

  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    if (isErrorBody(body)) throw new ApiError(response.status, body.error.code, body.error.message);
    throw new ApiError(response.status, 'http_error', `Request failed (HTTP ${response.status}).`);
  }
  return body as T;
}

export const api = {
  health: (signal?: AbortSignal) => request<HealthResponse>('/health', { signal }),

  analyze: (resume: File, jobDescription: string, signal?: AbortSignal) => {
    const form = new FormData();
    form.append('resume', resume);
    form.append('job_description', jobDescription);
    return request<AnalysisRecord>('/analyze', { method: 'POST', body: form, signal });
  },

  listAnalyses: (signal?: AbortSignal, limit = 100, offset = 0) =>
    request<AnalysisListResponse>(`/analyses?limit=${limit}&offset=${offset}`, { signal }),

  getAnalysis: (id: string, signal?: AbortSignal) =>
    request<AnalysisRecord>(`/analyses/${encodeURIComponent(id)}`, { signal }),

  deleteAnalysis: (id: string) =>
    request<void>(`/analyses/${encodeURIComponent(id)}`, { method: 'DELETE' }),
};

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return 'Something went wrong.';
}

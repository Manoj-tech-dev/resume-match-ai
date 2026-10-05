// Mirrors backend/app/schemas/analysis.py — keep in sync.

export type Priority = 'high' | 'medium' | 'low';

export interface ScoreBreakdown {
  skills: number;
  experience: number;
  education: number;
  projects: number;
  keywords: number;
}

export interface SectionAssessment {
  score: number;
  summary: string;
  strengths: string[];
  gaps: string[];
}

export interface KeywordMatch {
  keyword: string;
  found: boolean;
  importance: Priority;
  occurrences: number;
}

export interface KeywordAnalysis {
  match_rate: number;
  keywords: KeywordMatch[];
}

export interface Suggestion {
  title: string;
  detail: string;
  priority: Priority;
}

export interface BulletRewrite {
  original: string;
  improved: string;
}

export interface ProjectRecommendation {
  title: string;
  description: string;
  skills: string[];
}

export type QuestionCategory = 'technical' | 'behavioral' | 'experience' | 'gap';

export interface InterviewQuestion {
  question: string;
  category: QuestionCategory;
  rationale: string;
}

export interface AnalysisResult {
  job_title: string;
  overall_score: number;
  score_explanation: string;
  summary: string;
  score_breakdown: ScoreBreakdown;
  matching_skills: string[];
  missing_skills: string[];
  relevant_technologies: string[];
  experience: SectionAssessment;
  education: SectionAssessment;
  projects: SectionAssessment;
  keyword_analysis: KeywordAnalysis;
  suggestions: Suggestion[];
  improved_bullets: BulletRewrite[];
  recommended_projects: ProjectRecommendation[];
  interview_questions: InterviewQuestion[];
}

export interface AnalysisSummary {
  id: string;
  created_at: string;
  resume_filename: string;
  job_title: string;
  overall_score: number;
  provider: string;
}

export interface AnalysisRecord extends AnalysisSummary {
  model: string;
  job_description: string;
  resume_pages: number;
  resume_characters: number;
  result: AnalysisResult;
}

export interface AnalysisListResponse {
  items: AnalysisSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  version: string;
  environment: string;
  database: 'ok' | 'error';
  llm_provider: string;
  llm_model: string;
  max_upload_size_mb: number;
}

export interface ApiErrorBody {
  error: { code: string; message: string; details?: unknown };
}

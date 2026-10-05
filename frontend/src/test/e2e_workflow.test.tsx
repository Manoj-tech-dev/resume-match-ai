import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import { api } from '../api/client';
import type { AnalysisRecord } from '../types/analysis';

// Sample mock record simulating the exact response from the backend
const mockRecord: AnalysisRecord = {
  id: 'test-1111-2222-3333-444444444444',
  created_at: new Date().toISOString(),
  resume_filename: 'sample_resume.pdf',
  resume_pages: 1,
  resume_characters: 700,
  job_title: 'Senior Backend Engineer',
  job_description: 'We are seeking a Senior Backend Engineer with Python, FastAPI, and PostgreSQL experience.',
  overall_score: 84,
  provider: 'mock',
  model: 'heuristic-v1',
  result: {
    job_title: 'Senior Backend Engineer',
    overall_score: 84,
    score_explanation: 'Strong candidate match with extensive Python and FastAPI background.',
    summary: 'Candidate shows strong alignment with core backend technologies.',
    score_breakdown: {
      skills: 90,
      experience: 85,
      education: 80,
      projects: 80,
      keywords: 85,
    },
    matching_skills: ['Python', 'FastAPI', 'PostgreSQL', 'Docker'],
    missing_skills: ['Kubernetes', 'Redis'],
    relevant_technologies: ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'Git'],
    experience: {
      score: 85,
      summary: '5+ years backend engineering experience.',
      strengths: ['Hands-on FastAPI microservices', 'PostgreSQL schema optimization'],
      gaps: ['No direct enterprise Kubernetes mentions'],
    },
    education: {
      score: 80,
      summary: 'B.S. in Computer Science',
      strengths: ['Relevant CS degree'],
      gaps: [],
    },
    projects: {
      score: 80,
      summary: 'Relevant portfolio projects demonstrated',
      strengths: ['High-throughput REST APIs'],
      gaps: [],
    },
    keyword_analysis: {
      match_rate: 85,
      keywords: [
        { keyword: 'Python', found: true, importance: 'high', occurrences: 4 },
        { keyword: 'FastAPI', found: true, importance: 'high', occurrences: 3 },
        { keyword: 'PostgreSQL', found: true, importance: 'high', occurrences: 2 },
        { keyword: 'Kubernetes', found: false, importance: 'medium', occurrences: 0 },
      ],
    },
    suggestions: [
      {
        title: 'Highlight Kubernetes exposure',
        detail: 'Consider adding any container orchestration experience.',
        priority: 'high',
      },
    ],
    improved_bullets: [
      {
        original: 'Worked on REST APIs with FastAPI',
        improved: 'Engineered high-throughput REST APIs with FastAPI, reducing response latency by 35%.',
      },
    ],
    recommended_projects: [
      {
        title: 'Kubernetes Microservices Mesh',
        description: 'Deploy a multi-service FastAPI app with Helm and ingress.',
        skills: ['Kubernetes', 'Docker'],
      },
    ],
    interview_questions: [
      {
        question: 'How do you optimize slow PostgreSQL queries under heavy read loads?',
        category: 'technical',
        rationale: 'PostgreSQL is critical to the billing platform.',
      },
    ],
  },
};

describe('Full End-to-End User Workflow in Frontend', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('completes the entire user journey: upload -> analyze -> dashboard -> history -> open -> delete', async () => {
    const user = userEvent.setup();

    // Mock API methods with spies
    const analyzeSpy = vi.spyOn(api, 'analyze').mockResolvedValue(mockRecord);
    const getAnalysisSpy = vi.spyOn(api, 'getAnalysis').mockResolvedValue(mockRecord);
    const listSpy = vi.spyOn(api, 'listAnalyses').mockResolvedValue({
      items: [mockRecord],
      total: 1,
      limit: 100,
      offset: 0,
    });
    const deleteSpy = vi.spyOn(api, 'deleteAnalysis').mockResolvedValue(undefined);
    vi.spyOn(api, 'health').mockResolvedValue({
      status: 'ok',
      version: '1.0.0',
      environment: 'development',
      database: 'ok',
      llm_provider: 'mock',
      llm_model: 'heuristic-v1',
      max_upload_size_mb: 5,
    });

    // 1. Render App
    render(<App />);

    // 2. Verify Home Page rendered
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/ATS Resume Score/i);

    // 3. Upload sample_resume.pdf
    const fileInput = screen.getByTestId('resume-input');
    const pdfFile = new File(['%PDF-1.4 dummy content'], 'sample_resume.pdf', { type: 'application/pdf' });
    await user.upload(fileInput, pdfFile);
    expect(screen.getByText('sample_resume.pdf')).toBeInTheDocument();

    // 4. Submit realistic job description
    const jdTextarea = screen.getByPlaceholderText(/paste the full job posting here/i);
    await user.type(
      jdTextarea,
      'Senior Backend Engineer: We are seeking a Senior Backend Engineer to architect FastAPI microservices with PostgreSQL.'
    );

    // 5. Click Analyze resume
    const submitBtn = screen.getByRole('button', { name: /analyze resume/i });
    await user.click(submitBtn);

    // 6. Verify API was called with the file and JD
    expect(analyzeSpy).toHaveBeenCalledTimes(1);
    expect(analyzeSpy).toHaveBeenCalledWith(
      pdfFile,
      'Senior Backend Engineer: We are seeking a Senior Backend Engineer to architect FastAPI microservices with PostgreSQL.',
      expect.any(AbortSignal)
    );

    // 7. Verify Results Dashboard is displayed
    await waitFor(() => {
      expect(screen.getByTestId('results-dashboard')).toBeInTheDocument();
    });
    expect(screen.getByText('Senior Backend Engineer')).toBeInTheDocument();
    expect(screen.getByText('Strong candidate match with extensive Python and FastAPI background.')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: /84 out of 100/i })).toBeInTheDocument();
    expect(screen.getAllByText('Python').length).toBeGreaterThan(0);
    expect(screen.getAllByText('FastAPI').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Kubernetes').length).toBeGreaterThan(0);

    // 8. Navigate to History via Nav link
    const historyLink = screen.getByRole('link', { name: /history/i });
    await user.click(historyLink);

    // 9. Verify History Page lists the analysis
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /analysis history/i })).toBeInTheDocument();
    });
    expect(listSpy).toHaveBeenCalled();
    expect(screen.getByText('sample_resume.pdf')).toBeInTheDocument();

    // 10. Open saved analysis
    const viewReportBtn = screen.getByRole('button', { name: /view analysis details/i });
    await user.click(viewReportBtn);

    // Verify report reloaded
    await waitFor(() => {
      expect(screen.getByTestId('results-dashboard')).toBeInTheDocument();
    });
    expect(screen.getByText('Senior Backend Engineer')).toBeInTheDocument();

    // 11. Delete the analysis from the results page (or navigate back and delete)
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    const deleteBtn = screen.getByRole('button', { name: /delete/i });
    await act(async () => {
      fireEvent.click(deleteBtn);
    });

    expect(deleteSpy).toHaveBeenCalledWith(mockRecord.id);
  });
});

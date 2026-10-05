import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { HistoryList } from '../components/history/HistoryList';
import type { AnalysisSummary } from '../types/analysis';

const mockItems: AnalysisSummary[] = [
  {
    id: '11111111-1111-1111-1111-111111111111',
    created_at: new Date().toISOString(),
    resume_filename: 'alice_resume.pdf',
    job_title: 'Full Stack Engineer',
    overall_score: 82,
    provider: 'mock',
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    created_at: new Date().toISOString(),
    resume_filename: 'bob_resume.pdf',
    job_title: 'DevOps Specialist',
    overall_score: 64,
    provider: 'mock',
  },
];

describe('HistoryList component', () => {
  it('renders history items with scores and titles', () => {
    render(<HistoryList items={mockItems} onSelect={vi.fn()} onDelete={vi.fn()} />);

    expect(screen.getByText('Full Stack Engineer')).toBeInTheDocument();
    expect(screen.getByText('alice_resume.pdf')).toBeInTheDocument();
    expect(screen.getByText('82')).toBeInTheDocument();

    expect(screen.getByText('DevOps Specialist')).toBeInTheDocument();
    expect(screen.getByText('bob_resume.pdf')).toBeInTheDocument();
    expect(screen.getByText('64')).toBeInTheDocument();
  });

  it('triggers onSelect when an item is clicked', () => {
    const handleSelect = vi.fn();
    render(<HistoryList items={mockItems} onSelect={handleSelect} onDelete={vi.fn()} />);

    const item = screen.getByLabelText(/open analysis for full stack engineer/i);
    fireEvent.click(item);

    expect(handleSelect).toHaveBeenCalledWith('11111111-1111-1111-1111-111111111111');
  });

  it('triggers onDelete when the delete button is clicked', async () => {
    const handleDelete = vi.fn().mockResolvedValue(undefined);
    render(<HistoryList items={mockItems} onSelect={vi.fn()} onDelete={handleDelete} />);

    const deleteBtn = screen.getByLabelText(/delete analysis for full stack engineer/i);
    await act(async () => {
      fireEvent.click(deleteBtn);
    });

    expect(handleDelete).toHaveBeenCalledWith('11111111-1111-1111-1111-111111111111');
  });
});

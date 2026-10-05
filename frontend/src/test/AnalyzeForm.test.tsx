import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { AnalyzeForm } from '../components/analyze/AnalyzeForm';

describe('AnalyzeForm component', () => {
  it('renders dropzone, job description input, and submit button', () => {
    render(<AnalyzeForm onSubmit={vi.fn()} submitting={false} maxSizeMb={5} />);
    expect(screen.getByText(/drop your resume here/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/paste the full job posting here/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /analyze resume/i })).toBeInTheDocument();
  });

  it('validates on submit when fields are empty', async () => {
    const handleSubmit = vi.fn();
    render(<AnalyzeForm onSubmit={handleSubmit} submitting={false} maxSizeMb={5} />);

    const submitBtn = screen.getByRole('button', { name: /analyze resume/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/upload your resume as a pdf/i)).toBeInTheDocument();
    expect(await screen.findByText(/please paste the job description/i)).toBeInTheDocument();
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it('calls onSubmit with file and job description when valid', async () => {
    const user = userEvent.setup();
    const handleSubmit = vi.fn();
    render(<AnalyzeForm onSubmit={handleSubmit} submitting={false} maxSizeMb={5} />);

    const fileInput = screen.getByTestId('resume-input');
    const validFile = new File(['%PDF-1.4 sample content'], 'my_resume.pdf', { type: 'application/pdf' });
    await user.upload(fileInput, validFile);

    expect(screen.getByText('my_resume.pdf')).toBeInTheDocument();

    const textarea = screen.getByPlaceholderText(/paste the full job posting here/i);
    await user.type(
      textarea,
      'Senior Backend Engineer role requiring 5 years of Python, FastAPI, and PostgreSQL experience.'
    );

    const submitBtn = screen.getByRole('button', { name: /analyze resume/i });
    await user.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    expect(handleSubmit).toHaveBeenCalledWith(
      validFile,
      'Senior Backend Engineer role requiring 5 years of Python, FastAPI, and PostgreSQL experience.'
    );
  });

  it('disables submit button during submission', () => {
    render(<AnalyzeForm onSubmit={vi.fn()} submitting={true} maxSizeMb={5} />);
    const submitBtn = screen.getByRole('button', { name: /analyzing/i });
    expect(submitBtn).toBeDisabled();
  });
});

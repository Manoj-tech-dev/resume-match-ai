import { formatDate, scoreLabel } from '../../lib/format';
import type { AnalysisRecord } from '../../types/analysis';
import { Card } from '../common/Card';
import { Icon } from '../common/Icon';
import './Dashboard.css';
import { KeywordTable } from './KeywordTable';
import { BulletRewrites, InterviewQuestions, ProjectList, SuggestionList } from './Lists';
import { ScoreBreakdown } from './ScoreBreakdown';
import { ScoreRing } from './ScoreRing';
import { SectionAssessment } from './SectionAssessment';
import { SkillChips } from './SkillChips';

interface ResultsDashboardProps {
  record: AnalysisRecord;
}

export function ResultsDashboard({ record }: ResultsDashboardProps) {
  const { result } = record;

  return (
    <div className="dashboard" data-testid="results-dashboard">
      {/* Hero Overview */}
      <section className="card dashboard__hero" aria-label="Analysis Overview">
        <div className="dashboard__score-pane">
          <ScoreRing score={result.overall_score} />
          <span className="badge badge--medium" style={{ background: 'hsla(258, 90%, 66%, 0.15)', color: 'hsl(258 100% 85%)' }}>
            {scoreLabel(result.overall_score)}
          </span>
        </div>

        <div className="dashboard__summary-pane">
          <div className="dashboard__meta-row">
            <span className="dashboard__meta-pill">
              <Icon name="file" size={14} /> {record.resume_filename}
            </span>
            <span className="dashboard__meta-pill">
              <Icon name="layers" size={14} /> {record.resume_pages} page{record.resume_pages === 1 ? '' : 's'}
            </span>
            <span className="dashboard__meta-pill">
              <Icon name="history" size={14} /> {formatDate(record.created_at)}
            </span>
            <span className="dashboard__meta-pill">
              <Icon name="cpu" size={14} /> {record.provider} ({record.model})
            </span>
          </div>

          <h1 className="dashboard__job-title">{result.job_title}</h1>
          <p className="dashboard__explanation">{result.score_explanation}</p>
          <p className="muted small">{result.summary}</p>
        </div>
      </section>

      {/* Grid: Score Breakdown & Key Skills */}
      <div className="dashboard__grid-2">
        <Card title="Score Breakdown" icon="target" subtitle="Performance across key hiring dimensions">
          <ScoreBreakdown breakdown={result.score_breakdown} />
        </Card>

        <Card title="Skills Matching" icon="layers" subtitle="Direct alignment with role requirements">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
            <div>
              <p className="field__hint" style={{ marginBottom: 'var(--sp-2)' }}>
                Matching skills ({result.matching_skills.length})
              </p>
              <SkillChips
                skills={result.matching_skills}
                variant="success"
                emptyText="No directly matching core skills detected."
              />
            </div>
            <div>
              <p className="field__hint" style={{ marginBottom: 'var(--sp-2)' }}>
                Missing / Desired skills ({result.missing_skills.length})
              </p>
              <SkillChips
                skills={result.missing_skills}
                variant="danger"
                emptyText="No obvious skill gaps found in the job requirements!"
              />
            </div>
          </div>
        </Card>
      </div>

      {/* Relevant Technologies detected */}
      {result.relevant_technologies.length > 0 && (
        <Card title="Relevant Technologies" icon="code" subtitle="Technical competencies identified in your profile">
          <SkillChips
            skills={result.relevant_technologies}
            variant="info"
            emptyText="No technologies identified."
          />
        </Card>
      )}

      {/* Keyword Analysis */}
      <Card
        title="Keyword Analysis & ATS Optimization"
        icon="search"
        subtitle="Critical terms and phrases that applicant tracking systems look for"
      >
        <KeywordTable analysis={result.keyword_analysis} />
      </Card>

      {/* Section Assessments: Experience, Education, Projects */}
      <div className="dashboard__grid-3">
        <Card title="Experience Fit" icon="briefcase" subtitle="Relevance & depth of career background">
          <SectionAssessment label="Experience score" assessment={result.experience} gapsLabel="Experience gaps" />
        </Card>

        <Card title="Education" icon="graduation" subtitle="Degree & certification alignment">
          <SectionAssessment label="Education score" assessment={result.education} gapsLabel="Education gaps" />
        </Card>

        <Card title="Projects" icon="code" subtitle="Demonstrated practical work">
          <SectionAssessment label="Projects score" assessment={result.projects} gapsLabel="Project gaps" />
        </Card>
      </div>

      {/* Suggestions for Improvement */}
      <Card
        title="Actionable Resume Improvements"
        icon="lightbulb"
        subtitle="Prioritized recommendations to boost interview callback rates"
      >
        <SuggestionList suggestions={result.suggestions} />
      </Card>

      {/* Bullet Rewrites */}
      <Card
        title="Improved Bullet Points"
        icon="edit"
        subtitle="Impact-driven rewrites highlighting quantifiable achievements (XYZ format)"
      >
        <BulletRewrites bullets={result.improved_bullets} />
      </Card>

      {/* Recommended Projects */}
      <Card
        title="Recommended Portfolio Projects"
        icon="rocket"
        subtitle="Targeted projects to bridge experience gaps and demonstrate required stack skills"
      >
        <ProjectList projects={result.recommended_projects} />
      </Card>

      {/* Interview Preparation */}
      <Card
        title="Likely Interview Questions"
        icon="message"
        subtitle="Anticipated questions based on your profile and target role requirements"
      >
        <InterviewQuestions questions={result.interview_questions} />
      </Card>
    </div>
  );
}

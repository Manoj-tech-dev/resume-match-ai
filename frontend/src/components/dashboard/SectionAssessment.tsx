import type { SectionAssessment as Assessment } from '../../types/analysis';
import { Icon } from '../common/Icon';
import { ScoreBar } from './ScoreBreakdown';

interface Props {
  label: string;
  assessment: Assessment;
  gapsLabel?: string;
}

export function SectionAssessment({ label, assessment, gapsLabel = 'Gaps' }: Props) {
  return (
    <div className="assessment">
      <ScoreBar label={label} value={assessment.score} />
      <p className="assessment__summary">{assessment.summary}</p>
      <div className="assessment__lists">
        {assessment.strengths.length > 0 && (
          <div>
            <h4 className="assessment__heading assessment__heading--ok">Strengths</h4>
            <ul className="bullets">
              {assessment.strengths.map((s) => (
                <li key={s}>
                  <Icon name="check" size={14} className="bullets__icon bullets__icon--ok" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}
        {assessment.gaps.length > 0 && (
          <div>
            <h4 className="assessment__heading assessment__heading--gap">{gapsLabel}</h4>
            <ul className="bullets">
              {assessment.gaps.map((g) => (
                <li key={g}>
                  <Icon name="alert" size={14} className="bullets__icon bullets__icon--gap" />
                  {g}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

import { Icon } from '../common/Icon';

type Variant = 'success' | 'danger' | 'info';

interface SkillChipsProps {
  skills: string[];
  variant: Variant;
  emptyText: string;
}

const ICON: Record<Variant, 'check' | 'x' | 'cpu'> = { success: 'check', danger: 'x', info: 'cpu' };

export function SkillChips({ skills, variant, emptyText }: SkillChipsProps) {
  if (skills.length === 0) return <p className="muted small">{emptyText}</p>;
  return (
    <ul className="chip-list">
      {skills.map((skill, i) => (
        <li key={skill} className={`chip chip--${variant}`} style={{ animationDelay: `${i * 30}ms` }}>
          <Icon name={ICON[variant]} size={12} />
          {skill}
        </li>
      ))}
    </ul>
  );
}

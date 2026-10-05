import { useMemo, useState } from 'react';
import { capitalize } from '../../lib/format';
import type { KeywordAnalysis } from '../../types/analysis';
import { Icon } from '../common/Icon';

type Filter = 'all' | 'found' | 'missing';
const IMPORTANCE_ORDER = { high: 0, medium: 1, low: 2 } as const;

export function KeywordTable({ analysis }: { analysis: KeywordAnalysis }) {
  const [filter, setFilter] = useState<Filter>('all');

  const rows = useMemo(
    () =>
      [...analysis.keywords]
        .filter((k) => filter === 'all' || (filter === 'found' ? k.found : !k.found))
        .sort((a, b) => IMPORTANCE_ORDER[a.importance] - IMPORTANCE_ORDER[b.importance] || Number(a.found) - Number(b.found)),
    [analysis.keywords, filter],
  );
  const foundCount = analysis.keywords.filter((k) => k.found).length;

  if (analysis.keywords.length === 0) return <p className="muted small">No keywords were extracted.</p>;

  return (
    <div className="keywords">
      <div className="keywords__summary">
        <div>
          <span className="keywords__rate">{analysis.match_rate}%</span>
          <span className="muted small"> weighted keyword coverage</span>
        </div>
        <div className="segmented" role="group" aria-label="Filter keywords">
          {(['all', 'found', 'missing'] as Filter[]).map((f) => (
            <button
              key={f}
              type="button"
              className={`segmented__btn ${filter === f ? 'is-active' : ''}`}
              aria-pressed={filter === f}
              onClick={() => setFilter(f)}
            >
              {capitalize(f)}
              <span className="segmented__count">
                {f === 'all' ? analysis.keywords.length : f === 'found' ? foundCount : analysis.keywords.length - foundCount}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th scope="col">Keyword</th>
              <th scope="col">Importance</th>
              <th scope="col">In resume</th>
              <th scope="col" className="num">
                Mentions
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((k) => (
              <tr key={k.keyword}>
                <td className="strong">{k.keyword}</td>
                <td>
                  <span className={`badge badge--${k.importance}`}>{k.importance}</span>
                </td>
                <td>
                  {k.found ? (
                    <span className="status status--ok">
                      <Icon name="check" size={14} /> Found
                    </span>
                  ) : (
                    <span className="status status--missing">
                      <Icon name="x" size={14} /> Missing
                    </span>
                  )}
                </td>
                <td className="num">{k.occurrences}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

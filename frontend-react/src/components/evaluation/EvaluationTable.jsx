export default function EvaluationTable({ items = [] }) {
  return (
    <div className="table-card">
      <table className="evaluation-table">
        <thead>
          <tr>
            <th>Criterion</th>
            <th>Score</th>
            <th>Max</th>
            <th>Status</th>
            <th>Feedback</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, index) => (
            <tr key={index}>
              <td>{item.label || item.name || `Criterion ${index + 1}`}</td>
              <td>{item.score_awarded ?? item.score ?? '—'}</td>
              <td>{item.max_score ?? item.weight ?? '—'}</td>
              <td>{item.passed ? 'Pass' : 'Needs work'}</td>
              <td>{item.feedback || item.reason || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
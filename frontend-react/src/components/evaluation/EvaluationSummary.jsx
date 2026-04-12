export default function EvaluationSummary({ evaluation }) {
  const percentValue =
    typeof evaluation.percent === 'number'
      ? Math.round(evaluation.percent * 100)
      : '—'

  return (
    <section className="summary-grid">
      <div className="summary-card">
        <h3>Total Score</h3>
        <p>{evaluation.total_score ?? '—'} / {evaluation.total_possible ?? '—'}</p>
      </div>

      <div className="summary-card">
        <h3>Percent</h3>
        <p>{percentValue}%</p>
      </div>

      <div className="summary-card">
        <h3>Result</h3>
        <p>{evaluation.passed ? 'Passed' : 'Needs Improvement'}</p>
      </div>
    </section>
  )
}
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  evaluateTrainee,
  getSessionResults,
} from '../services/evaluationService'
import EvaluationSummary from '../components/evaluation/EvaluationSummary'
import EvaluationTable from '../components/evaluation/EvaluationTable'

export default function TraineeEvaluationPage() {
  const { sessionId } = useParams()
  const [evaluation, setEvaluation] = useState(null)
  const [sessionResults, setSessionResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        const evalData = await evaluateTrainee(sessionId)
        setEvaluation(evalData)

        try {
          const results = await getSessionResults(sessionId)
          setSessionResults(results)
        } catch (resultsError) {
          console.error(resultsError)
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [sessionId])

  if (loading) return <div className="page-shell">Evaluating trainee...</div>
  if (error) return <div className="page-shell">Error: {error}</div>
  if (!evaluation) return <div className="page-shell">No evaluation data found.</div>

  return (
    <div className="page-shell">
      <div className="page-topbar">
        <Link to="/cases">Back to Cases</Link>
      </div>

      <h1>Trainee Evaluation</h1>

      <EvaluationSummary evaluation={evaluation} />
      <EvaluationTable items={evaluation.items || []} />

      <section className="feedback-card">
        <h2>Feedback</h2>
        {Array.isArray(evaluation.summary_feedback) && evaluation.summary_feedback.length > 0 ? (
          <ul>
            {evaluation.summary_feedback.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        ) : (
          <p>No summary feedback available.</p>
        )}
      </section>

      {sessionResults && (
        <section className="feedback-card">
          <h2>Session Summary</h2>
          <p><strong>Strengths:</strong> {Array.isArray(sessionResults.strengths) ? sessionResults.strengths.join(', ') : '—'}</p>
          <p><strong>Weaknesses:</strong> {Array.isArray(sessionResults.weaknesses) ? sessionResults.weaknesses.join(', ') : '—'}</p>
          <p><strong>Improvement:</strong> {sessionResults.improvement || '—'}</p>
        </section>
      )}
    </div>
  )
}
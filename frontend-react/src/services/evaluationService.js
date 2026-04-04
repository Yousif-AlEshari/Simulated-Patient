import { apiRequest } from './api'

export function evaluateTrainee(sessionId) {
  return apiRequest('/eval/trainee', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  })
}

export function getSessionResults(sessionId) {
  return apiRequest(`/session/${sessionId}/results`)
}
import { apiRequest } from './api'

export function startSession(payload) {
  return apiRequest('/chat/start', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function sendMessage(payload) {
  return apiRequest('/chat/message', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getSessionProfile(sessionId) {
  return apiRequest(`/session/${sessionId}/profile`)
}

export function getSessionTime(sessionId) {
  return apiRequest(`/session/${sessionId}/time`)
}

export function endSession(sessionId) {
  return apiRequest(`/session/${sessionId}/end`, {
    method: 'POST',
  })
}
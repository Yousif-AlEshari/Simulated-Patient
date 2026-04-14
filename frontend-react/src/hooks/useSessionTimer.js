import { useEffect, useState } from 'react'
import { getSessionTime } from '../services/sessionService'

const TIMER_CHECK_INTERVAL_MS = 30000
const FRONTEND_DISPLAY_INTERVAL_MS = 1000
const INITIAL_SESSION_DURATION_SECONDS = 900

export function useSessionTimer(sessionId) {
  const [timeLeft, setTimeLeft] = useState(INITIAL_SESSION_DURATION_SECONDS)
  const [expired, setExpired] = useState(false)

  useEffect(() => {
    let backendSyncIntervalId
    let localCountdownIntervalId

    async function syncWithBackend() {
      try {
        const data = await getSessionTime(sessionId)
        setTimeLeft(Math.max(0, Math.floor(data.remaining_seconds || 0)))
        setExpired(Boolean(data.expired))
      } catch (error) {
        console.error('Timer sync error:', error)
      }
    }

    function startLocalCountdown() {
      localCountdownIntervalId = setInterval(() => {
        setTimeLeft((prev) => Math.max(0, prev - 1))
      }, FRONTEND_DISPLAY_INTERVAL_MS)
    }

    function startBackendSync() {
      syncWithBackend() // immediate call
      backendSyncIntervalId = setInterval(syncWithBackend, TIMER_CHECK_INTERVAL_MS)
    }

    // Start both intervals
    startLocalCountdown()
    startBackendSync()

    return () => {
      if (localCountdownIntervalId) clearInterval(localCountdownIntervalId)
      if (backendSyncIntervalId) clearInterval(backendSyncIntervalId)
    }
  }, [sessionId])

  return { timeLeft, expired }
}
import { useEffect, useState } from 'react'
import { getSessionTime } from '../services/sessionService'

export function useSessionTimer(sessionId) {
  const [timeLeft, setTimeLeft] = useState(0)
  const [expired, setExpired] = useState(false)

  useEffect(() => {
    let intervalId

    async function loadTime() {
      try {
        const data = await getSessionTime(sessionId)
        setTimeLeft(Math.max(0, Math.floor(data.remaining_seconds || 0)))
        setExpired(Boolean(data.expired))
      } catch (error) {
        console.error('Timer error:', error)
      }
    }

    loadTime()
    intervalId = setInterval(loadTime, 1000)

    return () => clearInterval(intervalId)
  }, [sessionId])

  return { timeLeft, expired }
}
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  getSessionProfile,
  sendMessage,
  endSession,
} from '../services/sessionService'
import { useSessionTimer } from '../hooks/useSessionTimer'
import SessionSidebar from '../components/chat/SessionSidebar'
import SessionHeader from '../components/chat/SessionHeader'
import ChatMessage from '../components/chat/ChatMessage'
import ChatInput from '../components/chat/ChatInput'

export default function SessionPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [profile, setProfile] = useState(null)
  const [messages, setMessages] = useState([])
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  const { timeLeft, expired } = useSessionTimer(sessionId)

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await getSessionProfile(sessionId)
        setProfile(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoadingProfile(false)
      }
    }

    loadProfile()
  }, [sessionId])

  async function handleSendMessage(text) {
    if (!text.trim() || sending || expired) return

    const userMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
    }

    setMessages((prev) => [...prev, userMessage])
    setSending(true)
    setError('')

    try {
      const reply = await sendMessage({
        session_id: sessionId,
        message: text,
      })

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: reply.content || reply.message || 'No response received.',
        },
      ])
    } catch (err) {
      setError(err.message)
    } finally {
      setSending(false)
    }
  }

  async function handleFinishSession() {
    try {
      await endSession(sessionId)
    } catch (err) {
      console.error(err)
    }
    navigate(`/evaluation/${sessionId}`)
  }

  return (
    <div className="session-page">
      <SessionSidebar profile={profile} loading={loadingProfile} />

      <main className="session-main">
        <SessionHeader timeLeft={timeLeft} onFinish={handleFinishSession} />

        {expired && <div className="error-banner">Session time has expired.</div>}
        {error && <div className="error-banner">{error}</div>}

        <div className="chat-thread">
          {messages.length === 0 ? (
            <div className="empty-chat">Start the interview by sending the first message.</div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}
        </div>

        <ChatInput onSend={handleSendMessage} disabled={sending || expired} />
      </main>
    </div>
  )
}
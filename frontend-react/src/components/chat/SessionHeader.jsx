function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${String(secs).padStart(2, '0')}`
}

export default function SessionHeader({ timeLeft, onFinish }) {
  return (
    <div className="session-header">
      <div>
        <h1>Session</h1>
        <p>Remaining time: {formatTime(timeLeft)}</p>
      </div>
      <button className="finish-btn" onClick={onFinish}>
        Finish Session
      </button>
    </div>
  )
}
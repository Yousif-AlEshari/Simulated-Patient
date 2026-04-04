export default function ChatMessage({ message }) {
  return (
    <div className={`chat-message ${message.role === 'user' ? 'user' : 'assistant'}`}>
      <div className="chat-bubble">{message.content}</div>
    </div>
  )
}
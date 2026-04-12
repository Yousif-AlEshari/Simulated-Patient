export default function SessionSidebar({ profile, loading }) {
  if (loading) {
    return <aside className="session-sidebar">Loading case...</aside>
  }

  if (!profile) {
    return <aside className="session-sidebar">No case details found.</aside>
  }

  return (
    <aside className="session-sidebar">
      <h2>Case Overview</h2>

      <div className="sidebar-card">
        <p><strong>Name:</strong> {profile.name || 'Patient'}</p>
        <p><strong>Age:</strong> {profile.age || '—'}</p>
        <p><strong>Gender:</strong> {profile.gender || '—'}</p>
        <p><strong>Occupation:</strong> {profile.occupation || '—'}</p>
      </div>

      <div className="sidebar-card">
        <p><strong>Chief complaint:</strong> {profile.chief_complaint || '—'}</p>
        <p><strong>Severity:</strong> {profile.symptom_severity || '—'}</p>
        <p><strong>Onset:</strong> {profile.symptom_onset || '—'}</p>
      </div>

      <div className="sidebar-card">
        <p><strong>Response style:</strong> {profile.response_style || '—'}</p>
        <p><strong>Emotional tone:</strong> {profile.emotional_tone || '—'}</p>
        <p><strong>Risk positive:</strong> {profile.risk_positive ? 'Yes' : 'No'}</p>
      </div>
    </aside>
  )
}
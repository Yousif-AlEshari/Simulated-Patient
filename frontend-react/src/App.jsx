import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import CasesPage from './pages/CasesPage'
import SessionPage from './pages/SessionPage'
import TraineeEvaluationPage from './pages/TraineeEvaluationPage'

function App() {
  return (
    <div className="app-container">
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/cases" element={<CasesPage />} />
        <Route path="/session/:sessionId" element={<SessionPage />} />
        <Route path="/evaluation/:sessionId" element={<TraineeEvaluationPage />} />
      </Routes>
    </div>
  )
}

export default App
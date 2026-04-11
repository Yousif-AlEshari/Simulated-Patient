import React, { useState, useEffect, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import CaseCard from '../components/CaseCard'
import parsedCases from '../data/cases.json'
import { startSession } from '../services/sessionService'

const CasesPage = () => {
  const navigate = useNavigate()

  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [startingCaseId, setStartingCaseId] = useState(null)

  const itemsPerPage = 6

  const filteredCases = useMemo(() => {
    if (!searchQuery.trim()) return parsedCases

    const q = searchQuery.toLowerCase()

    return parsedCases.filter((c) => {
      const allText = [
        c.title,
        c.subtitle,
        c.difficulty,
        c.dynamics,
        c.objective,
        c.duration,
        ...(c.skills || []),
      ]
        .join(' ')
        .toLowerCase()

      return allText.includes(q)
    })
  }, [searchQuery])

  const totalPages = Math.ceil(filteredCases.length / itemsPerPage)
  const indexOfLastItem = currentPage * itemsPerPage
  const indexOfFirstItem = indexOfLastItem - itemsPerPage
  const currentItems = filteredCases.slice(indexOfFirstItem, indexOfLastItem)

  const handlePageChange = (page) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery])

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [])

  async function handleStartCase(caseItem) {
    try {
      setStartingCaseId(caseItem.id)

      const data = await startSession({
        condition: caseItem.title || caseItem.name || 'General Case',
        language: 'English',
      })

      navigate(`/session/${data.session_id}`)
    } catch (err) {
      alert(`Failed to start session: ${err.message}`)
    } finally {
      setStartingCaseId(null)
    }
  }

  return (
    <div
      className="bg-light page-transition"
      style={{ minHeight: '100vh', paddingBottom: '4rem' }}
    >
      <nav className="navbar" style={{ position: 'sticky', top: 0, zIndex: 100 }}>
        <div className="container nav-container">
          <div
            className="logo d-flex align-center"
            style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}
          >
            <Link
              to="/"
              className="btn btn-sm btn-outline"
              style={{ color: 'var(--text-main)', borderColor: 'var(--text-muted)' }}
            >
              ⮌
            </Link>

            <div className="logo-text">
              PsychSim <span className="text-secondary">Trainee Dashboard</span>
            </div>
          </div>

          <div className="nav-links">
            <Link to="/" className="btn btn-sm btn-outline">
              Home
            </Link>
          </div>
        </div>
      </nav>

      <div className="container" style={{ paddingTop: '4rem' }}>
        <div className="section-header center animate-on-scroll is-visible slide-up">
          <h2>Select a Patient Case</h2>
          <p>Choose a clinical scenario below to begin your simulated interview session.</p>
        </div>

        <div
          className="animate-on-scroll is-visible slide-up"
          style={{ marginBottom: '3rem', display: 'flex', justifyContent: 'center' }}
        >
          <div style={{ position: 'relative', width: '100%', maxWidth: '600px' }}>
            <span
              style={{
                position: 'absolute',
                left: '1.25rem',
                top: '50%',
                transform: 'translateY(-50%)',
                zIndex: 10,
                filter: 'grayscale(100%) opacity(50%)',
              }}
            >
              🔍
            </span>

            <input
              type="text"
              placeholder="Search cases by title or keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '1.25rem 1.5rem 1.25rem 3.5rem',
                borderRadius: '999px',
                border: '1px solid rgba(26, 86, 219, 0.2)',
                boxShadow:
                  '0 10px 25px -5px rgba(26, 86, 219, 0.1), 0 8px 10px -6px rgba(26, 86, 219, 0.1)',
                outline: 'none',
                fontFamily: 'var(--font-body)',
                fontSize: '1.05rem',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(12px)',
              }}
              onFocus={(e) => {
                e.target.style.boxShadow =
                  '0 20px 25px -5px rgba(26, 86, 219, 0.2), 0 8px 10px -6px rgba(26, 86, 219, 0.1)'
                e.target.style.borderColor = 'var(--primary)'
                e.target.style.transform = 'translateY(-2px)'
              }}
              onBlur={(e) => {
                e.target.style.boxShadow =
                  '0 10px 25px -5px rgba(26, 86, 219, 0.1), 0 8px 10px -6px rgba(26, 86, 219, 0.1)'
                e.target.style.borderColor = 'rgba(26, 86, 219, 0.2)'
                e.target.style.transform = 'translateY(0)'
              }}
            />
          </div>
        </div>

        {filteredCases.length > 0 ? (
          <div className="grid layout-3 pattern-container animate-on-scroll is-visible slide-in-bottom">
            {currentItems.map((caseItem, index) => (
              <div
                key={caseItem.id}
                style={{ animationDelay: `${index * 0.05}s`, height: '100%' }}
                className="animate-on-scroll is-visible slide-up"
              >
                <CaseCard
                  data={caseItem}
                  onStart={() => handleStartCase(caseItem)}
                  isStarting={startingCaseId === caseItem.id}
                />
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
            <h4>No cases match your search.</h4>
            <p>Try adjusting your keywords.</p>
          </div>
        )}

        {totalPages > 1 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '0.5rem',
              marginTop: '4rem',
            }}
          >
            <button
              className="btn btn-sm btn-outline"
              onClick={() => handlePageChange(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              style={{
                color: currentPage === 1 ? 'var(--text-muted)' : 'var(--dark)',
                opacity: currentPage === 1 ? 0.5 : 1,
                cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
              }}
            >
              Previous
            </button>

            {[...Array(totalPages)].map((_, i) => (
              <button
                key={i}
                className={`btn btn-sm ${currentPage === i + 1 ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => handlePageChange(i + 1)}
                style={{
                  color: currentPage === i + 1 ? 'white' : 'var(--dark)',
                }}
              >
                {i + 1}
              </button>
            ))}

            <button
              className="btn btn-sm btn-outline"
              onClick={() => handlePageChange(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              style={{
                color: currentPage === totalPages ? 'var(--text-muted)' : 'var(--dark)',
                opacity: currentPage === totalPages ? 0.5 : 1,
                cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
              }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default CasesPage
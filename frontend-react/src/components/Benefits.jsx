const Benefits = () => {
  return (
    <section id="benefits" className="section">
      <div className="container">
        <div className="section-header center animate-on-scroll slide-up">
          <h2>Improving Mental Health Education</h2>
          <p>Discover how AI simulation can transform your training experience.</p>
        </div>
        <div className="grid layout-2 align-center">
          <div className="animate-on-scroll slide-in-left">
            <div className="benefit-item">
              <div className="benefit-icon">📈</div>
              <div>
                <h4>Easy to Grow</h4>
                <p>Train hundreds of students at the same time without the hassle of scheduling human actors.</p>
              </div>
            </div>
            <div className="benefit-item">
              <div className="benefit-icon">🧠</div>
              <div>
                <h4>Highly Realistic</h4>
                <p>Train with AI that acts just like real psychiatric patients, showing accurate symptoms.</p>
              </div>
            </div>
            <div className="benefit-item">
              <div className="benefit-icon">🔄</div>
              <div>
                <h4>Constant Improvement</h4>
                <p>Learn faster with immediate feedback that human teachers cannot always provide.</p>
              </div>
            </div>
          </div>
          <div className="animate-on-scroll slide-in-right visual-wrapper">
            <div className="glass-panel stats-panel">
              <h4>Cohort Analytics</h4>
              <div className="stat-row">
                <span>Diagnostic Accuracy</span>
                <div className="progress-bar"><div className="fill" style={{ width: '85%' }}></div></div>
                <span>85%</span>
              </div>
              <div className="stat-row">
                <span>Empathy Score</span>
                <div className="progress-bar"><div className="fill bg-secondary" style={{ width: '92%' }}></div></div>
                <span>92%</span>
              </div>
              <div className="stat-row">
                <span>Risk Detection</span>
                <div className="progress-bar"><div className="fill bg-success" style={{ width: '78%' }}></div></div>
                <span>78%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Benefits;
